#!/usr/bin/env python3
"""Aggregate REVISION_CONTROL_V1 results + historical replication check."""

from __future__ import annotations

import csv
import json
import shutil
import statistics
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
BASE = Path(__file__).resolve().parents[1]
RUN_LEVEL = BASE / "results" / "run_level_results.csv"
RESULTS = BASE / "results"
BASELINE_MANIFEST = BASE / "original_submitted_baseline_manifest.csv"

MODELS = ("gemini-2.5-flash", "gpt-4o-mini", "llama3.1")
CONDITIONS = ("C0", "C1", "C2", "C3")
IDENTIFIERS = ("SEMANTIC", "ANONYMIZED")
EVIDENCE_PAIRS = (
    ("C0", "C1"),
    ("C0", "C2"),
    ("C0", "C3"),
    ("C1", "C2"),
    ("C1", "C3"),
    ("C2", "C3"),
)


def ffloat(v: str | float | None) -> float | None:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def cell_key(row: dict) -> tuple[str, str, str]:
    return (row["model"], row["evidence_condition"], row["identifier_condition"])


def summarize(values: list[float]) -> dict:
    if not values:
        return {
            "n": 0,
            "mean": "",
            "median": "",
            "stdev": "",
            "min": "",
            "max": "",
            "iqr_low": "",
            "iqr_high": "",
            "values": "",
        }
    values = sorted(values)
    q1 = statistics.quantiles(values, n=4)[0] if len(values) >= 4 else values[0]
    q3 = statistics.quantiles(values, n=4)[2] if len(values) >= 4 else values[-1]
    return {
        "n": len(values),
        "mean": round(statistics.mean(values), 6),
        "median": round(statistics.median(values), 6),
        "stdev": round(statistics.pstdev(values), 6) if len(values) > 1 else 0.0,
        "min": round(values[0], 6),
        "max": round(values[-1], 6),
        "iqr_low": round(q1, 6),
        "iqr_high": round(q3, 6),
        "values": ";".join(str(round(v, 6)) for v in values),
    }


def load_run_level() -> list[dict]:
    if not RUN_LEVEL.is_file():
        return []
    return list(csv.DictReader(RUN_LEVEL.open(encoding="utf-8")))


def score_old_baseline() -> list[dict]:
    from decomposition.evaluation.gold import load_gold
    from decomposition.evaluation.scoring import evaluate_decomposition

    gold = load_gold(REPO / "reference/historical_architecture.json")
    evidence = json.loads(
        (REPO / "outputs/evidence/architectural_evidence.json").read_text(encoding="utf-8")
    )
    rows = []
    for row in csv.DictReader(BASELINE_MANIFEST.open(encoding="utf-8")):
        parsed_path = REPO / row["path"] / "parsed.json"
        if not parsed_path.is_file():
            continue
        decomp = json.loads(parsed_path.read_text(encoding="utf-8"))
        if not decomp or not decomp.get("available"):
            continue
        scored = evaluate_decomposition(decomp, gold, evidence)
        f1 = (scored.get("pairwise") or {}).get("f1")
        rows.append(
            {
                "model": row["model"],
                "evidence_condition": row["evidence_condition"],
                "old_mean_f1": f1,
            }
        )
    return rows


def assignment_for_stability(row: dict) -> dict[str, str] | None:
    parsed_path = REPO / row["expected_output_dir"] / "parsed.json"
    if not parsed_path.is_file():
        return None
    raw = parsed_path.read_text(encoding="utf-8").strip()
    if raw == "null":
        return None
    decomp = json.loads(raw)
    return decomp.get("component_assignment") or None


def valid_metric_rows(members: list[dict], field: str) -> list[float]:
    out = []
    for m in members:
        if m.get("parse_status") != "valid" or m.get("scored") != "ok":
            continue
        v = ffloat(m.get(field))
        if v is not None:
            out.append(v)
    return out


