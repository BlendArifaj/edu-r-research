#!/usr/bin/env python3
"""Score PETCLINIC_EXT_V1 runs (primary + sensitivity gold)."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BASE = REPO / "external_validation_petclinic"
sys.path.insert(0, str(REPO))

from decomposition.evaluation.gold import load_gold
from decomposition.evaluation.scoring import evaluate_decomposition

MANIFEST = BASE / "run_manifest.csv"
MAP_CSV = BASE / "component_identifier_map.csv"
GOLD_PRIMARY = BASE / "reference" / "petclinic_gold_PRIMARY_15.json"
GOLD_SENS = BASE / "reference" / "petclinic_gold_SENSITIVITY_CV_13.json"
OUT = BASE / "results" / "run_level_results.csv"


def load_reverse_map() -> dict[str, str]:
    rev: dict[str, str] = {}
    with MAP_CSV.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rev[row["anonymized_identifier"]] = row["original_identifier"]
    return rev


def reverse_assignment(assignment: dict[str, str], rev: dict[str, str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, val in assignment.items():
        out[rev.get(key, key)] = val
    return out


def score_one(decomp: dict, gold: dict, evidence: dict) -> dict:
    return evaluate_decomposition(decomp, gold, evidence)


def main() -> None:
    gold_p = load_gold(GOLD_PRIMARY)
    gold_s = load_gold(GOLD_SENS)
    rev = load_reverse_map()
    rows_out = []
    for row in csv.DictReader(MANIFEST.open(encoding="utf-8")):
        base = dict(row)
        meta_path = REPO / row["expected_output_path"] / "metadata.json"
        parsed_path = REPO / row["expected_output_path"] / "parsed.json"
        if not meta_path.is_file():
            base.update({"scored": "missing"})
            rows_out.append(base)
            continue
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        base["run_status"] = meta.get("run_status", "")
        if meta.get("run_status") == "INFRASTRUCTURE_FAILURE":
            base.update({"scored": "infra_failure"})
            rows_out.append(base)
            continue
        if not parsed_path.is_file() or parsed_path.read_text(encoding="utf-8").strip() == "null":
            base.update({"scored": "model_invalid"})
            rows_out.append(base)
            continue
        decomp = json.loads(parsed_path.read_text(encoding="utf-8"))
        if row["identifier_condition"] == "ANONYMIZED":
            ca = decomp.get("component_assignment") or {}
            decomp = dict(decomp)
            decomp["component_assignment"] = reverse_assignment(ca, rev)
        evidence = json.loads((REPO / row["evidence_path"]).read_text(encoding="utf-8"))
        primary = score_one(decomp, gold_p, evidence)
        sensitivity = score_one(decomp, gold_s, evidence)
        pair_p = primary.get("pairwise") or {}
        pair_s = sensitivity.get("pairwise") or {}
        base.update(
            {
                "scored": "ok",
                "pairwise_f1_primary": pair_p.get("f1"),
                "pairwise_precision_primary": pair_p.get("precision"),
                "pairwise_recall_primary": pair_p.get("recall"),
                "ari_primary": primary.get("ari"),
                "nmi_primary": primary.get("nmi"),
                "pairwise_f1_sensitivity_cv": pair_s.get("f1"),
                "ari_sensitivity_cv": pair_s.get("ari"),
                "nmi_sensitivity_cv": pair_s.get("nmi"),
            }
        )
        rows_out.append(base)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    seen: set[str] = set()
    for r in rows_out:
        for k in r:
            if k not in seen:
                seen.add(k)
                fieldnames.append(k)
    with OUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows_out)
    print(f"Wrote {OUT} ({len(rows_out)} rows)")


if __name__ == "__main__":
    main()
