#!/usr/bin/env python3
"""Aggregate Gemini 3.8 EDU-R rerun (identifier 40 + RQ3 12)."""

from __future__ import annotations

import csv
import hashlib
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parents[1]
GEMINI_DIR = BASE / "gemini_38_edur"
RESULTS = GEMINI_DIR / "results"
IDENT_CSV = RESULTS / "run_level_identifier.csv"
RQ3_CSV = RESULTS / "run_level_rq3.csv"
MAP_CSV = BASE / "component_identifier_map.csv"

sys.path.insert(0, str(REPO))
from decomposition.evaluation.stability import stability

MODEL = "gemini-3.8-flash"
CONDITIONS = ("C0", "C1", "C2", "C3")


def ffloat(v) -> float | None:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def load_reverse() -> dict[str, str]:
    rev: dict[str, str] = {}
    for row in csv.DictReader(MAP_CSV.open(encoding="utf-8")):
        rev[row["anonymized_identifier"]] = row["original_identifier"]
    return rev


def assignment_from_row(row: dict, rev: dict[str, str]) -> dict[str, str] | None:
    p = REPO / row["expected_output_dir"] / "parsed.json"
    if not p.is_file():
        return None
    d = json.loads(p.read_text(encoding="utf-8"))
    ca = d.get("component_assignment") or {}
    if not ca:
        return None
    if row.get("identifier_condition") == "ANONYMIZED":
        ca = {rev.get(k, k): v for k, v in ca.items()}
    return ca


def summarize_f1(values: list[float]) -> dict:
    if not values:
        return {"mean": "", "median": "", "stdev": "", "min": "", "max": ""}
    values = sorted(values)
    return {
        "mean": round(statistics.mean(values), 6),
        "median": round(statistics.median(values), 6),
        "stdev": round(statistics.pstdev(values), 6) if len(values) > 1 else 0.0,
        "min": round(values[0], 6),
        "max": round(values[-1], 6),
    }


