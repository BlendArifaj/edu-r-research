#!/usr/bin/env python3
"""Generate semantic vs anonymized prompt files (no LLM execution)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from decomposition.llm.prompts import build_prompt  # noqa: E402

CONDITIONS = ["C0", "C1", "C2", "C3"]
SEMANTIC_EVIDENCE = REPO / "outputs" / "evidence" / "architectural_evidence.json"
ANON_EVIDENCE = BASE / "evidence" / "architectural_evidence_anonymized.json"
PROMPT_DIR = BASE / "prompts"


def main() -> None:
    semantic = json.loads(SEMANTIC_EVIDENCE.read_text(encoding="utf-8"))
    anonymized = json.loads(ANON_EVIDENCE.read_text(encoding="utf-8"))
    PROMPT_DIR.mkdir(parents=True, exist_ok=True)
    for condition in CONDITIONS:
        sem_path = PROMPT_DIR / f"{condition}_SEMANTIC.txt"
        anon_path = PROMPT_DIR / f"{condition}_ANON.txt"
        sem_path.write_text(build_prompt(condition, semantic) + "\n", encoding="utf-8")
        anon_path.write_text(build_prompt(condition, anonymized) + "\n", encoding="utf-8")
        print(sem_path.name, anon_path.name)
    print(f"Wrote {len(CONDITIONS) * 2} prompt files under {PROMPT_DIR}")


if __name__ == "__main__":
    main()
