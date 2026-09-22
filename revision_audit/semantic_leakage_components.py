#!/usr/bin/env python3
"""Component semantic cue inventory from architectural evidence."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EVIDENCE = REPO / "outputs" / "evidence" / "architectural_evidence.json"
GOLD = REPO / "reference" / "historical_architecture.json"
OUT = Path(__file__).resolve().parent / "semantic_leakage_components.csv"

DOMAIN_TOKENS = [
    "faculty",
    "student",
    "grade",
    "finance",
    "attendance",
    "library",
    "auth",
    "user",
    "enrollment",
    "report",
]


def gold_owner(component: str) -> str:
    data = json.loads(GOLD.read_text(encoding="utf-8"))
    for service, payload in (data.get("services") or {}).items():
        if component in (payload.get("components") or []):
            return service
    extra = (data.get("evaluation_notes") or {}).get("legacy_components_in_six_way") or {}
    return str(extra.get(component, ""))


def cues(name: str) -> str:
    lower = name.lower()
    hits = [t for t in DOMAIN_TOKENS if t in lower]
    return "|".join(hits) if hits else ""


def main() -> None:
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    rows = []
    for row in evidence.get("components") or []:
        name = str(row.get("name") or "")
        if not name:
            continue
        rows.append(
            {
                "component": name,
                "kind": str(row.get("kind") or ""),
                "module": str(row.get("module") or ""),
                "semantic_cue_tokens": cues(name),
                "likely_reference_service": gold_owner(name),
            }
        )
    with OUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda r: r["component"]))
    print(f"Wrote {len(rows)} rows to {OUT}")


if __name__ == "__main__":
    main()
