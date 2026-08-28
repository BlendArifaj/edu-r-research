#!/usr/bin/env python3
"""Headless Locust runner for SEMS-R. Writes measured artifacts only."""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from workload.config_loader import load_config  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a SEMS-R Locust workload")
    parser.add_argument("--config", default="smoke", help="YAML name or path under workload/config")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("SEMS_BASE_URL", "http://127.0.0.1:8000"),
        help="Architecture-neutral target. Monolith :8000, gateway :8080.",
    )
    parser.add_argument("--outdir", default="", help="Override artifact directory")
    parser.add_argument(
        "--architecture",
        default="",
        help="monolith or microservices label stored in summary.json",
    )
    return parser.parse_args()


def _parse_locust_stats(stats_csv: Path) -> dict[str, float | int | str]:
    if not stats_csv.exists():
        return {}
    aggregated: dict[str, float | int | str] = {}
    with stats_csv.open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row.get("Name") == "Aggregated":
                aggregated = {
                    "request_count": int(float(row.get("Request Count") or 0)),
                    "failure_count": int(float(row.get("Failure Count") or 0)),
                    "median_ms": float(row.get("Median Response Time") or 0),
                    "p95_ms": float(row.get("95%") or 0),
                    "p99_ms": float(row.get("99%") or 0),
                    "rps": float(row.get("Requests/s") or 0),
                }
                break
    return aggregated


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    stamp = datetime.now(UTC).strftime("%Y-%m-%d_%H%M%S")
    default_out = ROOT / "outputs" / "performance" / f"{stamp}_{config.name}"
    outdir = Path(args.outdir) if args.outdir else default_out
    outdir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["SEMS_WORKLOAD_CONFIG"] = config.name
    env["SEMS_BASE_URL"] = args.base_url
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    csv_prefix = outdir / "locust"
    command = [
        sys.executable,
        "-m",
        "locust",
        "-f",
        str(ROOT / "workload" / "locustfile.py"),
        "--headless",
        "--host",
        args.base_url,
        "-u",
        str(config.users),
        "-r",
        str(config.spawn_rate),
        "-t",
        config.duration,
        "--csv",
        str(csv_prefix),
        "--html",
        str(outdir / "locust_report.html"),
    ]
    completed = subprocess.run(command, cwd=ROOT, env=env, check=False)
    stats = _parse_locust_stats(Path(str(csv_prefix) + "_stats.csv"))
    summary = {
        "integrity": "sems-r-reconstruction-measured",
        "workload_integrity": config.integrity,
        "note": config.note,
        "architecture_target": args.base_url,
        "architecture": args.architecture or "unspecified",
        "config": config.name,
        "users": config.users,
        "spawn_rate": config.spawn_rate,
        "duration": config.duration,
        "mix": config.mix,
        "locust_exit_code": completed.returncode,
        "stats": stats,
        "timestamp": stamp,
    }
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (outdir / "workload.json").write_text(
        json.dumps(
            {
                "name": config.name,
                "mix": config.mix,
                "integrity": config.integrity,
                "host": args.base_url,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote SEMS-R load artifacts to {outdir}")
    print("These are measurements of the experimental reconstruction, not production SEMS.")
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


if __name__ == "__main__":
    main()
