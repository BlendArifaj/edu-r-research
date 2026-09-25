#!/usr/bin/env python3
"""Execute Gemini 3.8 EDU-R identifier manifest (40 runs)."""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx

REPO = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = BASE / "gemini_38_edur" / "run_manifest_identifier_40.csv"
MAX_INFRA_RETRIES = 2
BACKOFFS = (5, 15)

sys.path.insert(0, str(REPO))
from decomposition.llm.convert import proposal_to_decomposition
from decomposition.llm.parse import format_validation_error, parse_proposal
from decomposition.llm.providers import MissingCredentialsError, get_provider


def load_dotenv() -> None:
    env_path = REPO / ".env"
    if not env_path.is_file():
        return
    import os

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


def is_infra_error(exc: Exception) -> bool:
    if isinstance(exc, MissingCredentialsError):
        return True
    if isinstance(exc, httpx.TimeoutException | httpx.ConnectError | httpx.NetworkError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code >= 500 or exc.response.status_code == 429
    msg = str(exc).lower()
    return "timeout" in msg or "connection" in msg or "http 5" in msg or "rate" in msg


def classify_run(execution_status: str, parse_status: str) -> str:
    if execution_status == "INFRA_FAILURE":
        return "INFRASTRUCTURE_FAILURE"
    if parse_status == "valid":
        return "VALID"
    return "MODEL_INVALID"


def run_row(row: dict[str, str]) -> dict[str, str]:
    run_dir = REPO / row["expected_output_dir"]
    run_dir.mkdir(parents=True, exist_ok=True)
    prompt = (REPO / row["prompt_path"]).read_text(encoding="utf-8")
    evidence_bytes = (REPO / row["evidence_path"]).read_bytes()
    (run_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
    (run_dir / "evidence_snapshot.json").write_bytes(evidence_bytes)
    attempt_log = run_dir / "attempt_log.jsonl"

    provider = get_provider(row["provider"])
    model = row["requested_model_id"]
    temperature = float(row["temperature"])
    condition = row["evidence_condition"]
    run_number = int(row["repetition"])

    raw = ""
    parsed = None
    error = None
    attempt_count = 0
    execution_status = "COMPLETED"
    parse_status = "not_applicable"

    for attempt in range(MAX_INFRA_RETRIES + 1):
        attempt_count = attempt + 1
        try:
            raw = provider.generate(prompt, model=model, temperature=temperature)
            break
        except Exception as exc:
            error = format_validation_error(exc)
            attempt_log.open("a", encoding="utf-8").write(
                json.dumps({"attempt": attempt_count, "type": "infra", "error": error}) + "\n"
            )
            if attempt < MAX_INFRA_RETRIES and is_infra_error(exc):
                time.sleep(BACKOFFS[min(attempt, len(BACKOFFS) - 1)])
                continue
            execution_status = "INFRA_FAILURE"
            parse_status = "not_applicable"
            raw = raw or ""
            break

    if execution_status == "COMPLETED":
        try:
            parsed = parse_proposal(raw)
            parse_status = "valid"
            error = None
        except Exception as exc:
            parsed = None
            parse_status = "invalid"
            error = format_validation_error(exc)
            attempt_log.open("a", encoding="utf-8").write(
                json.dumps({"attempt": 1, "type": "parse", "error": error}) + "\n"
            )

    (run_dir / "raw_response.txt").write_text(raw, encoding="utf-8")
    run_status = classify_run(execution_status, parse_status)
    metadata = {
        "run_id": row["run_id"],
        "cohort": row["cohort"],
        "protocol_version": row["protocol_version"],
        "pair_id": row["pair_id"],
        "pair_position": row["pair_position"],
        "pair_first_condition": row["pair_first_condition"],
        "identifier_condition": row["identifier_condition"],
        "model": model,
        "provider": row["provider"],
        "requested_model_id": model,
        "resolved_model_version": row.get("resolved_model_version") or "",
        "temperature": temperature,
        "timestamp": datetime.now(UTC).isoformat(),
        "condition": condition,
        "run_number": run_number,
        "attempt_count": attempt_count,
        "infra_retry_count": max(attempt_count - 1, 0),
        "execution_status": execution_status,
        "parse_status": parse_status,
        "run_status": run_status,
        "invalid_reason": error or "",
        "parse_ok": parsed is not None,
        "is_scientific_run": run_status == "VALID",
        "prompt_sha256": row["prompt_sha256"],
        "evidence_sha256": row["evidence_sha256"],
        "git_sha": row["git_sha"],
    }
    (run_dir / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    if parsed is None:
        (run_dir / "parsed.json").write_text("null\n", encoding="utf-8")
    else:
        method = f"llm_{model.replace('/', '-')}_{condition}_{row['identifier_condition']}"
        decomposition = proposal_to_decomposition(parsed, method=method, metadata=metadata)
        (run_dir / "parsed.json").write_text(json.dumps(decomposition, indent=2) + "\n", encoding="utf-8")

    row.update(
        {
            "execution_status": execution_status,
            "parse_status": parse_status,
            "run_status": run_status,
            "invalid_reason": error or "",
            "attempt_count": str(attempt_count),
            "infra_retry_count": str(max(attempt_count - 1, 0)),
            "execution_timestamp": metadata["timestamp"],
        }
    )
    return row


def should_skip(row: dict[str, str]) -> bool:
    meta_path = REPO / row["expected_output_dir"] / "metadata.json"
    if not meta_path.is_file():
        return False
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if meta.get("run_status") in ("VALID", "MODEL_INVALID"):
        return True
    if meta.get("execution_status") == "INFRA_FAILURE":
        return False
    return meta.get("execution_status") == "COMPLETED" and meta.get("parse_status") == "valid"


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    args = parser.parse_args()
    manifest = Path(args.manifest)
    if not manifest.is_absolute():
        manifest = REPO / manifest

    rows = list(csv.DictReader(manifest.open(encoding="utf-8")))
    rows.sort(key=lambda r: int(r["execution_order"]))
    completed: list[dict[str, str]] = []
    for row in rows:
        if should_skip(row):
            meta = json.loads((REPO / row["expected_output_dir"] / "metadata.json").read_text())
            row.update(
                {
                    "execution_status": str(meta.get("execution_status", "")),
                    "parse_status": str(meta.get("parse_status", "")),
                    "invalid_reason": str(meta.get("invalid_reason", "")),
                    "attempt_count": str(meta.get("attempt_count", "")),
                    "infra_retry_count": str(meta.get("infra_retry_count", "")),
                    "execution_timestamp": str(meta.get("timestamp", "")),
                    "run_status": str(meta.get("run_status", "")),
                }
            )
            completed.append(row)
            continue
        print(
            f"Executing {row['run_id']} {row['identifier_condition']} {row['evidence_condition']} rep{row['repetition']}"
        )
        completed.append(run_row(row))

    with manifest.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(completed[0].keys()))
        writer.writeheader()
        writer.writerows(completed)
    print(f"Done {len(completed)} runs -> {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