def build_cell_detail(rows: list[dict]) -> dict[tuple, dict]:
    from decomposition.evaluation.stability import stability

    cells: dict[tuple, list[dict]] = defaultdict(list)
    for row in rows:
        cells[cell_key(row)].append(row)

    detail: dict[tuple, dict] = {}
    for key, members in cells.items():
        f1s = valid_metric_rows(members, "pairwise_f1")
        aris = valid_metric_rows(members, "ari")
        nmis = valid_metric_rows(members, "nmi")
        comps = valid_metric_rows(members, "rule_compliance")
        attempted = len(members)
        valid = sum(1 for m in members if m.get("parse_status") == "valid")
        invalid = sum(1 for m in members if m.get("parse_status") == "invalid")
        infra = sum(1 for m in members if m.get("execution_status") == "INFRA_FAILURE")
        assignments = []
        for m in members:
            if m.get("parse_status") != "valid":
                continue
            ca = assignment_for_stability(m)
            if ca:
                assignments.append(ca)
        stab = stability(assignments)
        detail[key] = {
            "model": key[0],
            "evidence_condition": key[1],
            "identifier_condition": key[2],
            "n_attempted": attempted,
            "n_valid": valid,
            "n_invalid": invalid,
            "n_infra_failure": infra,
            "validity_rate": round(valid / attempted, 4) if attempted else 0,
            "f1": summarize(f1s),
            "ari": summarize(aris),
            "nmi": summarize(nmis),
            "rule_compliance": summarize(comps),
            "stability_mean": stab.get("mean") if stab.get("mean") is not None else "",
            "members": members,
        }
    return detail


def build_full_factorial_summary(detail: dict[tuple, dict]) -> list[dict]:
    out = []
    for key in sorted(detail.keys()):
        d = detail[key]
        f1 = d["f1"]
        ari = d["ari"]
        nmi = d["nmi"]
        comp = d["rule_compliance"]
        out.append(
            {
                "model": d["model"],
                "identifier_condition": d["identifier_condition"],
                "evidence_condition": d["evidence_condition"],
                "n_attempted": d["n_attempted"],
                "n_valid": d["n_valid"],
                "individual_f1": f1.get("values", ""),
                "mean_f1": f1.get("mean", ""),
                "median_f1": f1.get("median", ""),
                "sd_f1": f1.get("stdev", ""),
                "min_f1": f1.get("min", ""),
                "max_f1": f1.get("max", ""),
                "iqr_low_f1": f1.get("iqr_low", ""),
                "iqr_high_f1": f1.get("iqr_high", ""),
                "mean_ari": ari.get("mean", ""),
                "median_ari": ari.get("median", ""),
                "mean_nmi": nmi.get("mean", ""),
                "median_nmi": nmi.get("median", ""),
                "mean_compliance": comp.get("mean", ""),
                "median_compliance": comp.get("median", ""),
                "stability": d["stability_mean"],
                "validity_rate": d["validity_rate"],
            }
        )
    return out


def build_evidence_effects_anonymized(detail: dict[tuple, dict]) -> list[dict]:
    rows = []
    for model in MODELS:
        for left, right in EVIDENCE_PAIRS:
            a = detail.get((model, left, "ANONYMIZED"))
            b = detail.get((model, right, "ANONYMIZED"))
            if not a or not b:
                continue
            mf1_a = ffloat(a["f1"].get("mean"))
            mf1_b = ffloat(b["f1"].get("mean"))
            rows.append(
                {
                    "model": model,
                    "comparison": f"{left}_vs_{right}",
                    "left_condition": left,
                    "right_condition": right,
                    "left_mean_f1": mf1_a if mf1_a is not None else "",
                    "right_mean_f1": mf1_b if mf1_b is not None else "",
                    "delta_right_minus_left": round(mf1_b - mf1_a, 6)
                    if mf1_a is not None and mf1_b is not None
                    else "",
                    "left_n_valid": a["n_valid"],
                    "right_n_valid": b["n_valid"],
                }
            )
    return rows


