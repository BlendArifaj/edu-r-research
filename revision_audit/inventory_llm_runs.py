#!/usr/bin/env python3
"""Inventory all LLM run directories under outputs/runs/. Read-only."""

from __future__ import annotations

import csv
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RUNS = REPO / "outputs" / "runs"
OUT = Path(__file__).resolve().parent / "original_llm_runs.csv"


def main() -> None:
    rows: list[dict[str, str]] = []
    for meta_path in sorted(RUNS.glob("*/decompositions/*/*/run_*/metadata.json")):
        run_dir = meta_path.parent
        snapshot = meta_path.parts[meta_path.parts.index("runs") + 1]
        rel = run_dir.relative_to(REPO / "outputs" / "runs" / snapshot / "decompositions")
        model = rel.parts[0]
        condition = rel.parts[1]
        run_folder = run_dir.name
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        parsed_path = run_dir / "parsed.json"
        raw_path = run_dir / "raw_response.txt"
        prompt_path = run_dir / "prompt.txt"
        parsed = None
        parse_status = "missing_file"
        available = ""
        if parsed_path.is_file():
            text = parsed_path.read_text(encoding="utf-8").strip()
            if text == "null" or text == "":
                parse_status = "null_json"
                available = "false"
            else:
                try:
                    parsed = json.loads(text)
                    parse_status = "ok" if meta.get("parse_ok") else "parsed_but_flagged"
                    available = str(bool(parsed and parsed.get("available")))
                except json.JSONDecodeError:
                    parse_status = "invalid_json"
        evidence_in_prompt = "outputs/runs" in (prompt_path.read_text(encoding="utf-8")[:200] if prompt_path.is_file() else "")
        rows.append(
            {
                "snapshot_id": snapshot,
                "model": model,
                "condition": condition,
                "run_folder": run_folder,
                "run_number": str(meta.get("run_number") or ""),
                "provider": str(meta.get("provider") or ""),
                "temperature": str(meta.get("temperature") or ""),
                "is_scientific_run": str(meta.get("is_scientific_run") or ""),
                "parse_ok": str(meta.get("parse_ok") or ""),
                "parse_status": parse_status,
                "available": available,
                "retries_used": str(meta.get("retries_used") or ""),
                "error": str(meta.get("error") or ""),
                "timestamp": str(meta.get("timestamp") or ""),
                "prompt_path": str(prompt_path.relative_to(REPO)),
                "raw_response_path": str(raw_path.relative_to(REPO)) if raw_path.is_file() else "",
                "parsed_path": str(parsed_path.relative_to(REPO)),
                "method": str((parsed or {}).get("method") or "") if parsed else "",
            }
        )

    fields = list(rows[0].keys()) if rows else []
    with OUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    scientific = [r for r in rows if r.get("is_scientific_run") == "True"]
    print(f"Total metadata.json: {len(rows)}")
    print(f"is_scientific_run=True: {len(scientific)}")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