def main() -> None:
    if not IDENT_CSV.is_file():
        print("Missing run_level_identifier.csv — run score_gemini_38_edur.py first")
        return
    ident_rows = list(csv.DictReader(IDENT_CSV.open(encoding="utf-8")))
    rq3_rows = list(csv.DictReader(RQ3_CSV.open(encoding="utf-8"))) if RQ3_CSV.is_file() else []
    rev = load_reverse()

    # Per-cell stats (identifier control)
    cells: dict[tuple, list[dict]] = defaultdict(list)
    for row in ident_rows:
        cells[(row["evidence_condition"], row["identifier_condition"])].append(row)

    cell_rows = []
    for cond in CONDITIONS:
        for ident in ("SEMANTIC", "ANONYMIZED"):
            members = cells.get((cond, ident), [])
            f1s = [ffloat(m["pairwise_f1"]) for m in members if m.get("scored") == "ok"]
            f1s = [x for x in f1s if x is not None]
            aris = [ffloat(m["ari"]) for m in members if m.get("scored") == "ok"]
            aris = [x for x in aris if x is not None]
            nmis = [ffloat(m["nmi"]) for m in members if m.get("scored") == "ok"]
            nmis = [x for x in nmis if x is not None]
            stats = summarize_f1(f1s)
            assignments = [
                a
                for m in members
                if m.get("scored") == "ok"
                for a in [assignment_from_row(m, rev)]
                if a
            ]
            stab = stability(assignments).get("mean", "") if assignments else ""
            valid = sum(1 for m in members if m.get("run_status") == "VALID" or m.get("scored") == "ok")
            invalid = sum(1 for m in members if m.get("run_status") == "MODEL_INVALID")
            infra = sum(1 for m in members if m.get("run_status") == "INFRASTRUCTURE_FAILURE")
            cell_rows.append(
                {
                    "evidence_condition": cond,
                    "identifier_condition": ident,
                    "attempted": len(members),
                    "valid": valid,
                    "invalid": invalid,
                    "infra": infra,
                    **stats,
                    "mean_ari": round(statistics.mean(aris), 6) if aris else "",
                    "mean_nmi": round(statistics.mean(nmis), 6) if nmis else "",
                    "stability": stab,
                }
            )

    # Pivot table semantic vs anonymized mean F1 per condition
    sem_means = {c: "" for c in CONDITIONS}
    anon_means = {c: "" for c in CONDITIONS}
    for cr in cell_rows:
        if cr["identifier_condition"] == "SEMANTIC":
            sem_means[cr["evidence_condition"]] = cr["mean"]
        else:
            anon_means[cr["evidence_condition"]] = cr["mean"]

    # RQ3
    rq3_by_cond: dict[str, list[dict]] = defaultdict(list)
    for row in rq3_rows:
        rq3_by_cond[row["evidence_condition"]].append(row)

    rq3_summary = []
    for cond in CONDITIONS:
        members = rq3_by_cond.get(cond, [])
        comps = [ffloat(m["rule_compliance"]) for m in members if m.get("scored") == "ok"]
        comps = [x for x in comps if x is not None]
        assignments = [
            a
            for m in members
            if m.get("scored") == "ok"
            for a in [assignment_from_row({**m, "identifier_condition": "SEMANTIC"}, rev)]
            if a
        ]
        stab = stability(assignments).get("mean", "") if assignments else ""
        rq3_summary.append(
            {
                "condition": cond,
                "rule_compliance": round(statistics.mean(comps), 6) if comps else "",
                "stability": stab,
                "attempted": len(members),
                "valid": sum(1 for m in members if m.get("scored") == "ok"),
                "invalid": sum(1 for m in members if m.get("run_status") == "MODEL_INVALID"),
            }
        )

    # Validity
    all_ident = ident_rows
    validity = {
        "attempted": len(all_ident),
        "valid": sum(1 for r in all_ident if r.get("run_status") == "VALID" or r.get("scored") == "ok"),
        "model_invalid": sum(1 for r in all_ident if r.get("run_status") == "MODEL_INVALID"),
        "infra": sum(1 for r in all_ident if r.get("run_status") == "INFRASTRUCTURE_FAILURE"),
    }

    # Contrasts
    c0_sem = ffloat(sem_means["C0"])
    c0_anon = ffloat(anon_means["C0"])
    anon_f1_by_cond = {c: ffloat(anon_means[c]) for c in CONDITIONS}
    best_anon_cond = max(anon_f1_by_cond, key=lambda c: anon_f1_by_cond[c] or -1)
    best_anon_f1 = anon_f1_by_cond[best_anon_cond]

    sem_f1_list = [ffloat(sem_means[c]) for c in CONDITIONS if ffloat(sem_means[c]) is not None]
    best_sem_cond = max(CONDITIONS, key=lambda c: ffloat(sem_means[c]) or -1)

    manifest_h = hashlib.sha256(
        (GEMINI_DIR / "run_manifest_identifier_40.csv").read_bytes()
    ).hexdigest()
    fingerprint = hashlib.sha256(f"{MODEL}:{manifest_h}".encode()).hexdigest()[:16]

    lines = [
        "# GEMINI_38_EDUR_RESULTS_FREEZE",
        "",
        f"- Model: `{MODEL}` (provider: gemini)",
        f"- Experiment fingerprint: `{fingerprint}`",
        f"- Identifier manifest SHA-256: `{manifest_h}`",
        f"- Historical Gemini 2.5 preserved under `outputs/runs/anonymization_exp_v1/` (unchanged)",
        "",
        "## Validity (identifier 40)",
        json.dumps(validity, indent=2),
        "",
        "## Identifier pivot (mean pairwise F1)",
        "",
        f"| Model | Identifier | C0 | C1 | C2 | C3 |",
        f"| --- | --- | --- | --- | --- | --- |",
        f"| {MODEL} | SEMANTIC | {sem_means['C0']} | {sem_means['C1']} | {sem_means['C2']} | {sem_means['C3']} |",
        f"| {MODEL} | ANONYMIZED | {anon_means['C0']} | {anon_means['C1']} | {anon_means['C2']} | {anon_means['C3']} |",
        "",
        "## C0 semantic − anonymized delta",
        str(round(c0_sem - c0_anon, 6) if c0_sem is not None and c0_anon is not None else ""),
        "",
        "## Best anonymized",
        f"{best_anon_cond} F1={best_anon_f1}",
        "",
        "## RQ3 (12 semantic)",
        "",
    ]
    for r in rq3_summary:
        lines.append(f"- {r['condition']}: compliance={r['rule_compliance']} stability={r['stability']}")
    lines.append("")

    RESULTS.mkdir(parents=True, exist_ok=True)
    write_csv(RESULTS / "cell_summary_identifier.csv", cell_rows)
    write_csv(RESULTS / "rq3_summary.csv", rq3_summary)
    (RESULTS / "GEMINI_38_EDUR_RESULTS_FREEZE.md").write_text("\n".join(lines), encoding="utf-8")

    print("Pivot table:")
    print(lines[12])
    print(lines[13])
    print(lines[14])
    print("Analysis ->", RESULTS)


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        w = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
