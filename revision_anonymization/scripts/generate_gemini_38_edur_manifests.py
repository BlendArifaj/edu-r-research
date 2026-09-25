#!/usr/bin/env python3
"""Frozen EDU-R Gemini 3.8 manifests (40 identifier + 12 RQ3 semantic)."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parents[1]
OUT_DIR = BASE / "gemini_38_edur"
IDENT_ROOT = "outputs/runs/gemini_38_edur_identifier_v1"
RQ3_ROOT = "outputs/runs/gemini_38_edur_rq3_v1"
MODEL = "gemini-3.8-flash"
PROVIDER = "gemini"
TEMPERATURE = "0.2"
MAX_INFRA_RETRIES = "2"
PROTOCOL_VERSION = "gemini_38_edur_v1"
PARSER_VERSION = "decomposition/llm/parse.py@anonymization_exp_v2"
CONDITIONS = ["C0", "C1", "C2", "C3"]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def pair_first_condition(pair_index: int) -> str:
    return "SEMANTIC" if pair_index % 2 == 1 else "ANONYMIZED"


def git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    except Exception:
        return ""


def build_identifier_rows() -> list[dict[str, str]]:
    safe = MODEL.replace("/", "-")
    rows: list[dict[str, str]] = []
    pair_index = 0
    order = 0
    for condition in CONDITIONS:
        for rep in range(1, 6):
            pair_index += 1
            pair_id = f"{MODEL}|{condition}|{rep}"
            first = pair_first_condition(pair_index)
            second = "ANONYMIZED" if first == "SEMANTIC" else "SEMANTIC"
            for position, ident in ((1, first), (2, second)):
                order += 1
                if ident == "SEMANTIC":
                    prompt_path = BASE / "prompts" / f"{condition}_SEMANTIC.txt"
                    evidence_path = REPO / "outputs/evidence/architectural_evidence.json"
                    sub = "semantic"
                else:
                    prompt_path = BASE / "prompts" / f"{condition}_ANON.txt"
                    evidence_path = BASE / "evidence/architectural_evidence_anonymized.json"
                    sub = "anonymized"
                rows.append(
                    {
                        "run_id": f"G38I-{order:03d}",
                        "execution_order": str(order),
                        "cohort": "GEMINI_38_EDUR_IDENTIFIER_V1",
                        "status": "PLANNED_NEW",
                        "pair_id": pair_id,
                        "pair_index": str(pair_index),
                        "pair_position": str(position),
                        "pair_first_condition": first,
                        "identifier_condition": ident,
                        "model": MODEL,
                        "provider": PROVIDER,
                        "requested_model_id": MODEL,
                        "resolved_model_version": "",
                        "evidence_condition": condition,
                        "repetition": str(rep),
                        "temperature": TEMPERATURE,
                        "max_infra_retries": MAX_INFRA_RETRIES,
                        "protocol_version": PROTOCOL_VERSION,
                        "prompt_path": str(prompt_path.relative_to(REPO)),
                        "evidence_path": str(evidence_path.relative_to(REPO)),
                        "prompt_sha256": sha256_file(prompt_path),
                        "evidence_sha256": sha256_file(evidence_path),
                        "git_sha": git_sha(),
                        "parser_scorer_version": PARSER_VERSION,
                        "execution_timestamp": "",
                        "attempt_count": "",
                        "infra_retry_count": "",
                        "execution_status": "",
                        "parse_status": "",
                        "invalid_reason": "",
                        "run_status": "",
                        "expected_output_dir": (
                            f"{IDENT_ROOT}/decompositions/{safe}/{condition}/{sub}/run_{rep:02d}"
                        ),
                    }
                )
    return rows


def build_rq3_rows() -> list[dict[str, str]]:
    safe = MODEL.replace("/", "-")
    rows: list[dict[str, str]] = []
    order = 0
    for condition in CONDITIONS:
        for rep in range(1, 4):
            order += 1
            rows.append(
                {
                    "run_id": f"G38R-{order:03d}",
                    "execution_order": str(order),
                    "cohort": "GEMINI_38_EDUR_RQ3_V1",
                    "status": "PLANNED_NEW",
                    "model": MODEL,
                    "provider": PROVIDER,
                    "requested_model_id": MODEL,
                    "resolved_model_version": "",
                    "evidence_condition": condition,
                    "repetition": str(rep),
                    "temperature": TEMPERATURE,
                    "max_infra_retries": MAX_INFRA_RETRIES,
                    "protocol_version": PROTOCOL_VERSION,
                    "identifier_condition": "SEMANTIC",
                    "prompt_source": "decomposition.llm.prompts",
                    "git_sha": git_sha(),
                    "parser_scorer_version": PARSER_VERSION,
                    "execution_timestamp": "",
                    "attempt_count": "",
                    "execution_status": "",
                    "parse_status": "",
                    "invalid_reason": "",
                    "run_status": "",
                    "expected_output_dir": (
                        f"{RQ3_ROOT}/decompositions/{safe}/{condition}/run_{rep:02d}"
                    ),
                }
            )
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)
    with path.open("w", encoding="utf-8", newline="") as handle:
        w = csv.DictWriter(handle, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    ident = build_identifier_rows()
    rq3 = build_rq3_rows()
    assert len(ident) == 40
    assert len(rq3) == 12
    write_csv(OUT_DIR / "run_manifest_identifier_40.csv", ident)
    write_csv(OUT_DIR / "run_manifest_rq3_12.csv", rq3)
    print(f"Wrote {len(ident)} identifier + {len(rq3)} RQ3 rows under {OUT_DIR}")


if __name__ == "__main__":
    main()
