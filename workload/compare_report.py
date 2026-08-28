"""Write Mode A comparison tables from measured Locust summaries. Never invent stats."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

STAT_KEYS = ("request_count", "failure_count", "median_ms", "p95_ms", "p99_ms", "rps")
ARCH_RANK = {"monolith": 0, "clustered": 1, "microservices": 2}


def paired_architecture(runs: list[dict[str, Any]]) -> str:
    names = {str(row["architecture"]) for row in runs}
    names.discard("monolith")
    names.discard("")
    if "clustered" in names:
        return "clustered"
    if "microservices" in names:
        return "microservices"
    if len(names) == 1:
        return next(iter(names))
    return "microservices"


def load_summary(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def collect_runs(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for summary_path in sorted(root.glob("*/*/summary.json")):
        payload = load_summary(summary_path)
        stats = payload.get("stats") or {}
        rows.append(
            {
                "architecture": payload.get("architecture") or summary_path.parents[1].name,
                "config": payload.get("config") or summary_path.parent.name,
                "users": payload.get("users"),
                "duration": payload.get("duration"),
                "request_count": stats.get("request_count"),
                "failure_count": stats.get("failure_count"),
                "median_ms": stats.get("median_ms"),
                "p95_ms": stats.get("p95_ms"),
                "p99_ms": stats.get("p99_ms"),
                "rps": stats.get("rps"),
                "locust_exit_code": payload.get("locust_exit_code"),
                "artifact_dir": str(summary_path.parent),
            }
        )
    arch_rank = ARCH_RANK
    config_rank = {"smoke": 0, "low": 1, "medium": 2, "high": 3, "very_high": 4}
    rows.sort(
        key=lambda row: (
            arch_rank.get(str(row["architecture"]), 9),
            config_rank.get(str(row["config"]), 9),
            str(row["config"]),
        )
    )
    return rows


def delta_rows(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key = {(row["architecture"], row["config"]): row for row in runs}
    config_rank = {"smoke": 0, "low": 1, "medium": 2, "high": 3, "very_high": 4}
    configs = sorted({row["config"] for row in runs}, key=lambda name: (config_rank.get(str(name), 9), str(name)))
    other = paired_architecture(runs)
    deltas: list[dict[str, Any]] = []
    for config in configs:
        mono = by_key.get(("monolith", config))
        peer = by_key.get((other, config))
        if mono is None or peer is None:
            continue
        row: dict[str, Any] = {"config": config, "delta": f"{other}_minus_monolith"}
        for key in STAT_KEYS:
            left, right = peer.get(key), mono.get(key)
            if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                row[key] = left - right
            else:
                row[key] = None
        deltas.append(row)
    return deltas


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_markdown(
    path: Path,
    runs: list[dict[str, Any]],
    deltas: list[dict[str, Any]],
    *,
    mode: str = "A",
) -> None:
    header = (
        "| architecture | config | users | duration | requests | failures "
        "| median_ms | p95_ms | p99_ms | rps |"
    )
    if mode == "C":
        budget_line = (
            "Mode C is nginx plus declared replicas. Totals are not equal. "
            "Locust ran on the host (outside the container budget)."
        )
    elif mode == "D":
        budget_line = (
            "Mode D is monolith 2 GB vs microservices 16 GB. Totals are not equal. "
            "Locust ran on the host (outside the container budget)."
        )
    elif mode == "B":
        budget_line = (
            "Mode B is selective extra CPU/RAM. Totals are not equal. "
            "Locust ran on the host (outside the container budget)."
        )
    elif mode == "E":
        budget_line = (
            "Mode E is a dependency-clustered campus plus library at equal 4 CPU / 4 GB. "
            "Not the historical six-service gold. "
            "Locust ran on the host (outside the container budget)."
        )
    else:
        budget_line = (
            "Locust ran on the host (outside the 4 CPU / 4 GB container budget)."
        )
    lines = [
        f"# SEMS-R Mode {mode} load comparison",
        "",
        "Measured reconstruction traffic. Not production SEMS.",
        budget_line,
        "",
        "## Per architecture",
        "",
        header,
        "| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    run_keys = (
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
    for row in runs:
        cells = " | ".join(_fmt(row.get(key)) for key in run_keys)
        lines.append(f"| {cells} |")
    pair = paired_architecture(runs)
    lines += [
        "",
        f"## Delta ({pair} − monolith)",
        "",
        "| config | requests | failures | median_ms | p95_ms | p99_ms | rps |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    delta_keys = (
        "config",
        "request_count",
        "failure_count",
        "median_ms",
        "p95_ms",
        "p99_ms",
        "rps",
    )
    for row in deltas:
        cells = " | ".join(_fmt(row.get(key)) for key in delta_keys)
        lines.append(f"| {cells} |")
    lines += [
        "",
        "Positive p95/median means the non-monolith path was slower.",
        "Positive rps means it completed more requests per second.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_p95_svg(path: Path, runs: list[dict[str, Any]], *, mode: str = "A") -> None:
    configs = sorted({row["config"] for row in runs})
    pair = paired_architecture(runs)
    architectures = ("monolith", pair)
    series = {
        architecture: [
            next(
                (
                    float(row["p95_ms"])
                    for row in runs
                    if row["architecture"] == architecture and row["config"] == config
                    and isinstance(row.get("p95_ms"), (int, float))
                ),
                0.0,
            )
            for config in configs
        ]
        for architecture in architectures
    }
    ymax = max([value for values in series.values() for value in values] + [1.0])
    width, height = 720, 360
    left, top, right, bottom = 72, 48, 24, 72
    plot_w, plot_h = width - left - right, height - top - bottom
    colors = {"monolith": "#334155", "microservices": "#0f766e", "clustered": "#0f766e"}
    n = max(len(configs), 1)
    group_w = plot_w / n
    bar_w = group_w * 0.35
    parts: list[str] = []
    for index, config in enumerate(configs):
        for series_index, architecture in enumerate(architectures):
            value = series[architecture][index]
            h = plot_h * (value / ymax)
            x = left + index * group_w + 0.1 * group_w + series_index * bar_w
            y = top + plot_h - h
            fill = colors.get(architecture, "#0f766e")
            parts.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" '
                f'height="{h:.1f}" fill="{fill}"/>'
            )
        cx = left + index * group_w + group_w / 2
        parts.append(
            f'<text x="{cx:.1f}" y="{height - 24}" '
            f'text-anchor="middle" font-size="12">{config}</text>'
        )
    parts.append(
        f'<text x="{width / 2:.1f}" y="28" text-anchor="middle" font-size="14">'
        f"Mode {mode} p95 latency (ms) — SEMS-R reconstruction</text>"
    )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
        f'<rect width="100%" height="100%" fill="#fff"/>'
        f'<rect x="{left}" y="{top}" width="{plot_w}" height="{plot_h}" '
        'fill="none" stroke="#cbd5e1"/>'
        + "".join(parts)
        + "</svg>\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")


def write_comparison(root: Path) -> dict[str, list[dict[str, Any]]]:
    mode = "A"
    plan_path = root / "plan.json"
    if plan_path.is_file():
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        mode = str(plan.get("mode") or "A")
    runs = collect_runs(root)
    deltas = delta_rows(runs)
    run_fields = [
        "architecture", "config", "users", "duration", "request_count", "failure_count",
        "median_ms", "p95_ms", "p99_ms", "rps", "locust_exit_code", "artifact_dir",
    ]
    write_csv(root / "comparison.csv", runs, run_fields)
    write_csv(
        root / "comparison_delta.csv",
        deltas,
        ["config", "delta", *STAT_KEYS],
    )
    write_markdown(root / "comparison.md", runs, deltas, mode=mode)
    write_p95_svg(root / "p95.svg", runs, mode=mode)
    return {"runs": runs, "deltas": deltas}


def _fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.4f}".rstrip("0").rstrip(".")
    return str(value)
