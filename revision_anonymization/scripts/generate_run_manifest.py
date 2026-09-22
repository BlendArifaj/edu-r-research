#!/usr/bin/env python3
"""120-run revision manifest with counterbalanced pair order."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "run_manifest.csv"
OUT_BASELINE = BASE / "original_submitted_baseline_manifest.csv"
DIGEST_FILE = BASE / "llama_digest_frozen.txt"
REVISION_RUN_ROOT = "outputs/runs/anonymization_exp_v1"
GIT_SHA = subprocess.check_output(
    ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
).strip()
PARSER_VERSION = "decomposition/llm/parse.py@anonymization_exp_v2"
PROTOCOL_VERSION = "anonymization_exp_v2"
MAX_INFRA_RETRIES = "2"
TEMPERATURE = "0.2"

MODELS = [
    ("gemini-2.5-flash", "gemini", "gemini-2.5-flash"),
    ("gpt-4o-mini", "openai", "gpt-4o-mini"),
    ("llama3.1", "ollama", "llama3.1"),
]
CONDITIONS = ["C0", "C1", "C2", "C3"]


def read_llama_digest() -> str:
    if not DIGEST_FILE.is_file():
        return ""
    for line in DIGEST_FILE.read_text(encoding="utf-8").splitlines():
        if line.startswith("digest:"):
            return line.split(":", 1)[1].strip()
    return ""


def sha256_file(path: Path) -> str:
    if not path.is_file():
        return ""
    import hashlib

    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def pair_first_condition(pair_index: int) -> str:
    """Odd pair_index -> SEMANTIC first; even -> ANONYMIZED first (1-based)."""
    return "SEMANTIC" if pair_index % 2 == 1 else "ANONYMIZED"


def main() -> None:
    llama_digest = read_llama_digest()
    pairs: list[dict] = []
    pair_index = 0
    for model, provider, model_id in MODELS:
        safe = model.replace("/", "-")
        for condition in CONDITIONS:
            for rep in range(1, 6):
                pair_index += 1
                pair_id = f"{model}|{condition}|{rep}"
                first = pair_first_condition(pair_index)
                second = "ANONYMIZED" if first == "SEMANTIC" else "SEMANTIC"
                for position, ident in ((1, first), (2, second)):
                    sem_prompt = BASE / "prompts" / f"{condition}_SEMANTIC.txt"
                    anon_prompt = BASE / "prompts" / f"{condition}_ANON.txt"
                    sem_evidence = REPO / "outputs/evidence/architectural_evidence.json"
                    anon_evidence = BASE / "evidence/architectural_evidence_anonymized.json"
                    if ident == "SEMANTIC":
                        prompt_path = sem_prompt
                        evidence_path = sem_evidence
                        sub = "semantic"
                    else:
                        prompt_path = anon_prompt
                        evidence_path = anon_evidence
                        sub = "anonymized"
                    pairs.append(
                        {
                            "cohort": "REVISION_CONTROL_V1",
                            "status": "PLANNED_NEW",
                            "pair_id": pair_id,
                            "pair_index": str(pair_index),
                            "pair_position": str(position),
                            "pair_first_condition": first,
                            "identifier_condition": ident,
                            "model": model,
                            "provider": provider,
                            "requested_model_id": model_id,
                            "resolved_model_version": "",
                            "llama_artifact_digest": llama_digest if provider == "ollama" else "",
                            "evidence_condition": condition,
                            "repetition": str(rep),
                            "temperature": TEMPERATURE,
                            "max_infra_retries": MAX_INFRA_RETRIES,
                            "protocol_version": PROTOCOL_VERSION,
                            "prompt_path": str(prompt_path.relative_to(REPO)),
                            "evidence_path": str(evidence_path.relative_to(REPO)),
                            "prompt_sha256": sha256_file(prompt_path),
                            "evidence_sha256": sha256_file(evidence_path),
                            "git_sha": GIT_SHA,
                            "parser_scorer_version": PARSER_VERSION,
                            "execution_timestamp": "",
                            "seed_if_supported": "",
                            "attempt_count": "",
                            "infra_retry_count": "",
                            "execution_status": "",
                            "parse_status": "",
                            "invalid_reason": "",
                            "expected_output_dir": (
                                f"{REVISION_RUN_ROOT}/decompositions/{safe}/"
                                f"{condition}/{sub}/run_{rep:02d}"
                            ),
                        }
                    )

    # Stable pair order: model, condition, rep — rows already in pair order with counterbalance
    rows: list[dict[str, str]] = []
    for i, row in enumerate(pairs, start=1):
        rows.append({"run_id": f"REV-{i:03d}", "execution_order": str(i), **row})

    fields = list(rows[0].keys())
    with OUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    baseline_rows = []
    for model, provider, model_id in MODELS:
        safe = model.replace("/", "-")
        for condition in CONDITIONS:
            for rep in range(1, 4):
                baseline_rows.append(
                    {
                        "cohort": "ORIGINAL_SUBMITTED_BASELINE",
                        "status": "FROZEN_HISTORICAL",
                        "model": model,
                        "provider": provider,
                        "requested_model_id": model_id,
                        "evidence_condition": condition,
                        "repetition": str(rep),
                        "path": (
                            f"outputs/runs/2026-08-27_005/decompositions/"
                            f"{safe}/{condition}/run_{rep:02d}"
                        ),
                        "analysis_use": "historical_replication_check_only",
                    }
                )
    with OUT_BASELINE.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(baseline_rows[0].keys()))
        writer.writeheader()
        writer.writerows(baseline_rows)

    first_sem = sum(1 for r in rows if r["pair_position"] == "1" and r["identifier_condition"] == "SEMANTIC")
    first_anon = sum(1 for r in rows if r["pair_position"] == "1" and r["identifier_condition"] == "ANONYMIZED")
    print(f"rows={len(rows)} pair_first SEMANTIC={first_sem} ANONYMIZED={first_anon}")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
