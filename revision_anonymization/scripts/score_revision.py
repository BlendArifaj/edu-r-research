#!/usr/bin/env python3
"""Score REVISION_CONTROL_V1 runs with reverse-map for ANONYMIZED arm."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from decomposition.evaluation.gold import load_gold
from decomposition.evaluation.scoring import evaluate_decomposition

MANIFEST = BASE / "run_manifest.csv"
MAP_CSV = BASE / "component_identifier_map.csv"
GOLD = REPO / "reference" / "historical_architecture.json"
EVIDENCE = REPO / "outputs/evidence/architectural_evidence.json"
OUT = BASE / "results" / "run_level_results.csv"


def load_reverse_map() -> dict[str, str]:
    rev: dict[str, str] = {}
    with MAP_CSV.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rev[row["anonymized_identifier"]] = row["original_identifier"]
    return rev


def reverse_assignment(assignment: dict[str, str], reverse: dict[str, str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, val in assignment.items():
        orig_key = reverse.get(key, key)
        out[orig_key] = val
    return out


def main() -> None:
    gold = load_gold(GOLD)
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    reverse = load_reverse_map()
    rows_out = []
    for row in csv.DictReader(MANIFEST.open(encoding="utf-8")):
        run_dir = REPO / row["expected_output_dir"]
        meta_path = run_dir / "metadata.json"
        parsed_path = run_dir / "parsed.json"
        base = dict(row)
        if not meta_path.is_file():
            base.update({"scored": "missing"})
            rows_out.append(base)
            continue
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("execution_status") == "INFRA_FAILURE":
            base.update({"scored": "infra_failure"})
            rows_out.append(base)
            continue
        if not parsed_path.is_file() or parsed_path.read_text(encoding="utf-8").strip() == "null":
            base.update({"scored": "invalid_parse", "pairwise_f1": ""})
            rows_out.append(base)
            continue
        decomp = json.loads(parsed_path.read_text(encoding="utf-8"))
        if row["identifier_condition"] == "ANONYMIZED":
            ca = decomp.get("component_assignment") or {}
            decomp = dict(decomp)
            decomp["component_assignment"] = reverse_assignment(ca, reverse)
        scored = evaluate_decomposition(decomp, gold, evidence)
        pair = scored.get("pairwise") or {}
        base.update(
            {
                "scored": "ok",
                "pairwise_precision": pair.get("precision"),
                "pairwise_recall": pair.get("recall"),
                "pairwise_f1": pair.get("f1"),
                "ari": scored.get("ari"),
                "nmi": scored.get("nmi"),
                "rule_compliance": scored.get("rule_compliance"),
            }
        )
        rows_out.append(base)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    if rows_out:
        fieldnames: list[str] = []
        seen: set[str] = set()
        for r in rows_out:
            for k in r:
                if k not in seen:
                    seen.add(k)
                    fieldnames.append(k)
        extra = [
            "scored",
            "pairwise_precision",
            "pairwise_recall",
            "pairwise_f1",
            "ari",
            "nmi",
            "rule_compliance",
        ]
        for k in extra:
            if k not in seen:
                fieldnames.append(k)
        with OUT.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows_out)
    print(f"Wrote {OUT} ({len(rows_out)} rows)")


if __name__ == "__main__":
    main()
