#!/usr/bin/env python3
"""Regenerate FINAL_ARTIFACT_MANIFEST.sha256 for REVISION_CONTROL_V1 freeze."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BASE = REPO / "revision_anonymization"
OUT = BASE / "FINAL_ARTIFACT_MANIFEST.sha256"


def add(path: Path, seen: set[str], lines: list[str]) -> None:
    if not path.is_file():
        return
    rel = path.relative_to(REPO).as_posix()
    if rel in seen:
        return
    seen.add(rel)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    lines.append(f"{digest}  {rel}")


def main() -> None:
    seen: set[str] = set()
    lines: list[str] = []
    for p in sorted(BASE.rglob("*")):
        if not p.is_file() or p.name == OUT.name:
            continue
        if p.suffix in {".md", ".csv", ".json", ".txt"} and "results" not in p.parts:
            if p.parent.name == "scripts" and p.name != "generate_final_manifest.py":
                continue
            add(p, seen, lines)
    for p in sorted((BASE / "prompts").glob("*.txt")):
        add(p, seen, lines)
    for p in sorted((BASE / "evidence").glob("*")):
        if p.is_file():
            add(p, seen, lines)
    for name in (
        "analyze_revision.py",
        "score_revision.py",
        "execute_revision.py",
        "verify_anonymization.py",
        "generate_run_manifest.py",
        "generate_final_manifest.py",
    ):
        add(BASE / "scripts" / name, seen, lines)
    for rel in (
        "decomposition/evaluation/scoring.py",
        "decomposition/evaluation/pairwise.py",
        "decomposition/evaluation/stability.py",
        "decomposition/evaluation/gold.py",
        "decomposition/llm/parse.py",
    ):
        add(REPO / rel, seen, lines)
    add(BASE / "run_manifest.csv", seen, lines)
    for name in (
        "run_level_results.csv",
        "full_factorial_summary.csv",
        "evidence_effects_anonymized.csv",
        "paired_identifier_effects.csv",
        "identifier_effects_by_metric.csv",
        "historical_replication_check.csv",
        "validity_summary.csv",
        "cell_summary.csv",
        "REVISION_CONTROL_RESULTS.md",
        "PUBLICATION_RESULTS_FREEZE.md",
        "validation_results.json",
        "run_manifest.csv",
    ):
        add(BASE / "results" / name, seen, lines)
    add(BASE / "validation_results.json", seen, lines)
    add(BASE / "llama_digest_frozen.txt", seen, lines)
    add(BASE / "FREEZE_REVISION_CONTROL_V1/PROVENANCE.json", seen, lines)
    add(BASE / "FREEZE_REVISION_CONTROL_V1/README.md", seen, lines)
    add(BASE / "REVISION_CLAIM_MATRIX.md", seen, lines)
    add(BASE / "REVIEWER_RESOLUTION_MATRIX.md", seen, lines)
    for row in csv.DictReader((BASE / "run_manifest.csv").open(encoding="utf-8")):
        d = REPO / row["expected_output_dir"]
        for fn in (
            "prompt.txt",
            "evidence_snapshot.json",
            "raw_response.txt",
            "parsed.json",
            "metadata.json",
        ):
            add(d / fn, seen, lines)
    lines.sort(key=lambda x: x.split("  ", 1)[1])
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    manifest_hash = hashlib.sha256(OUT.read_bytes()).hexdigest()
    print(f"Wrote {len(lines)} entries to {OUT}")
    print(f"manifest_file_sha256={manifest_hash}")


if __name__ == "__main__":
    main()