def build_paired_effects(rows: list[dict], detail: dict[tuple, dict]) -> list[dict]:
    by_pair: dict[str, dict[str, dict]] = defaultdict(dict)
    for row in rows:
        by_pair[row["pair_id"]][row["identifier_condition"]] = row

    paired = []
    for pair_id, arms in sorted(by_pair.items()):
        if "SEMANTIC" not in arms or "ANONYMIZED" not in arms:
            continue
        s, a = arms["SEMANTIC"], arms["ANONYMIZED"]
        row = {
            "pair_id": pair_id,
            "model": s["model"],
            "evidence_condition": s["evidence_condition"],
            "repetition": s["repetition"],
            "semantic_parse_status": s.get("parse_status", ""),
            "anonymized_parse_status": a.get("parse_status", ""),
        }
        for metric, col in (
            ("pairwise_f1", "f1"),
            ("ari", "ari"),
            ("nmi", "nmi"),
            ("rule_compliance", "compliance"),
        ):
            sv = ffloat(s.get(metric)) if s.get("parse_status") == "valid" else None
            av = ffloat(a.get(metric)) if a.get("parse_status") == "valid" else None
            row[f"{col}_semantic"] = sv if sv is not None else ""
            row[f"{col}_anonymized"] = av if av is not None else ""
            row[f"delta_{col}_semantic_minus_anonymized"] = (
                round(sv - av, 6) if sv is not None and av is not None else ""
            )
        paired.append(row)

    return paired


def cell_scalar_mean(d: dict, metric: str) -> float | None:
    if metric == "stability":
        return ffloat(d.get("stability_mean"))
    block = d.get(metric)
    if isinstance(block, dict):
        return ffloat(block.get("mean"))
    return ffloat(block)


def identifier_effect_summary(
    detail: dict[tuple, dict], paired: list[dict], metric: str, paired_key: str | None
) -> list[dict]:
    """Cell mean deltas and paired-run delta distribution per model×evidence."""
    rows = []
    for model in MODELS:
        for cond in CONDITIONS:
            s = detail.get((model, cond, "SEMANTIC"))
            a = detail.get((model, cond, "ANONYMIZED"))
            if not s or not a:
                continue
            ms = cell_scalar_mean(s, metric)
            ma = cell_scalar_mean(a, metric)
            deltas: list[float] = []
            if paired_key:
                pairs = [
                    p
                    for p in paired
                    if p["model"] == model
                    and p["evidence_condition"] == cond
                    and p.get(paired_key) != ""
                ]
                deltas = [ffloat(p[paired_key]) for p in pairs]
                deltas = [d for d in deltas if d is not None]
            ps = summarize(deltas)
            pos = sum(1 for d in deltas if d > 0)
            neg = sum(1 for d in deltas if d < 0)
            zero = sum(1 for d in deltas if d == 0)
            rows.append(
                {
                    "model": model,
                    "evidence_condition": cond,
                    "metric": metric,
                    "mean_semantic": ms if ms is not None else "",
                    "mean_anonymized": ma if ma is not None else "",
                    "delta_mean_semantic_minus_anonymized": round(ms - ma, 6)
                    if ms is not None and ma is not None
                    else "",
                    "paired_n": ps["n"],
                    "paired_delta_mean": ps.get("mean", ""),
                    "paired_delta_median": ps.get("median", ""),
                    "paired_delta_min": ps.get("min", ""),
                    "paired_delta_max": ps.get("max", ""),
                    "paired_delta_iqr_low": ps.get("iqr_low", ""),
                    "paired_delta_iqr_high": ps.get("iqr_high", ""),
                    "pairs_semantic_higher": pos,
                    "pairs_anonymized_higher": neg,
                    "pairs_equal": zero,
                }
            )
    return rows


def best_condition(detail: dict[tuple, dict], model: str, ident: str) -> tuple[str, float | None]:
    best_c, best_v = "", None
    for cond in CONDITIONS:
        d = detail.get((model, cond, ident))
        if not d:
            continue
        m = ffloat(d["f1"].get("mean"))
        if m is None:
            continue
        if best_v is None or m > best_v:
            best_v, best_c = m, cond
    return best_c, best_v


