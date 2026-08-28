from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

import networkx as nx


def structural_metrics(
    assignment: dict[str, str],
    evidence: dict[str, Any],
) -> dict[str, Any]:
    """Architecture-quality metrics. Independent of gold labels."""
    directed = _call_digraph(evidence)
    internal = 0
    cross = 0
    for src, dst in directed.edges:
        left, right = assignment.get(str(src)), assignment.get(str(dst))
        if not left or not right:
            continue
        if left == right:
            internal += 1
        else:
            cross += 1
    total = internal + cross
    sizes = list(Counter(assignment.values()).values())
    return {
        "service_count": len(set(assignment.values())),
        "intra_service_dependencies": internal,
        "inter_service_dependencies": cross,
        "cross_service_call_ratio": round(cross / total, 4) if total else 0.0,
        "internal_cohesion_ratio": round(internal / total, 4) if total else 0.0,
        "cyclic_service_dependencies": _service_cycles(assignment, directed),
        "service_size_distribution": sorted(sizes, reverse=True),
        "modularity": _modularity(assignment, directed),
        "shared_entity_count": _shared_entity_count(evidence),
        "db_multi_owner_count": _multi_owner_count(assignment, evidence),
    }


def inter_service_coupling_ratio(assignment: dict[str, str], evidence: dict[str, Any]) -> float:
    return float(structural_metrics(assignment, evidence)["cross_service_call_ratio"])


def _call_digraph(evidence: dict[str, Any]) -> nx.DiGraph:
    graph = nx.DiGraph()
    for edge in (evidence.get("dependencies") or {}).get("G_call") or []:
        src, dst = edge.get("from"), edge.get("to")
        if src and dst and src != dst:
            graph.add_edge(str(src), str(dst))
    return graph


def _service_cycles(assignment: dict[str, str], graph: nx.DiGraph) -> list[list[str]]:
    service_graph = nx.DiGraph()
    for src, dst in graph.edges:
        left, right = assignment.get(str(src)), assignment.get(str(dst))
        if left and right and left != right:
            service_graph.add_edge(left, right)
    return [sorted(scc) for scc in nx.strongly_connected_components(service_graph) if len(scc) > 1]


def _modularity(assignment: dict[str, str], directed: nx.DiGraph) -> float | None:
    undirected = directed.to_undirected()
    communities: dict[str, set[str]] = defaultdict(set)
    for node, label in assignment.items():
        if node in undirected:
            communities[label].add(node)
    partitions = [members for members in communities.values() if members]
    if not partitions or undirected.number_of_edges() == 0:
        return None
    try:
        return round(float(nx.community.modularity(undirected, partitions)), 4)
    except Exception:
        return None


def _shared_entity_count(evidence: dict[str, Any]) -> int:
    return sum(1 for row in evidence.get("entity_ownership") or [] if int(row.get("sharing_degree") or 0) > 1)


def _multi_owner_count(assignment: dict[str, str], evidence: dict[str, Any]) -> int:
    owners: dict[str, set[str]] = defaultdict(set)
    for row in evidence.get("entity_ownership") or []:
        entity = str(row.get("entity") or "")
        owner = str(row.get("candidate_owner") or "")
        if not entity or owner == "UNCERTAIN":
            continue
        service = assignment.get(owner)
        if service:
            owners[entity].add(service)
    return sum(1 for services in owners.values() if len(services) > 1)
