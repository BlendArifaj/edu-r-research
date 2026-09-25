#!/usr/bin/env python3
"""Aggregate PETCLINIC_EXT_V1 results + outcome classification."""

from __future__ import annotations

import csv
import hashlib
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BASE = REPO / "external_validation_petclinic"
RUN_LEVEL = BASE / "results" / "run_level_results.csv"
RESULTS = BASE / "results"


def ffloat(v) -> float | None:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def summarize_f1(values: list[float]) -> dict:
    if not values:
        return {"n": 0, "mean": "", "median": "", "stdev": "", "min": "", "max": ""}
    values = sorted(values)
    return {
        "n": len(values),
        "mean": round(statistics.mean(values), 6),
        "median": round(statistics.median(values), 6),
        "stdev": round(statistics.pstdev(values), 6) if len(values) > 1 else 0.0,
        "min": round(values[0], 6),
        "max": round(values[-1], 6),
    }


def cell_key(row: dict) -> tuple:
    return (row["model"], row["evidence_condition"], row["identifier_condition"])


def stability_for_cell(members: list[dict], rev: dict[str, str]) -> float | str:
    from decomposition.evaluation.stability import stability

    assignments = []
    for m in members:
        if m.get("scored") != "ok":
            continue
        p = REPO / m["expected_output_path"] / "parsed.json"
        if not p.is_file():
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        ca = d.get("component_assignment") or {}
        if m.get("identifier_condition") == "ANONYMIZED":
            ca = {rev.get(k, k): v for k, v in ca.items()}
        if ca:
            assignments.append(ca)
    if not assignments:
        return ""
    return stability(assignments).get("mean", "")


def main() -> None:
    rows = list(csv.DictReader(RUN_LEVEL.open(encoding="utf-8"))) if RUN_LEVEL.is_file() else []
    if not rows:
        print("No run_level_results.csv")
        return

    rev: dict[str, str] = {}
    map_csv = BASE / "component_identifier_map.csv"
    if map_csv.is_file():
        for row in csv.DictReader(map_csv.open(encoding="utf-8")):
            rev[row["anonymized_identifier"]] = row["original_identifier"]

    cells: dict[tuple, list[dict]] = defaultdict(list)
    for row in rows:
        cells[cell_key(row)].append(row)

    cell_rows = []
    for key in sorted(cells.keys()):
        members = cells[key]
        f1s = [ffloat(m.get("pairwise_f1_primary")) for m in members if m.get("scored") == "ok"]
        f1s = [x for x in f1s if x is not None]
        aris = [ffloat(m.get("ari_primary")) for m in members if m.get("scored") == "ok"]
        aris = [x for x in aris if x is not None]
        nmis = [ffloat(m.get("nmi_primary")) for m in members if m.get("scored") == "ok"]
        nmis = [x for x in nmis if x is not None]
        stats = summarize_f1(f1s)
        cell_rows.append(
            {
                "model": key[0],
                "evidence_condition": key[1],
                "identifier_condition": key[2],
                "attempts": len(members),
                "valid_count": len(f1s),
                "invalid_count": sum(1 for m in members if m.get("run_status") == "MODEL_INVALID"),
                "infra_count": sum(1 for m in members if m.get("run_status") == "INFRASTRUCTURE_FAILURE"),
                "low_valid_count": "yes" if len(f1s) < 3 else "no",
                "mean_f1": stats["mean"],
                "median_f1": stats["median"],
                "sd_f1": stats["stdev"],
                "min_f1": stats["min"],
                "max_f1": stats["max"],
                "mean_ari": round(statistics.mean(aris), 6) if aris else "",
                "mean_nmi": round(statistics.mean(nmis), 6) if nmis else "",
                "stability": stability_for_cell(members, rev),
            }
        )
    write_csv(RESULTS / "cell_summary.csv", cell_rows)

    # EXT-RQ contrasts by model
    models = sorted({r["model"] for r in rows})
    rq1 = []
    rq2 = []
    for model in models:
        def cell_mean(ev, ident):
            sub = [ffloat(r.get("pairwise_f1_primary")) for r in rows if r["model"] == model and r["evidence_condition"] == ev and r["identifier_condition"] == ident and r.get("scored") == "ok"]
            sub = [x for x in sub if x is not None]
            return statistics.mean(sub) if sub else None

        m_sem = cell_mean("E0_MINIMAL", "SEMANTIC")
        m_anon = cell_mean("E0_MINIMAL", "ANONYMIZED")
        rq1.append(
            {
                "model": model,
                "mean_f1_e0_semantic": round(m_sem, 6) if m_sem is not None else "",
                "mean_f1_e0_anonymized": round(m_anon, 6) if m_anon is not None else "",
                "delta_f1_semantic_minus_anonymized": round(m_sem - m_anon, 6)
                if m_sem is not None and m_anon is not None
                else "",
            }
        )
        e0a = cell_mean("E0_MINIMAL", "ANONYMIZED")
        e1a = cell_mean("E1_STRUCTURAL", "ANONYMIZED")
        rq2.append(
            {
                "model": model,
                "mean_f1_e0_anonymized": round(e0a, 6) if e0a is not None else "",
                "mean_f1_e1_anonymized": round(e1a, 6) if e1a is not None else "",
                "delta_f1_e1_minus_e0_anonymized": round(e1a - e0a, 6)
                if e0a is not None and e1a is not None
                else "",
            }
        )
    write_csv(RESULTS / "ext_rq1_deltas.csv", rq1)
    write_csv(RESULTS / "ext_rq2_deltas.csv", rq2)

    # Sensitivity EXT-RQ1/2 on sensitivity F1 column
    sens_rows = []
    for model in models:
        def sens_mean(ev, ident):
            sub = [
                ffloat(r.get("pairwise_f1_sensitivity_cv"))
                for r in rows
                if r["model"] == model
                and r["evidence_condition"] == ev
                and r["identifier_condition"] == ident
                and r.get("scored") == "ok"
            ]
            sub = [x for x in sub if x is not None]
            return statistics.mean(sub) if sub else None

        d1p = rq1[[r["model"] for r in rq1].index(model)]["delta_f1_semantic_minus_anonymized"]
        d1s = ""
        ms, ma = sens_mean("E0_MINIMAL", "SEMANTIC"), sens_mean("E0_MINIMAL", "ANONYMIZED")
        if ms is not None and ma is not None:
            d1s = round(ms - ma, 6)
        d2p = rq2[[r["model"] for r in rq2].index(model)]["delta_f1_e1_minus_e0_anonymized"]
        e0a, e1a = sens_mean("E0_MINIMAL", "ANONYMIZED"), sens_mean("E1_STRUCTURAL", "ANONYMIZED")
        d2s = round(e1a - e0a, 6) if e0a is not None and e1a is not None else ""

        def sign(x):
            if x == "" or x is None:
                return 0
            x = float(x)
            if x > 0.01:
                return 1
            if x < -0.01:
                return -1
            return 0

        s1p, s1s = sign(d1p), sign(d1s)
        s2p, s2s = sign(d2p), sign(d2s)
        consistent = (s1p == s1s and s2p == s2s) or (s1p == 0 and s1s == 0)
        partial = not consistent and (s1p == s1s or s2p == s2s)
        label = "CONSISTENT" if consistent else ("PARTIALLY_CONSISTENT" if partial else "INCONSISTENT")
        sens_rows.append(
            {
                "model": model,
                "primary_rq1_delta": d1p,
                "sensitivity_rq1_delta": d1s,
                "primary_rq2_delta": d2p,
                "sensitivity_rq2_delta": d2s,
                "consistency": label,
            }
        )
    write_csv(RESULTS / "sensitivity_consistency.csv", sens_rows)

    # Outcome classification (pre-specified)
    pos_rq1 = sum(1 for r in rq1 if ffloat(r["delta_f1_semantic_minus_anonymized"]) and ffloat(r["delta_f1_semantic_minus_anonymized"]) > 0)
    outcome = classify_outcome(rq1, rq2, pos_rq1, len(models))

    write_freeze_md(rows, cell_rows, rq1, rq2, sens_rows, outcome)
    print("Analysis complete under external_validation_petclinic/results/")


