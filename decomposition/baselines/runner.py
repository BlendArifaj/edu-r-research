from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from decomposition.baselines.clustering import cluster_graph, unavailable_result
from decomposition.baselines.config import BaselineConfig, load_config
from decomposition.baselines.graphs import call_graph, combine_graphs, component_names, data_graph, runtime_graph
from decomposition.baselines.rule_based import run_rule_based
from decomposition.extraction.evidence_builder import FORBIDDEN_GOLD


def run_all_baselines(
    evidence: dict[str, Any],
    config: BaselineConfig,
) -> dict[str, dict[str, Any]]:
    if (evidence.get("system") or {}).get("evidence_sources", {}).get("historical_gold_labels"):
        raise RuntimeError("evidence package contains evaluation gold; refusing to run baselines")
    names = component_names(evidence)
    static_call = call_graph(evidence)
    static_data = data_graph(evidence)
    runtime = runtime_graph(evidence)
    combined = combine_graphs(
        [(static_call, config.alpha), (static_data, config.beta), (runtime, config.gamma)],
        names,
        normalize_layers=config.normalize_layers,
    )
    results = {
        "rule_based": run_rule_based(evidence, config),
        "graph_static": cluster_graph(
            static_call,
            config,
            method="graph_static",
            evidence=evidence,
            notes=["Louvain on undirected G_call. Community count is not fixed to six."],
        ),
        "static_only": cluster_graph(
            combine_graphs(
                [(static_call, 1.0), (static_data, 1.0)],
                names,
                normalize_layers=config.normalize_layers,
            ),
            config,
            method="static_only",
            evidence=evidence,
            notes=["Louvain on static call + static data-sharing edges."],
        ),
    }
    if runtime is None:
        results["runtime_only"] = unavailable_result(
            "runtime_only",
            evidence,
            config,
            "No measured runtime traces. Runtime baseline left empty rather than fabricated.",
        )
    else:
        results["runtime_only"] = cluster_graph(
            runtime,
            config,
            method="runtime_only",
            evidence=evidence,
            notes=[
                "Louvain on cosine component co-occurrence from measured endpoints.",
                "Not production SEMS traffic.",
            ],
        )
    results["combined_graph"] = cluster_graph(
        combined,
        config,
        method="combined_graph",
        evidence=evidence,
        notes=[
            f"w = {config.alpha}*call + {config.beta}*data + {config.gamma}*runtime "
            "after per-layer max-normalization.",
            "Weights are configuration, not fit on evaluation gold.",
        ],
    )
    return results


def write_results(results: dict[str, dict[str, Any]], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []
    for method, payload in results.items():
        (out_dir / f"{method}.json").write_text(
            json.dumps(payload, indent=2) + "\n", encoding="utf-8"
        )
        for component, service in (payload.get("component_assignment") or {}).items():
            rows.append({"method": method, "component": component, "service": service})
    _write_csv(out_dir / "assignments.csv", rows, ["method", "component", "service"])
    (out_dir / "summary.md").write_text(_summary_markdown(results), encoding="utf-8")


def load_evidence(path: Path) -> dict[str, Any]:
    if FORBIDDEN_GOLD in str(path):
        raise RuntimeError("refusing path that looks like evaluation gold")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("evidence package must be a JSON object")
    return payload


def run_from_paths(evidence_path: Path, out_dir: Path, config_path: Path | None) -> dict[str, dict[str, Any]]:
    evidence = load_evidence(evidence_path)
    config = load_config(config_path)
    results = run_all_baselines(evidence, config)
    write_results(results, out_dir)
    return results


def _write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _summary_markdown(results: dict[str, dict[str, Any]]) -> str:
    lines = [
        "# SEMS-R deterministic baselines",
        "",
        "Controlled reconstruction. Not original production SEMS. Gold labels were not used.",
        "",
        "| Method | Available | # services | # assigned | Uncertain components | Modularity |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for method, payload in results.items():
        stats = payload.get("graph_stats") or {}
        uncertain = len(payload.get("uncertain_decisions") or [])
        lines.append(
            f"| `{method}` | {payload.get('available')} | {len(payload.get('services') or [])} | "
            f"{len(payload.get('component_assignment') or {})} | {uncertain} | "
            f"{stats.get('modularity', '')} |"
        )
    lines += [
        "",
        "## Notes",
        "",
        "- Louvain community count is discovered, not set to six from the reference architecture.",
        "- Combined-graph weights default to alpha=beta=gamma=1.0 and are not gold-tuned.",
        "- Runtime-only is empty when traces are missing.",
        "",
    ]
    return "\n".join(lines) + "\n"
