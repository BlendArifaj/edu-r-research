from __future__ import annotations

from collections import defaultdict
from itertools import combinations
from typing import Any

import networkx as nx

from decomposition.extraction.static_analysis import _is_component


def component_names(evidence: dict[str, Any]) -> list[str]:
    names = [str(row["name"]) for row in evidence.get("components") or [] if row.get("name")]
    return sorted({name for name in names if _is_component(name)})


def call_graph(evidence: dict[str, Any]) -> nx.Graph:
    graph = _empty_graph(evidence)
    for edge in (evidence.get("dependencies") or {}).get("G_call") or []:
        src, dst = edge.get("from"), edge.get("to")
        if src and dst and src != dst:
            _add_weight(graph, str(src), str(dst), 1.0)
    return graph


def data_graph(evidence: dict[str, Any]) -> nx.Graph:
    """Undirected edges between components that statically share an entity.

    Weight is 1/sharing_degree so highly shared tables do not form a hairball.
    """
    graph = _empty_graph(evidence)
    by_entity: dict[str, set[str]] = defaultdict(set)
    for row in evidence.get("database_usage") or []:
        component = str(row.get("component") or "")
        entity = str(row.get("entity") or "")
        if not component or not entity or not _is_component(component):
            continue
        if row.get("static_direct") or row.get("static_via_repository"):
            by_entity[entity].add(component)
    sharing = {
        str(row["entity"]): max(int(row.get("sharing_degree") or 1), 1)
        for row in evidence.get("entity_ownership") or []
        if row.get("entity")
    }
    for entity, members in by_entity.items():
        if len(members) < 2:
            continue
        degree = float(sharing.get(entity, len(members)))
        weight = 1.0 / degree
        for src, dst in combinations(sorted(members), 2):
            _add_weight(graph, src, dst, weight)
    return graph


def runtime_graph(evidence: dict[str, Any]) -> nx.Graph | None:
    """Cosine co-occurrence of components on the same measured request/endpoint.

    Returns None when traces are absent so callers can skip rather than fabricate.
    """
    runtime = evidence.get("runtime_interactions") or {}
    if not runtime.get("available"):
        return None
    endpoints = runtime.get("endpoints") or []
    if not endpoints:
        return None
    graph = _empty_graph(evidence)
    pair_counts: dict[tuple[str, str], float] = defaultdict(float)
    freq: dict[str, float] = defaultdict(float)
    for row in endpoints:
        count = float(row.get("count") or 0)
        if count <= 0:
            continue
        raw = row.get("components") or {}
        names = sorted({name for name in raw if _is_component(str(name))})
        for name in names:
            freq[name] += count
        for src, dst in combinations(names, 2):
            pair_counts[(src, dst)] += count
    for (src, dst), cooccur in pair_counts.items():
        denom = (freq[src] * freq[dst]) ** 0.5
        if denom <= 0:
            continue
        _add_weight(graph, src, dst, cooccur / denom)
    return graph


def combine_graphs(
    layers: list[tuple[nx.Graph | None, float]],
    nodes: list[str],
    *,
    normalize_layers: bool = True,
) -> nx.Graph:
    combined = nx.Graph()
    combined.add_nodes_from(nodes)
    for graph, weight in layers:
        if graph is None or weight == 0:
            continue
        layer = normalize_graph(graph) if normalize_layers else graph
        for src, dst, data in layer.edges(data=True):
            _add_weight(combined, src, dst, weight * float(data.get("weight") or 0.0))
    return combined


def normalize_graph(graph: nx.Graph) -> nx.Graph:
    scaled = nx.Graph()
    scaled.add_nodes_from(graph.nodes)
    if graph.number_of_edges() == 0:
        return scaled
    peak = max(float(data.get("weight") or 0.0) for _, _, data in graph.edges(data=True))
    if peak <= 0:
        return scaled
    for src, dst, data in graph.edges(data=True):
        scaled.add_edge(src, dst, weight=float(data.get("weight") or 0.0) / peak)
    return scaled


def _empty_graph(evidence: dict[str, Any]) -> nx.Graph:
    graph = nx.Graph()
    graph.add_nodes_from(component_names(evidence))
    return graph


def _add_weight(graph: nx.Graph, src: str, dst: str, weight: float) -> None:
    if src == dst or weight <= 0:
        return
    graph.add_node(src)
    graph.add_node(dst)
    if graph.has_edge(src, dst):
        graph[src][dst]["weight"] = float(graph[src][dst].get("weight") or 0.0) + weight
    else:
        graph.add_edge(src, dst, weight=weight)
