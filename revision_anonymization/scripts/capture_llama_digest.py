#!/usr/bin/env python3
"""Capture frozen Ollama Llama 3.1 artifact digest (no LLM experiment calls)."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "llama_digest_frozen.txt"
MODEL = "llama3.1"
TAG = "latest"


def main() -> int:
    list_out = subprocess.check_output(["ollama", "list"], text=True)
    show_out = subprocess.check_output(["ollama", "show", f"{MODEL}:{TAG}"], text=True)
    digest = ""
    for line in list_out.splitlines():
        if "llama3.1" not in line:
            continue
        parts = line.split()
        # NAME ID SIZE ... — ID is second token when name is first
        if len(parts) >= 2:
            digest = parts[1]
            break
    payload = {
        "frozen_at_utc": datetime.now(UTC).isoformat(),
        "model_name": MODEL,
        "model_tag": TAG,
        "model_ref": f"{MODEL}:{TAG}",
        "digest": digest,
        "ollama_list_excerpt": [ln for ln in list_out.splitlines() if "llama3.1" in ln],
        "ollama_show": show_out,
        "abort_if_digest_changes": True,
    }
    lines = [
        "# Frozen Llama artifact — do not edit after execution starts",
        f"frozen_at_utc: {payload['frozen_at_utc']}",
        f"model_name: {MODEL}",
        f"model_tag: {TAG}",
        f"model_ref: {MODEL}:{TAG}",
        f"digest: {digest}",
        "",
        "## ollama list (llama3.1 row)",
        *[ln for ln in payload["ollama_list_excerpt"]],
        "",
        "## ollama show",
        show_out.strip(),
        "",
        "## machine-readable",
        json.dumps(payload, indent=2),
    ]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} digest={digest}")
    return 0 if digest else 1


if __name__ == "__main__":
    raise SystemExit(main())