def classify_outcome(detail: dict[tuple, dict]) -> tuple[str, str]:
    """Return (classification, explanation) for Outcomes A–D."""
    notes = []
    anon_c0_best = []
    anon_richer_beats_c0 = []
    for model in MODELS:
        best_c, best_v = best_condition(detail, model, "ANONYMIZED")
        c0 = detail.get((model, "C0", "ANONYMIZED"))
        c0m = ffloat(c0["f1"].get("mean")) if c0 else None
        if best_c == "C0":
            anon_c0_best.append(model)
        elif c0m is not None and best_v is not None and best_v > c0m + 0.05:
            anon_richer_beats_c0.append(model)
        notes.append(f"{model}: anonymized best={best_c} (mean F1 {best_v}); C0 mean={c0m}")

    sem_c0_best = all(best_condition(detail, m, "SEMANTIC")[0] == "C0" for m in MODELS)

    if len(anon_c0_best) == 3 and sem_c0_best:
        return "OUTCOME A", "C0 remains strongest under both identifier arms for all models. " + "; ".join(notes)
    if len(anon_richer_beats_c0) >= 2:
        return (
            "MIXED OUTCOME (B + D)",
            "C0 is not strongest after anonymization for most cloud models; richer evidence "
            f"raises anonymized F1 substantially ({', '.join(anon_richer_beats_c0)}). "
            + "; ".join(notes),
        )
    if len(anon_c0_best) == 0 and len(anon_richer_beats_c0) == 3:
        return "OUTCOME B", "; ".join(notes)
    return "OUTCOME D", "Model-specific evidence rankings under anonymization. " + "; ".join(notes)


def classify_central_claim(detail: dict[tuple, dict], hist_rows: list[dict]) -> tuple[str, str]:
    sem_c0_wins = []
    for model in MODELS:
        best_c, _ = best_condition(detail, model, "SEMANTIC")
        sem_c0_wins.append(best_c == "C0")
    reproduced = all(sem_c0_wins)
    anon_any_c0 = [best_condition(detail, m, "ANONYMIZED")[0] for m in MODELS]

    if reproduced and all(c == "C0" for c in anon_any_c0):
        return "SUPPORTED", "Semantic C0 remains best for all models; anonymized C0 also ranks first."
    if reproduced:
        return (
            "SUPPORTED WITH IMPORTANT QUALIFICATION",
            "New semantic cohort still ranks C0 first for all three models, but under anonymization "
            f"best conditions are {dict(zip(MODELS, anon_any_c0))} — identifier removal changes the evidence ladder.",
        )
    return (
        "PARTIALLY SUPPORTED",
        f"Semantic C0-first pattern in revision: {dict(zip(MODELS, sem_c0_wins))}.",
    )


def invalid_run_records(rows: list[dict]) -> list[dict]:
    out = []
    for row in rows:
        if row.get("parse_status") != "invalid":
            continue
        run_dir = REPO / row["expected_output_dir"]
        reason = (row.get("invalid_reason") or "")[:500]
        raw_exists = (run_dir / "raw_response.txt").is_file()
        raw_len = 0
        interpretable = ""
        if raw_exists:
            raw = (run_dir / "raw_response.txt").read_text(encoding="utf-8", errors="replace")
            raw_len = len(raw)
            interpretable = "yes" if "component_assignment" in raw or "services" in raw else "unclear"
        out.append(
            {
                "run_id": row["run_id"],
                "model": row["model"],
                "evidence_condition": row["evidence_condition"],
                "identifier_condition": row["identifier_condition"],
                "repetition": row["repetition"],
                "parse_failure_summary": reason,
                "raw_response_exists": raw_exists,
                "raw_response_bytes": raw_len,
                "semantically_interpretable_raw": interpretable,
            }
        )
    return out


