from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

import networkx as nx

from decomposition.baselines.config import BaselineConfig
from decomposition.extraction.static_analysis import _is_component


def cluster_graph(
    graph: nx.Graph,
    config: BaselineConfig,
    *,
    method: str,
    evidence: dict[str, Any],
    notes: list[str] | None = None,
) -> dict[str, Any]:
    communities = _louvain_partition(graph, config)
    assignment = _assignment_from_communities(communities)
    return serialize_decomposition(
        method=method,
        evidence=evidence,
        config=config,
        assignment=assignment,
        graph=graph,
        notes=notes or [],
        available=True,
    )


def _louvain_partition(graph: nx.Graph, config: BaselineConfig) -> list[set[str]]:
    if graph.number_of_nodes() == 0:
        return []
    if graph.number_of_edges() == 0:
        return [{node} for node in sorted(graph.nodes)]
    raw = nx.community.louvain_communities(
        graph,
        weight="weight",
        resolution=config.louvain_resolution,
        seed=config.seed,
    )
    communities = [set(map(str, group)) for group in raw]
    covered = {node for group in communities for node in group}
    for node in graph.nodes:
        if str(node) not in covered:
            communities.append({str(node)})
    return _sorted_communities(communities)


def _sorted_communities(communities: list[set[str]]) -> list[set[str]]:
    return sorted(communities, key=lambda group: (-len(group), min(group) if group else ""))


def _assignment_from_communities(communities: list[set[str]]) -> dict[str, str]:
    assignment: dict[str, str] = {}
    for index, group in enumerate(communities):
        label = f"community_{index:02d}"
        for name in sorted(group):
            assignment[name] = label
    return assignment


def serialize_decomposition(
    *,
    method: str,
    evidence: dict[str, Any],
    config: BaselineConfig,
    assignment: dict[str, str],
    graph: nx.Graph | None,
    notes: list[str],
    available: bool,
    uncertain_decisions: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    system = evidence.get("system") or {}
    owned = _entities_by_component(assignment, evidence.get("entity_ownership") or [])
    services = _services_from_assignment(assignment, owned)
    unassigned = _unassigned(evidence, assignment) if available else []
    stats = _graph_stats(graph, assignment) if graph is not None else {}
    return {
        "schema_version": "1",
        "method": method,
        "method_family": "deterministic_baseline",
        "system": {
            "name": system.get("name", "SEMS-R"),
            "is_original_sems_source": False,
            "gold_labels_used": False,
            "integrity": (
                "SEMS-R reconstruction baselines. Not original production SEMS. "
                "This output does not consume evaluation gold labels."
            ),
            "generated_at": datetime.now(UTC).isoformat(),
        },
        "config": config.as_dict(),
        "available": available,
        "component_assignment": dict(sorted(assignment.items())),
        "services": services,
        "unassigned_components": unassigned,
        "uncertain_decisions": uncertain_decisions or [],
        "uncertain_entities": [
            str(row["entity"])
            for row in evidence.get("entity_ownership") or []
            if row.get("candidate_owner") == "UNCERTAIN"
        ],
        "graph_stats": stats,
        "checks": structural_checks(assignment, services, unassigned, evidence),
        "notes": notes,
    }


def unavailable_result(
    method: str,
    evidence: dict[str, Any],
    config: BaselineConfig,
    reason: str,
) -> dict[str, Any]:
    payload = serialize_decomposition(
        method=method,
        evidence=evidence,
        config=config,
        assignment={},
        graph=None,
        notes=[reason],
        available=False,
    )
    payload["services"] = []
    return payload


def structural_checks(
    assignment: dict[str, str],
    services: list[dict[str, Any]],
    unassigned: list[str],
    evidence: dict[str, Any],
) -> dict[str, Any]:
    empty = [row["id"] for row in services if not row["components"]]
    return {
        "no_duplicate_component_assignment": len(assignment) == len(set(assignment)),
        "no_empty_services": empty == [],
        "no_unassigned_components": unassigned == [],
        "cyclic_service_dependencies": _service_cycles(assignment, evidence),
        "empty_services": empty,
    }


def _services_from_assignment(
    assignment: dict[str, str],
    owned: dict[str, list[str]],
) -> list[dict[str, Any]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for component, service in assignment.items():
        grouped[service].append(component)
    services = []
    for service_id, components in sorted(grouped.items(), key=lambda item: item[0]):
        services.append(
            {
                "id": service_id,
                "label": service_id,
                "components": sorted(components),
                "owned_entities": owned.get(service_id, []),
            }
        )
    return services


def _entities_by_component(
    assignment: dict[str, str],
    ownership: list[dict[str, Any]],
) -> dict[str, list[str]]:
    owned: dict[str, list[str]] = defaultdict(list)
    for row in ownership:
        entity = str(row.get("entity") or "")
        owner = str(row.get("candidate_owner") or "")
        if not entity or owner == "UNCERTAIN":
            continue
        service = assignment.get(owner)
        if service:
            owned[service].append(entity)
    return {key: sorted(values) for key, values in owned.items()}


def _unassigned(evidence: dict[str, Any], assignment: dict[str, str]) -> list[str]:
    names = [
        str(row["name"])
        for row in evidence.get("components") or []
        if row.get("name") and _is_component(str(row["name"]))
    ]
    return sorted({name for name in names if name not in assignment})


def _graph_stats(graph: nx.Graph, assignment: dict[str, str]) -> dict[str, Any]:
    communities = defaultdict(set)
    for node, label in assignment.items():
        communities[label].add(node)
    partitions = list(communities.values())
    modularity = None
    if graph.number_of_edges() and partitions:
        try:
            modularity = round(float(nx.community.modularity(graph, partitions, weight="weight")), 4)
        except Exception:
            modularity = None
    return {
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "communities": len(partitions),
        "modularity": modularity,
        "algorithm": "louvain",
    }


def _service_cycles(assignment: dict[str, str], evidence: dict[str, Any]) -> list[list[str]]:
    service_graph = nx.DiGraph()
    for edge in (evidence.get("dependencies") or {}).get("G_call") or []:
        left = assignment.get(str(edge.get("from") or ""))
        right = assignment.get(str(edge.get("to") or ""))
        if left and right and left != right:
            service_graph.add_edge(left, right)
    cycles = []
    for scc in nx.strongly_connected_components(service_graph):
        if len(scc) > 1:
            cycles.append(sorted(scc))
    return cycles
