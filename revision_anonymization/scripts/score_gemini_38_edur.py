#!/usr/bin/env python3
"""Score Gemini 3.8 EDU-R identifier + RQ3 manifests."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parents[1]
GEMINI_DIR = BASE / "gemini_38_edur"
sys.path.insert(0, str(REPO))

from decomposition.evaluation.gold import load_gold
from decomposition.evaluation.scoring import evaluate_decomposition

GOLD = REPO / "reference/historical_architecture.json"
EVIDENCE = REPO / "outputs/evidence/architectural_evidence.json"
MAP_CSV = BASE / "component_identifier_map.csv"


def load_reverse_map() -> dict[str, str]:
    rev: dict[str, str] = {}
    with MAP_CSV.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rev[row["anonymized_identifier"]] = row["original_identifier"]
    return rev


def reverse_assignment(assignment: dict[str, str], reverse: dict[str, str]) -> dict[str, str]:
    return {reverse.get(k, k): v for k, v in assignment.items()}


def score_manifest(manifest: Path, out_csv: Path, cohort: str) -> None:
    gold = load_gold(GOLD)
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    reverse = load_reverse_map()
    rows_out: list[dict] = []
    for row in csv.DictReader(manifest.open(encoding="utf-8")):
        base = dict(row)
        base["cohort"] = cohort
        run_dir = REPO / row["expected_output_dir"]
        meta_path = run_dir / "metadata.json"
        parsed_path = run_dir / "parsed.json"
        if not meta_path.is_file():
            base["scored"] = "missing"
            rows_out.append(base)
            continue
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        base["run_status"] = meta.get("run_status") or (
            "VALID" if meta.get("parse_ok") else "MODEL_INVALID"
        )
        if meta.get("execution_status") == "INFRA_FAILURE" or base["run_status"] == "INFRASTRUCTURE_FAILURE":
            base["scored"] = "infra_failure"
            rows_out.append(base)
            continue
        if not parsed_path.is_file() or parsed_path.read_text(encoding="utf-8").strip() == "null":
            base["scored"] = "model_invalid"
            rows_out.append(base)
            continue
        decomp = json.loads(parsed_path.read_text(encoding="utf-8"))
        if row.get("identifier_condition") == "ANONYMIZED":
            ca = decomp.get("component_assignment") or {}
            decomp = dict(decomp)
            decomp["component_assignment"] = reverse_assignment(ca, reverse)
        scored = evaluate_decomposition(decomp, gold, evidence)
        pair = scored.get("pairwise") or {}
        base.update(
            {
                "scored": "ok",
                "pairwise_f1": pair.get("f1"),
                "ari": scored.get("ari"),
                "nmi": scored.get("nmi"),
                "rule_compliance": scored.get("rule_compliance"),
            }
        )
        rows_out.append(base)

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for r in rows_out:
        for k in r:
            if k not in fields:
                fields.append(k)
    with out_csv.open("w", encoding="utf-8", newline="") as handle:
        w = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows_out)
    print(f"Wrote {out_csv} ({len(rows_out)} rows)")


def main() -> None:
    score_manifest(
        GEMINI_DIR / "run_manifest_identifier_40.csv",
        GEMINI_DIR / "results" / "run_level_identifier.csv",
        "GEMINI_38_EDUR_IDENTIFIER_V1",
    )
    score_manifest(
        GEMINI_DIR / "run_manifest_rq3_12.csv",
        GEMINI_DIR / "results" / "run_level_rq3.csv",
        "GEMINI_38_EDUR_RQ3_V1",
    )


if __name__ == "__main__":
    main()