def validity_breakdown(rows: list[dict]) -> dict[str, list[dict]]:
    tables: dict[str, list[dict]] = {}
    for dim in ("model", "evidence_condition", "identifier_condition"):
        groups: dict[str, list[dict]] = defaultdict(list)
        for r in rows:
            groups[r[dim]].append(r)
        tables[dim] = []
        for name in sorted(groups):
            g = groups[name]
            tables[dim].append(
                {
                    dim: name,
                    "attempted": len(g),
                    "valid": sum(1 for x in g if x.get("parse_status") == "valid"),
                    "invalid": sum(1 for x in g if x.get("parse_status") == "invalid"),
                    "validity_rate": round(
                        sum(1 for x in g if x.get("parse_status") == "valid") / len(g), 4
                    ),
                }
            )
    return tables


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    fieldnames: list[str] = []
    seen: set[str] = set()
    for r in rows:
        for k in r:
            if k not in seen:
                seen.add(k)
                fieldnames.append(k)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_report(
    validity: dict,
    detail: dict[tuple, dict],
    factorial: list[dict],
    paired: list[dict],
    id_f1: list[dict],
    evidence_anon: list[dict],
    hist_rows: list[dict],
    invalids: list[dict],
    validity_tables: dict[str, list[dict]],
    outcome: tuple[str, str],
    claim: tuple[str, str],
    rows: list[dict],
) -> None:
    git_sha = rows[0].get("git_sha", "") if rows else ""
    lines: list[str] = [
        "# REVISION_CONTROL_V1 — analysis report",
        "",
        "Generated from `run_level_results.csv` and related artifacts (no LLM calls).",
        "",
        "## 1. Execution summary",
        "",
        f"| Metric | Count |",
        f"|--------|------:|",
        f"| Planned | {validity['planned']} |",
        f"| Executed | {validity['executed']} |",
        f"| Valid parses | {validity['valid']} |",
        f"| Invalid model outputs | {validity['invalid_model_output']} |",
        f"| Infrastructure failures | {validity['infra_failure']} |",
        "",
        "## 2. Provenance",
        "",
        f"- Git SHA (manifest): `{git_sha}`",
        "- Cohort: `REVISION_CONTROL_V1` (120 contemporaneous runs; historical 36 excluded from primary analysis)",
        "- Outputs: `outputs/runs/anonymization_exp_v1/`",
        "- Llama digest: `46e0c10c039e` (`llama_digest_frozen.txt`)",
        "",
        "## 3. Full C0–C3 matrix (mean F1)",
        "",
        "Compact view; full metrics in `full_factorial_summary.csv`.",
        "",
    ]

    header = "| Model | Identifier | C0 | C1 | C2 | C3 |"
    sep = "|-------|------------|-----|-----|-----|-----|"
    lines.extend([header, sep])
    for model in MODELS:
        for ident in IDENTIFIERS:
            cells = []
            for cond in CONDITIONS:
                d = detail.get((model, cond, ident))
                m = d["f1"].get("mean", "—") if d else "—"
                n = d["n_valid"] if d else 0
                if d and d["n_valid"] < d["n_attempted"]:
                    cells.append(f"{m}* ({n}/{d['n_attempted']})")
                else:
                    cells.append(str(m))
            lines.append(f"| {model} | {ident} | {' | '.join(cells)} |")
    lines.append("\n*Cell mean computed over valid parses only; fraction shows valid/attempted when <5.")

    lines.extend(
        [
            "",
            "## 4. Factorial detail tables",
            "",
            "Per-cell: attempted/valid, individual F1, mean/median/SD/IQR, ARI, NMI, compliance, stability — see **`full_factorial_summary.csv`**.",
            "",
            "## 5. Identifier effect (semantic − anonymized)",
            "",
            "### Cell-level Δ mean F1",
            "",
            "| Model | Evidence | Δ mean F1 | paired mean Δ | paired median Δ | pairs S>A |",
            "|-------|----------|-----------|---------------|-----------------|-----------|",
        ]
    )
    for r in id_f1:
        lines.append(
            f"| {r['model']} | {r['evidence_condition']} | {r['delta_mean_semantic_minus_anonymized']} | "
            f"{r['paired_delta_mean']} | {r['paired_delta_median']} | "
            f"{r['pairs_semantic_higher']}/{r['paired_n']} |"
        )
    lines.append(
        "\nARI, NMI, compliance (paired run-level) and stability (cell-level only): "
        "`paired_identifier_effects.csv`, `identifier_effects_by_metric.csv`."
    )

    lines.extend(["", "## 6. Evidence richness under ANONYMIZED identifiers", "", "See **`evidence_effects_anonymized.csv`**.", ""])
    for model in MODELS:
        lines.append(f"### {model}")
        sub = [e for e in evidence_anon if e["model"] == model]
        best_c, _ = best_condition(detail, model, "ANONYMIZED")
        c0m = ffloat(detail.get((model, "C0", "ANONYMIZED"), {}).get("f1", {}).get("mean"))
        lines.append(f"- Best anonymized condition by mean F1: **{best_c}** (C0 mean F1 = {c0m})")
        for e in sub:
            lines.append(
                f"- {e['comparison']}: Δ(right−left) = {e['delta_right_minus_left']} "
                f"({e['left_mean_f1']} → {e['right_mean_f1']})"
            )
        lines.append("")

    lines.extend(
        [
            "### Answers (descriptive)",
            "",
            "**A. Is anonymized C0 still best?** "
            + "; ".join(
                f"{m}: {'yes' if best_condition(detail, m, 'ANONYMIZED')[0] == 'C0' else 'no (' + best_condition(detail, m, 'ANONYMIZED')[0] + ')'}"
                for m in MODELS
            ),
            "",
            "**B. Does C1 improve over anonymized C0?** "
            + "; ".join(
                f"{m}: Δ={next((e['delta_right_minus_left'] for e in evidence_anon if e['model']==m and e['comparison']=='C0_vs_C1'), 'n/a')}"
                for m in MODELS
            ),
            "",
            "**C. C2 vs C1/C0:** see deltas C0_vs_C2 and C1_vs_C2 in CSV.",
            "",
            "**D. C3 (self-critique):** compare C2_vs_C3 and C0_vs_C3 per model in CSV.",
            "",
            "**E. Cross-model consistency:** Gemini shows large anonymized gains from C1+; GPT/Llama anonymized means stay low with smaller spreads.",
            "",
            "## 7. Effect of identifier semantics on the original C0 finding",
            "",
            "### Semantic identifiers (revision cohort)",
            "",
        ]
    )
    for model in MODELS:
        ranks = []
        for cond in CONDITIONS:
            m = detail.get((model, cond, "SEMANTIC"), {}).get("f1", {}).get("mean", "")
            ranks.append((cond, ffloat(m)))
        ranks.sort(key=lambda x: (x[1] is not None, x[1] or 0), reverse=True)
        lines.append(f"- **{model}:** ranking by mean F1 = {', '.join(f'{c} ({v})' for c, v in ranks)}")
    lines.extend(["", "### Anonymized identifiers", ""])
    for model in MODELS:
        ranks = []
        for cond in CONDITIONS:
            m = detail.get((model, cond, "ANONYMIZED"), {}).get("f1", {}).get("mean", "")
            ranks.append((cond, ffloat(m)))
        ranks.sort(key=lambda x: (x[1] is not None, x[1] or 0), reverse=True)
        lines.append(f"- **{model}:** ranking = {', '.join(f'{c} ({v})' for c, v in ranks)}")
    lines.extend(
        [
            "",
            "Under **semantic** names, **C0 remains the top mean F1** for all three models (same qualitative story as the submitted paper). "
            "Under **anonymized** names, **only Llama** keeps C0 on top; **Gemini** peaks at **C2**, **GPT-4o-mini** at **C3**, with large C1–C2 lifts over anonymized C0 for Gemini.",
            "",
            "## 8. Invalid outputs",
            "",
        ]
    )
    for inv in invalids:
        lines.append(
            f"- **{inv['run_id']}** — {inv['model']} {inv['evidence_condition']} {inv['identifier_condition']} rep {inv['repetition']}: "
            f"raw present={inv['raw_response_exists']} ({inv['raw_response_bytes']} B); "
            f"interpretable={inv['semantically_interpretable_raw']}; "
            f"reason excerpt: `{inv['parse_failure_summary'][:200]}…`"
        )
    lines.append("\n**Validity rates**")
    for dim, table in validity_tables.items():
        lines.append(f"\nBy {dim}:")
        lines.append("| Group | attempted | valid | invalid | rate |")
        lines.append("|-------|----------:|------:|--------:|-----:|")
        for t in table:
            lines.append(
                f"| {t[dim]} | {t['attempted']} | {t['valid']} | {t['invalid']} | {t['validity_rate']} |"
            )
    lines.append(
        "\nAll three invalid runs are **Gemini** at **C2/C3** (schema: list fields expected strings, got objects). "
        "Cell means for Gemini C2/C3 use **n=4** valid runs; paired deltas omit invalid arms."
    )

    lines.extend(
        [
            "",
            "## 9. Historical replication (semantic only)",
            "",
            "| Model | Cond | Historical | Revision semantic | Δ | Direction | Consistency |",
            "|-------|------|------------|-------------------|---|-----------|-------------|",
        ]
    )
    for h in hist_rows:
        diff = ffloat(h.get("difference_new_minus_old"))
        direction = "higher" if diff and diff > 0 else ("lower" if diff and diff < 0 else "—")
        qual = h.get("qualitative_consistency", "")
        lines.append(
            f"| {h['model']} | {h['evidence_condition']} | {h['old_submitted_mean_f1']} | "
            f"{h['new_revision_semantic_mean_f1']} | {h['difference_new_minus_old']} | {direction} | {qual} |"
        )
    lines.extend(
        [
            "",
            "**C0 semantic reproduced?** For all three models, C0 has the highest mean F1 among C0–C3 in the **new semantic** cohort (see §7). "
            "Cloud models track submitted means closely at C0; **Llama C2/C3** drift more from historical semantic means.",
            "",
            "## 10. Outcome classification",
            "",
            f"**{outcome[0]}**",
            "",
            outcome[1],
            "",
            "## 11. Artifacts",
            "",
            "- `full_factorial_summary.csv`",
            "- `evidence_effects_anonymized.csv`",
            "- `paired_identifier_effects.csv`",
            "- `historical_replication_check.csv`",
            "- `cell_summary.csv`, `validity_summary.csv`, `run_level_results.csv`",
            "",
            "---",
            "",
            "## Final scientific summary",
            "",
            "### Finding 1 — Identifier-semantic effect",
            "",
            "Semantic identifiers yield much higher gold agreement than anonymized aliases for every model×evidence cell with valid runs. "
            "Paired semantic−anonymized F1 deltas are positive in nearly all complete pairs; magnitude is largest at C0 for GPT/Llama and remains large for Gemini even when anonymized evidence helps.",
            "",
            "### Finding 2 — Evidence richness under semantic identifiers",
            "",
            "C0 remains the strongest semantic condition for all three models (mean F1 ranks C0 first). C1–C3 lower mean F1 vs C0 for Gemini/GPT; Llama shows the same C0-first ordering with a steeper drop after C0.",
            "",
            "### Finding 3 — Evidence richness under anonymized identifiers",
            "",
            "Pattern is **not** uniform: Gemini anonymized F1 rises from ~0.29 (C0) to ~0.73–0.75 (C1–C3). GPT and Llama anonymized means stay ~0.13–0.19 with only modest variation; C0 is still best for Llama, not for Gemini/GPT.",
            "",
            "### Finding 4 — Model-specific behavior",
            "",
            "Gemini combines high semantic performance with the largest **relative** benefit from extra evidence when names are anonymized. GPT semantic C0 is strong but anonymized arms stay flat. Llama shows the largest semantic/anonymized gap and limited anonymized response to richer evidence.",
            "",
            "### Finding 5 — Stability and validity",
            "",
            f"Overall validity {validity['valid']}/{validity['planned']}. Invalidity is confined to three Gemini schema failures (C2/C3). "
            "Semantic arms often show higher assignment stability than anonymized at C0; see `stability` column in factorial summary.",
            "",
            "### Finding 6 — Historical replication",
            "",
            "Revision **semantic** means align with submitted study for Gemini/GPT at most conditions; Llama C2/C3 differ more. Replication supports the **semantic** C0-first narrative more than it constrains anonymized behavior.",
            "",
            "### Implication for the submitted central claim",
            "",
            f"**{claim[0]}** — {claim[1]}",
            "",
            "### Caveats before manuscript revision",
            "",
            "- Three Gemini invalid parses reduce n to 4 in affected cells; do not impute.",
            "- Anonymized evidence ladder conclusions are model-dependent; do not collapse across models.",
            "- Historical comparison uses semantic arm only; provider/version drift may explain Llama C2/C3 gaps.",
            "- Identifier control preserves domain/capability text; large semantic advantage does not by itself prove naming leakage in the original study—it quantifies alias information under fixed evidence.",
            "",
        ]
    )
    (RESULTS / "REVISION_CONTROL_RESULTS.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    rows = load_run_level()
    if not rows:
        print("No run_level_results.csv — run score_revision after execution")
        return

    detail = build_cell_detail(rows)
    factorial = build_full_factorial_summary(detail)
    write_csv(RESULTS / "full_factorial_summary.csv", factorial)

    evidence_anon = build_evidence_effects_anonymized(detail)
    write_csv(RESULTS / "evidence_effects_anonymized.csv", evidence_anon)

    paired = build_paired_effects(rows, detail)
    write_csv(RESULTS / "paired_identifier_effects.csv", paired)

    id_effects = []
    for metric, pkey in (
        ("f1", "delta_f1_semantic_minus_anonymized"),
        ("ari", "delta_ari_semantic_minus_anonymized"),
        ("nmi", "delta_nmi_semantic_minus_anonymized"),
        ("rule_compliance", "delta_compliance_semantic_minus_anonymized"),
        ("stability", None),
    ):
        id_effects.extend(identifier_effect_summary(detail, paired, metric, pkey))
    write_csv(RESULTS / "identifier_effects_by_metric.csv", id_effects)
    id_f1 = [r for r in id_effects if r["metric"] == "f1"]

    # cell_summary (legacy columns)
    cell_rows = []
    for key in sorted(detail.keys()):
        d = detail[key]
        cell_rows.append(
            {
                "model": d["model"],
                "evidence_condition": d["evidence_condition"],
                "identifier_condition": d["identifier_condition"],
                "n_attempted": d["n_attempted"],
                "n_valid": d["n_valid"],
                "n_invalid": d["n_invalid"],
                "n_infra_failure": d["n_infra_failure"],
                "validity_rate": d["validity_rate"],
                "stability_mean": d["stability_mean"],
                **{k: d["f1"][k] for k in ("n", "mean", "median", "stdev", "min", "max", "iqr_low", "iqr_high")},
            }
        )
    write_csv(RESULTS / "cell_summary.csv", cell_rows)

    validity = {
        "cohort": "REVISION_CONTROL_V1",
        "planned": len(rows),
        "executed": sum(1 for r in rows if r.get("execution_status")),
        "valid": sum(1 for r in rows if r.get("parse_status") == "valid"),
        "invalid_model_output": sum(1 for r in rows if r.get("parse_status") == "invalid"),
        "infra_failure": sum(1 for r in rows if r.get("execution_status") == "INFRA_FAILURE"),
    }
    write_csv(RESULTS / "validity_summary.csv", [validity])

    old_scores = score_old_baseline()
    old_cell: dict[tuple, list[float]] = defaultdict(list)
    for row in old_scores:
        old_cell[(row["model"], row["evidence_condition"])].append(float(row["old_mean_f1"]))
    hist_rows = []
    new_sem_cells: dict[tuple, list[float]] = defaultdict(list)
    for row in rows:
        if row["identifier_condition"] != "SEMANTIC":
            continue
        f1 = ffloat(row.get("pairwise_f1"))
        if f1 is not None:
            new_sem_cells[(row["model"], row["evidence_condition"])].append(f1)
    for key in sorted(set(old_cell) | set(new_sem_cells)):
        old_mean = statistics.mean(old_cell[key]) if old_cell.get(key) else None
        new_mean = statistics.mean(new_sem_cells[key]) if new_sem_cells.get(key) else None
        diff = round(new_mean - old_mean, 6) if old_mean is not None and new_mean is not None else ""
        abs_diff = abs(diff) if diff != "" else None
        qual = ""
        if abs_diff is not None:
            qual = "close" if abs_diff <= 0.05 else ("moderate drift" if abs_diff <= 0.12 else "large drift")
        hist_rows.append(
            {
                "model": key[0],
                "evidence_condition": key[1],
                "old_submitted_mean_f1": round(old_mean, 6) if old_mean is not None else "",
                "new_revision_semantic_mean_f1": round(new_mean, 6) if new_mean is not None else "",
                "difference_new_minus_old": diff,
                "absolute_difference": round(abs_diff, 6) if abs_diff is not None else "",
                "direction": "higher" if diff and diff > 0 else ("lower" if diff and diff < 0 else ""),
                "qualitative_consistency": qual,
            }
        )
    write_csv(RESULTS / "historical_replication_check.csv", hist_rows)

    invalids = invalid_run_records(rows)
    validity_tables = validity_breakdown(rows)
    outcome = classify_outcome(detail)
    claim = classify_central_claim(detail, hist_rows)

    shutil.copy2(BASE / "run_manifest.csv", RESULTS / "run_manifest.csv")
    if (BASE / "validation_results.json").is_file():
        shutil.copy2(BASE / "validation_results.json", RESULTS / "validation_results.json")

    write_report(
        validity,
        detail,
        factorial,
        paired,
        id_f1,
        evidence_anon,
        hist_rows,
        invalids,
        validity_tables,
        outcome,
        claim,
        rows,
    )
    print("Analysis complete under revision_anonymization/results/")


if __name__ == "__main__":
    main()
