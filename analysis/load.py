from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_manifest(run_dir: Path) -> dict[str, Any]:
    path = run_dir / "manifest.json"
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def load_run_tables(run_dir: Path) -> dict[str, list[dict[str, str]]]:
    metrics = run_dir / "metrics"
    return {
        "table_a": load_csv(metrics / "table_a.csv"),
        "table_b": load_csv(metrics / "table_b.csv"),
        "table_c": load_csv(metrics / "table_c.csv"),
        "table_d": load_csv(metrics / "table_d.csv"),
    }


def float_or_none(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    return float(value)
