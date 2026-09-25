#!/usr/bin/env python3
"""Execute Gemini 3.8 EDU-R RQ3 semantic cohort (12 runs, standard LLM prompts)."""

from __future__ import annotations

import csv
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parents[1]
MANIFEST = BASE / "gemini_38_edur" / "run_manifest_rq3_12.csv"

sys.path.insert(0, str(REPO))
from decomposition.llm.convert import proposal_to_decomposition
from decomposition.llm.prompts import build_prompt
from decomposition.llm.providers import MissingCredentialsError, get_provider
from decomposition.llm.parse import format_validation_error, parse_proposal


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


def main() -> int:
    load_dotenv()
    evidence = json.loads((REPO / "outputs/evidence/architectural_evidence.json").read_text())
    rows = list(csv.DictReader(MANIFEST.open(encoding="utf-8")))
    rows.sort(key=lambda r: int(r["execution_order"]))
    provider = get_provider("gemini")
    model = rows[0]["requested_model_id"]
    temperature = float(rows[0]["temperature"])

    for row in rows:
        run_dir = REPO / row["expected_output_dir"]
        meta_path = run_dir / "metadata.json"
        if meta_path.is_file():
            meta = json.loads(meta_path.read_text())
            if meta.get("parse_ok"):
                continue
        run_dir.mkdir(parents=True, exist_ok=True)
        condition = row["evidence_condition"]
        run_number = int(row["repetition"])
        prompt = build_prompt(condition, evidence)
        (run_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
        print(f"Executing {row['run_id']} {condition} run_{run_number:02d}")
        try:
            raw = provider.generate(prompt, model=model, temperature=temperature)
        except MissingCredentialsError as exc:
            print(exc)
            return 2
        except Exception as exc:
            raw = ""
            error = format_validation_error(exc)
            parse_ok = False
            parsed = None
        else:
            error = None
            try:
                parsed = parse_proposal(raw)
                parse_ok = True
            except Exception as exc:
                parsed = None
                parse_ok = False
                error = format_validation_error(exc)

        (run_dir / "raw_response.txt").write_text(raw, encoding="utf-8")
        run_status = "VALID" if parse_ok else "MODEL_INVALID"
        metadata = {
            "run_id": row["run_id"],
            "cohort": row["cohort"],
            "model": model,
            "provider": "gemini",
            "requested_model_id": model,
            "condition": condition,
            "run_number": run_number,
            "temperature": temperature,
            "timestamp": datetime.now(UTC).isoformat(),
            "parse_ok": parse_ok,
            "run_status": run_status,
            "is_scientific_run": parse_ok,
            "invalid_reason": error or "",
        }
        (run_dir / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        if parsed is None:
            (run_dir / "parsed.json").write_text("null\n", encoding="utf-8")
        else:
            decomp = proposal_to_decomposition(
                parsed, method=f"llm_{model}_{condition}", metadata=metadata
            )
            (run_dir / "parsed.json").write_text(json.dumps(decomp, indent=2) + "\n", encoding="utf-8")

    print(f"Done RQ3 cohort -> {MANIFEST.parent}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
