#!/usr/bin/env python3
"""Build deterministic identifier maps (components + functional areas)."""

from __future__ import annotations

import csv
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
EVIDENCE = REPO / "outputs" / "evidence" / "architectural_evidence.json"
GOLD = REPO / "reference" / "historical_architecture.json"
BASE = Path(__file__).resolve().parents[1]
COMP_MAP = BASE / "component_identifier_map.csv"
AREA_MAP = BASE / "functional_area_identifier_map.csv"


def main() -> None:
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    names = sorted({str(c["name"]) for c in evidence.get("components") or [] if c.get("name")})
    if len(names) != 26:
        raise SystemExit(f"expected 26 components, got {len(names)}")
    gold = json.loads(GOLD.read_text(encoding="utf-8"))
    excluded = set(gold.get("shared_identity", {}).get("components") or [])
    comp_rows = []
    for index, original in enumerate(names, start=1):
        anon = f"Component_{index:02d}"
        comp_rows.append(
            {
                "original_identifier": original,
                "anonymized_identifier": anon,
                "sort_index": index,
                "anonymized_module": f"Module_{index:02d}",
                "anonymized_file": f"artifacts/{anon}.py",
                "in_six_way_eval_universe": "yes" if original not in excluded else "no",
            }
        )
    with COMP_MAP.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(comp_rows[0].keys()))
        writer.writeheader()
        writer.writerows(comp_rows)

    domain = evidence.get("domain_descriptions") or {}
    area_ids = sorted(
        {str(a.get("id") or "") for a in domain.get("functional_areas") or [] if a.get("id")}
    )
    area_rows = []
    for index, original in enumerate(area_ids, start=1):
        area_rows.append(
            {
                "original_area_id": original,
                "anonymized_area_id": f"Area_{index:02d}",
                "sort_index": index,
            }
        )
    with AREA_MAP.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(area_rows[0].keys()))
        writer.writeheader()
        writer.writerows(area_rows)
    print(f"Wrote {len(comp_rows)} components, {len(area_rows)} areas")


if __name__ == "__main__":
    main()
