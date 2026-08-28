from __future__ import annotations

from typing import Any

import networkx as nx

from decomposition.extraction.static_analysis import StaticEvidence, _is_component


def build_graphs(static: StaticEvidence) -> dict[str, nx.DiGraph]:
    g_code = nx.DiGraph()
    for edge in static.module_imports:
        src = edge["from_module"]
        dst = edge["imported_module"]
        if dst.startswith("app.") and src != dst:
            g_code.add_edge(src, dst)

    g_call = nx.DiGraph()
    for edge in static.calls:
        src, dst = edge["from_component"], edge["to_component"]
        if src != dst and _is_component(src) and _is_component(dst):
            g_call.add_edge(src, dst)

    g_data = nx.DiGraph()
    for mention in static.entity_mentions:
        g_data.add_edge(mention["component"], mention["entity"])
    return {"G_code": g_code, "G_call": g_call, "G_data": g_data}


def _pagerank(graph: nx.DiGraph, alpha: float = 0.85, iterations: int = 40) -> dict[str, float]:
    """Power-iteration PageRank. Avoids NetworkX's SciPy backend requirement."""
    nodes = list(graph.nodes)
    count = len(nodes)
    if count == 0:
        return {}
    rank = {node: 1.0 / count for node in nodes}
    for _ in range(iterations):
        dangling = sum(rank[node] for node in nodes if graph.out_degree(node) == 0)
        nxt = {node: (1.0 - alpha) / count + alpha * dangling / count for node in nodes}
        for node in nodes:
            degree = graph.out_degree(node)
            if degree == 0:
                continue
            contribution = alpha * rank[node] / degree
            for successor in graph.successors(node):
                nxt[successor] += contribution
        rank = nxt
    return rank


def graph_metrics(graph: nx.DiGraph) -> list[dict[str, Any]]:
    if graph.number_of_nodes() == 0:
        return []
    betweenness = nx.betweenness_centrality(graph)
    pagerank = _pagerank(graph) if graph.number_of_edges() else {n: 0.0 for n in graph}
    rows = []
    for node in graph.nodes:
        fan_in = int(graph.in_degree(node))
        fan_out = int(graph.out_degree(node))
        internal = 0
        external = 0
        for pred in graph.predecessors(node):
            if graph.has_edge(node, pred) or pred == node:
                internal += 1
            else:
                external += 1
        for succ in graph.successors(node):
            if not graph.has_edge(succ, node):
                external += 1
        total = max(internal + external, 1)
        rows.append(
            {
                "component": node,
                "fan_in": fan_in,
                "fan_out": fan_out,
                "afferent_coupling": fan_in,
                "efferent_coupling": fan_out,
                "dependency_degree": fan_in + fan_out,
                "betweenness_centrality": round(float(betweenness.get(node, 0.0)), 6),
                "pagerank": round(float(pagerank.get(node, 0.0)), 6),
                "internal_dependency_ratio": round(internal / total, 4),
                "external_dependency_ratio": round(external / total, 4),
                "cohesion_proxy": round(1.0 - (external / total), 4),
            }
        )
    return sorted(rows, key=lambda row: row["pagerank"], reverse=True)


def cycles_as_sccs(graph: nx.DiGraph) -> list[list[str]]:
    cycles = []
    for scc in nx.strongly_connected_components(graph):
        if len(scc) > 1:
            cycles.append(sorted(scc))
        elif len(scc) == 1:
            node = next(iter(scc))
            if graph.has_edge(node, node):
                cycles.append([node])
    return cycles


def serialize_edges(graph: nx.DiGraph, kind: str) -> list[dict[str, str]]:
    return [{"from": u, "to": v, "kind": kind} for u, v in graph.edges]
