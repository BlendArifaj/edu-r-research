#!/usr/bin/env python3
"""Execute PETCLINIC_EXT_V1 frozen manifest (60 runs)."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx

REPO = Path(__file__).resolve().parents[2]
BASE = REPO / "external_validation_petclinic"
MANIFEST = BASE / "run_manifest.csv"
MAX_INFRA_RETRIES = 2
BACKOFFS = (5, 15)

MODEL_PROVIDER = {
    "gemini-2.5-flash": "gemini",
    "gemini-3.8-flash": "gemini",
    "gpt-4o-mini": "openai",
    "llama3.1": "ollama",
}

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
    return "timeout" in msg or "connection" in msg or "rate" in msg


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_full_prompt(prompt: str, evidence: dict) -> str:
    return (
        prompt
        + "\n\n## Evidence JSON (authoritative)\n```json\n"
        + json.dumps(evidence, indent=2)
        + "\n```\n"
    )


def classify_status(execution_status: str, parse_status: str) -> str:
    if execution_status == "INFRASTRUCTURE_FAILURE":
        return "INFRASTRUCTURE_FAILURE"
    if parse_status == "valid":
        return "VALID"
    return "MODEL_INVALID"


def run_row(row: dict[str, str]) -> dict[str, str]:
    run_id = row["run_id"]
    run_dir = REPO / row["expected_output_path"]
    run_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = REPO / "outputs" / "raw"
    parsed_dir = REPO / "outputs" / "parsed"
    status_dir = REPO / "outputs" / "status"
    raw_dir.mkdir(parents=True, exist_ok=True)
    parsed_dir.mkdir(parents=True, exist_ok=True)
    status_dir.mkdir(parents=True, exist_ok=True)

    prompt = (REPO / row["prompt_path"]).read_text(encoding="utf-8")
    evidence = json.loads((REPO / row["evidence_path"]).read_text(encoding="utf-8"))
    full_prompt = build_full_prompt(prompt, evidence)
    (run_dir / "prompt.txt").write_text(full_prompt, encoding="utf-8")
    (run_dir / "evidence_snapshot.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")

    provider_name = MODEL_PROVIDER[row["model"]]
    provider = get_provider(provider_name)
    model = row["requested_model_id"]
    temperature = float(row["temperature"])
    attempt_log = run_dir / "attempt_log.jsonl"

    t0 = time.perf_counter()
    raw = ""
    parsed = None
    error = None
    attempt_count = 0
    execution_status = "COMPLETED"
    parse_status = "not_applicable"

    for attempt in range(MAX_INFRA_RETRIES + 1):
        attempt_count = attempt + 1
        try:
            raw = provider.generate(full_prompt, model=model, temperature=temperature)
            break
        except Exception as exc:
            error = format_validation_error(exc)
            attempt_log.open("a", encoding="utf-8").write(
                json.dumps({"attempt": attempt_count, "type": "infra", "error": error}) + "\n"
            )
            if attempt < MAX_INFRA_RETRIES and is_infra_error(exc):
                time.sleep(BACKOFFS[min(attempt, len(BACKOFFS) - 1)])
                continue
            execution_status = "INFRASTRUCTURE_FAILURE"
            parse_status = "not_applicable"
            break

    latency_ms = round((time.perf_counter() - t0) * 1000, 2)

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

    raw_path = run_dir / "raw_response.txt"
    raw_path.write_text(raw, encoding="utf-8")
    raw_hash = sha256_text(raw)
    (REPO / "outputs" / "raw" / f"{run_id}.txt").write_text(raw, encoding="utf-8")
    (REPO / "outputs" / "raw" / f"{run_id}.sha256").write_text(raw_hash + "\n", encoding="utf-8")

    run_status = classify_status(execution_status, parse_status)
    status_payload = {
        "run_id": run_id,
        "run_status": run_status,
        "execution_status": execution_status,
        "parse_status": parse_status,
        "invalid_reason": error or "",
        "latency_ms": latency_ms,
        "attempt_count": attempt_count,
        "infra_retry_count": max(attempt_count - 1, 0),
        "timestamp": datetime.now(UTC).isoformat(),
        "model": model,
        "provider": provider_name,
        "requested_model_id": model,
        "resolved_model_version": row.get("resolved_model_version") or "",
        "evidence_condition": row["evidence_condition"],
        "identifier_condition": row["identifier_condition"],
        "repetition": row["repetition"],
        "temperature": temperature,
        "raw_sha256": raw_hash,
        "prompt_sha256": row["prompt_sha256"],
        "evidence_sha256": row["evidence_sha256"],
    }
    (run_dir / "metadata.json").write_text(json.dumps(status_payload, indent=2) + "\n", encoding="utf-8")
    (status_dir / f"{run_id}.json").write_text(json.dumps(status_payload, indent=2) + "\n", encoding="utf-8")

    if parsed is None:
        (run_dir / "parsed.json").write_text("null\n", encoding="utf-8")
        (parsed_dir / f"{run_id}.json").write_text("null\n", encoding="utf-8")
    else:
        method = f"petclinic_{model}_{row['evidence_condition']}_{row['identifier_condition']}"
        decomposition = proposal_to_decomposition(parsed, method=method, metadata=status_payload)
        body = json.dumps(decomposition, indent=2) + "\n"
        (run_dir / "parsed.json").write_text(body, encoding="utf-8")
        (parsed_dir / f"{run_id}.json").write_text(body, encoding="utf-8")

    row.update(
        {
            "run_status": run_status,
            "execution_status": execution_status,
            "parse_status": parse_status,
            "latency_ms": str(latency_ms),
            "attempt_count": str(attempt_count),
            "execution_timestamp": status_payload["timestamp"],
            "raw_sha256": raw_hash,
        }
    )
    return row


def main() -> int:
    load_dotenv()
    import os

    os.environ.setdefault("SEMS_ENABLE_OLLAMA", "1")
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--models",
        default="",
        help="Comma-separated model keys (default: all). e.g. llama3.1 or gemini-3.8-flash,gpt-4o-mini",
    )
    args = parser.parse_args()
    filter_models = {m.strip() for m in args.models.split(",") if m.strip()}

    rows = list(csv.DictReader(MANIFEST.open(encoding="utf-8")))
    rows.sort(key=lambda r: int(r["execution_order"]))
    out_rows = []
    for row in rows:
        if filter_models and row["model"] not in filter_models:
            out_rows.append(row)
            continue
        meta_path = REPO / row["expected_output_path"] / "metadata.json"
        if meta_path.is_file():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            if meta.get("run_status") in ("VALID", "MODEL_INVALID"):
                row.update({k: str(meta.get(k, "")) for k in ("run_status", "execution_status", "parse_status")})
                out_rows.append(row)
                continue
            if meta.get("execution_status") == "INFRASTRUCTURE_FAILURE":
                pass  # retry
            elif meta.get("execution_status") == "COMPLETED":
                row.update({k: str(meta.get(k, "")) for k in ("run_status", "execution_status", "parse_status")})
                out_rows.append(row)
                continue
        print(f"Executing {row['run_id']} {row['model']} {row['evidence_condition']} {row['identifier_condition']}")
        out_rows.append(run_row(row))

    fieldnames = list(out_rows[0].keys()) if out_rows else []
    for r in out_rows:
        for k in r:
            if k not in fieldnames:
                fieldnames.append(k)
    with MANIFEST.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"Done {len([r for r in out_rows if not filter_models or r['model'] in filter_models])} targeted rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
