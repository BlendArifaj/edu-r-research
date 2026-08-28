from __future__ import annotations

import argparse
import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from decomposition.extraction.call_graph import (
    build_graphs,
    cycles_as_sccs,
    graph_metrics,
    serialize_edges,
)
from decomposition.extraction.database_analysis import build_database_matrix, entity_ownership
from decomposition.extraction.runtime_analysis import analyze_runtime, load_traces
from decomposition.extraction.static_analysis import analyze_app

FORBIDDEN_GOLD = "historical_architecture"


def build_evidence_package(
    app_root: Path,
    traces_path: Path | None,
    domain_path: Path,
    rules_path: Path,
) -> dict[str, Any]:
    if FORBIDDEN_GOLD in str(app_root) or (traces_path and FORBIDDEN_GOLD in str(traces_path)):
        raise RuntimeError("refusing path that looks like evaluation gold")
    static = analyze_app(app_root)
    graphs = build_graphs(static)
    traces = load_traces(traces_path)
    runtime = analyze_runtime(traces)
    matrix = build_database_matrix(static, runtime.get("component_entity_counts"))
    ownership = entity_ownership(matrix)
    call_metrics = graph_metrics(graphs["G_call"])
    metrics_by_name = {row["component"]: row for row in call_metrics}
    components = []
    for cls in static.classes:
        if not cls["is_component"]:
            continue
        kind = "legacy"
        if cls["name"].endswith("Service"):
            kind = "service"
        elif cls["name"].endswith("Repository"):
            kind = "repository"
        components.append(
            {
                "name": cls["name"],
                "module": cls["module"],
                "file": cls["file"],
                "kind": kind,
                "metrics": metrics_by_name.get(cls["name"], {}),
            }
        )
    domain = json.loads(domain_path.read_text(encoding="utf-8"))
    rules = json.loads(rules_path.read_text(encoding="utf-8"))
    return {
        "system": {
            "name": "SEMS-R",
            "full_name": "SEMS Experimental Reconstruction",
            "is_original_sems_source": False,
            "integrity": (
                "Controlled reconstruction based on documented SEMS functional areas. "
                "Not original production SEMS source. Runtime values are measured SEMS-R traces."
            ),
            "generated_at": datetime.now(UTC).isoformat(),
            "app_root": str(app_root),
            "traces_path": str(traces_path) if traces_path else None,
            "evidence_sources": {
                "static_ast": True,
                "database_static": True,
                "runtime_traces": bool(runtime.get("available")),
                "historical_gold_labels": False,
            },
        },
        "components": components,
        "dependencies": {
            "module_imports": static.module_imports,
            "G_code": serialize_edges(graphs["G_code"], "module_import"),
            "G_call": serialize_edges(graphs["G_call"], "call"),
            "G_data": serialize_edges(graphs["G_data"], "entity_mention"),
            "resolved_calls": static.calls,
            "call_cycles": cycles_as_sccs(graphs["G_call"]),
            "module_cycles": cycles_as_sccs(graphs["G_code"]),
        },
        "database_usage": matrix,
        "entity_ownership": ownership,
        "runtime_interactions": runtime,
        "domain_descriptions": domain,
        "migration_constraints": rules,
        "endpoints": static.endpoints,
        "component_metrics": call_metrics,
        "orm_tablenames": static.tablenames,
    }


