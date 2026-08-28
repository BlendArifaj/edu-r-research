"""Load measured Phase 10 comparison CSVs. Never invent latency or RPS."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from analysis.load import load_csv

REPO_ROOT = Path(__file__).resolve().parents[1]
CATALOG = Path(__file__).resolve().parent / "phase10_artifacts.yaml"
LOAD_FIELDS = (
    "architecture",
    "config",
    "users",
    "duration",
    "request_count",
    "failure_count",
    "median_ms",
    "p95_ms",
    "p99_ms",
    "rps",
)


def load_catalog(path: Path | None = None) -> list[dict[str, Any]]:
    raw = yaml.safe_load((path or CATALOG).read_text(encoding="utf-8"))
    items = (raw or {}).get("comparisons") or []
    return [item for item in items if isinstance(item, dict)]


def load_phase10_rows(
    repo_root: Path | None = None,
    catalog_path: Path | None = None,
) -> list[dict[str, str]]:
    root = repo_root or REPO_ROOT
    rows: list[dict[str, str]] = []
    for item in load_catalog(catalog_path):
        stamp = str(item.get("stamp") or "")
        csv_path = root / "outputs" / "performance" / "comparisons" / stamp / "comparison.csv"
        if not csv_path.is_file():
            continue
        for raw in load_csv(csv_path):
            row = {key: str(raw.get(key) or "") for key in LOAD_FIELDS}
            row["mode"] = str(item.get("mode") or "")
            row["stamp"] = stamp
            row["equal_total"] = "true" if item.get("equal_total") else "false"
            row["budget"] = str(item.get("budget") or "")
            rows.append(row)
    return rows


def comparison_dirs(rows: list[dict[str, str]], repo_root: Path | None = None) -> list[Path]:
    root = repo_root or REPO_ROOT
    seen: list[Path] = []
    for stamp in dict.fromkeys(row["stamp"] for row in rows):
        path = root / "outputs" / "performance" / "comparisons" / stamp
        if path.is_dir():
            seen.append(path)
    return seen