def classify_outcome(rq1, rq2, pos_rq1, n_models) -> str:
    if pos_rq1 >= n_models:
        base = "OUTCOME A"
    elif pos_rq1 == 0:
        base = "OUTCOME B"
    else:
        base = "MIXED"
    e1_improves = sum(1 for r in rq2 if ffloat(r.get("delta_f1_e1_minus_e0_anonymized")) and ffloat(r["delta_f1_e1_minus_e0_anonymized"]) > 0.05)
    if e1_improves >= 2:
        base += " + OUTCOME C"
    if len({sign_delta(r["delta_f1_semantic_minus_anonymized"]) for r in rq1}) > 2:
        base += " + OUTCOME D"
    return base


def sign_delta(v):
    x = ffloat(v)
    if x is None:
        return "na"
    if x > 0.01:
        return "pos"
    if x < -0.01:
        return "neg"
    return "flat"


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_freeze_md(rows, cell_rows, rq1, rq2, sens_rows, outcome) -> None:
    def h(p: Path) -> str:
        return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else ""

    manifest_h = h(BASE / "run_manifest.csv")
    ref_h = h(BASE / "reference_mapping.csv")
    fingerprint = hashlib.sha256(f"{manifest_h}:{ref_h}".encode()).hexdigest()[:16]

    valid = sum(1 for r in rows if r.get("run_status") == "VALID")
    invalid = sum(1 for r in rows if r.get("run_status") == "MODEL_INVALID")
    infra = sum(1 for r in rows if r.get("run_status") == "INFRASTRUCTURE_FAILURE")

    lines = [
        "# PETCLINIC_EXT_V1_RESULTS_FREEZE",
        "",
        f"- Experiment fingerprint: `{fingerprint}`",
        f"- Attempted: {len(rows)} | VALID: {valid} | MODEL_INVALID: {invalid} | INFRA: {infra}",
        f"- Monolith SHA: `818c4136ea971c21674525f9053de0d9c7ad8cfe`",
        f"- Microservices SHA: `aefaf7fa9eb0ab911a24c346ca0e4dc5837251c7`",
        f"- reference_mapping.csv SHA-256: `{ref_h}`",
        f"- run_manifest.csv SHA-256: `{manifest_h}`",
        "",
        "## Outcome classification",
        outcome,
        "",
        "## EXT-RQ1 (E0 semantic − anonymized)",
        "",
    ]
    for r in rq1:
        lines.append(f"- {r['model']}: delta={r['delta_f1_semantic_minus_anonymized']}")
    lines.extend(["", "## EXT-RQ2 (E1−E0 anonymized)", ""])
    for r in rq2:
        lines.append(f"- {r['model']}: delta={r['delta_f1_e1_minus_e0_anonymized']}")
    lines.extend(["", "## Sensitivity consistency", ""])
    for r in sens_rows:
        lines.append(f"- {r['model']}: {r['consistency']}")
    lines.extend(["", "## Cell summary", "", "See `cell_summary.csv`.", ""])
    (RESULTS / "PETCLINIC_EXT_V1_RESULTS_FREEZE.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    sys.path.insert(0, str(REPO))
    main()