def write_package(package: dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "architectural_evidence.json"
    json_path.write_text(json.dumps(package, indent=2) + "\n", encoding="utf-8")
    (out_dir / "architectural_evidence.md").write_text(_to_markdown(package), encoding="utf-8")
    _write_csv(
        out_dir / "component_metrics.csv",
        package["component_metrics"],
        [
            "component",
            "fan_in",
            "fan_out",
            "afferent_coupling",
            "efferent_coupling",
            "dependency_degree",
            "betweenness_centrality",
            "pagerank",
            "internal_dependency_ratio",
            "external_dependency_ratio",
            "cohesion_proxy",
        ],
    )
    _write_csv(
        out_dir / "database_usage.csv",
        package["database_usage"],
        [
            "component",
            "entity",
            "table",
            "static_direct",
            "static_via_repository",
            "runtime_cooccurrence_count",
        ],
    )
    _write_csv(
        out_dir / "entity_ownership.csv",
        package["entity_ownership"],
        [
            "entity",
            "table",
            "sharing_degree",
            "candidate_owner",
            "accessing_components",
        ],
        transform=lambda row: {
            **row,
            "accessing_components": "|".join(row.get("accessing_components") or []),
        },
    )
    _write_csv(
        out_dir / "call_dependencies.csv",
        package["dependencies"]["G_call"],
        ["from", "to", "kind"],
    )
    runtime_endpoints = package["runtime_interactions"].get("endpoints") or []
    _write_csv(
        out_dir / "runtime_endpoints.csv",
        runtime_endpoints,
        ["endpoint", "count", "sql_query_mean", "duration_ms_mean", "status_counts"],
        transform=lambda row: {**row, "status_counts": json.dumps(row.get("status_counts") or {})},
    )


def _write_csv(
    path: Path,
    rows: list[dict[str, Any]],
    fieldnames: list[str],
    transform=None,
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            payload = transform(row) if transform else row
            writer.writerow({key: payload.get(key, "") for key in fieldnames})


def _to_markdown(package: dict[str, Any]) -> str:
    system = package["system"]
    runtime = package["runtime_interactions"]
    lines = [
        "# SEMS-R architectural evidence",
        "",
        system["integrity"],
        "",
        f"- Generated: `{system['generated_at']}`",
        f"- Original SEMS source: `{system['is_original_sems_source']}`",
        f"- Runtime traces used: `{system['evidence_sources']['runtime_traces']}`",
        f"- Historical gold labels used: `{system['evidence_sources']['historical_gold_labels']}`",
        "",
        "## Components",
        "",
        f"{len(package['components'])} service/repository/legacy components were extracted from AST.",
        "",
        "## Call-graph cycles (SCC)",
        "",
    ]
    cycles = package["dependencies"]["call_cycles"]
    if cycles:
        for cycle in cycles:
            lines.append(f"- `{' -> '.join(cycle)}`")
    else:
        lines.append("- None detected.")
    lines += ["", "## Shared data (highest sharing degree)", ""]
    shared = sorted(
        package["entity_ownership"], key=lambda row: row["sharing_degree"], reverse=True
    )
    for row in shared[:15]:
        lines.append(
            f"- **{row['entity']}** (`{row['table']}`): sharing={row['sharing_degree']}, "
            f"candidate_owner={row['candidate_owner']}, "
            f"components={', '.join(row['accessing_components'])}"
        )
    lines += ["", "## Runtime (measured, not fabricated)", ""]
    if not runtime.get("available"):
        lines.append(runtime.get("note", "No traces."))
    else:
        lines.append(runtime.get("note", ""))
        lines.append(
            "- Runtime component×entity counts are request-level co-occurrence "
            "(component appeared on the same request as a queried table), "
            "applied only where a static access edge already exists."
        )
        lines.append(f"- Trace count: {runtime['trace_count']}")
        lines.append(f"- HTTP status counts: `{runtime.get('status_counts')}`")
        lines.append("")
        lines.append("### Busiest endpoints")
        for row in (runtime.get("endpoints") or [])[:12]:
            lines.append(
                f"- `{row['endpoint']}` n={row['count']} "
                f"sql_mean={row['sql_query_mean']} duration_ms_mean={row['duration_ms_mean']}"
            )
    lines += [
        "",
        "## Migration constraints included",
        "",
        "Rules R1–R9 are included as constraints. They do not encode a six-service mapping.",
        "",
        "## Domain descriptions included",
        "",
        "High-level documented functional areas only. Not evaluation gold labels.",
        "",
    ]
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract SEMS-R architectural evidence")
    parser.add_argument("--app-root", default="monolith/app")
    parser.add_argument("--traces", default="outputs/evidence/runtime_traces.jsonl")
    parser.add_argument("--domain", default="reference/domain_description.json")
    parser.add_argument("--rules", default="reference/migration_rules.json")
    parser.add_argument("--out", default="outputs/evidence")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    traces = Path(args.traces)
    package = build_evidence_package(
        app_root=Path(args.app_root),
        traces_path=traces if traces.exists() else None,
        domain_path=Path(args.domain),
        rules_path=Path(args.rules),
    )
    write_package(package, Path(args.out))
    print(f"Wrote evidence package to {args.out}")
    print("This package does not include historical gold service assignments.")


if __name__ == "__main__":
    main()
