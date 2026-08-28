from __future__ import annotations

import re
from collections import Counter
from typing import Any

from decomposition.baselines.clustering import serialize_decomposition
from decomposition.baselines.config import BaselineConfig
from decomposition.baselines.graphs import call_graph
from decomposition.extraction.static_analysis import _is_component

STOPWORDS = {
    "and",
    "the",
    "for",
    "with",
    "from",
    "into",
    "a",
    "an",
    "of",
    "or",
    "to",
    "in",
    "on",
    "by",
    "is",
    "are",
    "used",
    "based",
}


def run_rule_based(evidence: dict[str, Any], config: BaselineConfig) -> dict[str, Any]:
    """Map components to documented functional areas without gold service labels.

    Priority: area-id substring in the class name, then module path, then
    capability-keyword overlap, then call-graph neighbor majority, then
    identity tokens. Remaining items are reported as uncertain (R9).
    """
    areas = _area_ids(evidence)
    lexicon = _area_lexicon(evidence)
    components = [
        row
        for row in evidence.get("components") or []
        if row.get("name") and _is_component(str(row["name"]))
    ]
    assignment: dict[str, str] = {}
    uncertain: list[dict[str, str]] = []
    reasons: dict[str, str] = {}

    for row in components:
        name = str(row["name"])
        module = str(row.get("module") or "")
        area = _match_area_id(name, areas)
        if area:
            assignment[name] = area
            reasons[name] = "name_contains_functional_area_id"
            continue
        area = _match_area_id(module.replace(".", "_").replace("/", "_"), areas)
        if area:
            assignment[name] = area
            reasons[name] = "module_path_contains_functional_area_id"
            continue
        scored = _keyword_scores(name, lexicon, config)
        if len(scored) == 1:
            assignment[name] = scored[0]
            reasons[name] = "capability_keyword_overlap"
            continue
        if _is_identity(name, module, config):
            assignment[name] = "shared_identity"
            reasons[name] = "identity_token"
            continue

    graph = call_graph(evidence)
    _propagate_neighbors(assignment, reasons, graph, components)

    for row in components:
        name = str(row["name"])
        if name in assignment:
            continue
        if _is_identity(name, str(row.get("module") or ""), config):
            assignment[name] = "shared_identity"
            reasons[name] = "identity_token"
            continue
        assignment[name] = "uncertain"
        reasons[name] = "no_unique_rule_match"
        uncertain.append({"component": name, "reason": reasons[name]})

    notes = [
        "Rule baseline uses domain_description functional areas, module paths, "
        "capability keywords, call-graph neighbors, and identity tokens.",
        "It does not read evaluation gold labels.",
        "Functional-area count comes from domain_description, not from evaluation gold.",
    ]
    return serialize_decomposition(
        method="rule_based",
        evidence=evidence,
        config=config,
        assignment=assignment,
        graph=graph,
        notes=notes[:8],
        available=True,
        uncertain_decisions=uncertain,
    )


def _area_ids(evidence: dict[str, Any]) -> list[str]:
    domain = evidence.get("domain_descriptions") or {}
    return [str(area["id"]).lower() for area in domain.get("functional_areas") or [] if area.get("id")]


def _area_lexicon(evidence: dict[str, Any]) -> dict[str, set[str]]:
    lexicon: dict[str, set[str]] = {}
    domain = evidence.get("domain_descriptions") or {}
    for area in domain.get("functional_areas") or []:
        area_id = str(area.get("id") or "").lower()
        if not area_id:
            continue
        tokens = {area_id}
        for capability in area.get("capabilities") or []:
            tokens.update(_words(str(capability)))
        lexicon[area_id] = tokens
    return lexicon


def _match_area_id(text: str, areas: list[str]) -> str | None:
    lowered = text.lower()
    hits = [area for area in areas if area in lowered]
    if not hits:
        return None
    hits.sort(key=len, reverse=True)
    return hits[0]


def _keyword_scores(name: str, lexicon: dict[str, set[str]], config: BaselineConfig) -> list[str]:
    tokens = {token for token in _camel_tokens(name) if token not in config.drop_suffixes}
    scores: dict[str, int] = {}
    for area, vocab in lexicon.items():
        overlap = len(tokens & vocab)
        if overlap:
            scores[area] = overlap
    if not scores:
        return []
    best = max(scores.values())
    return sorted(area for area, score in scores.items() if score == best)


def _is_identity(name: str, module: str, config: BaselineConfig) -> bool:
    tokens = set(_camel_tokens(name)) | set(_words(module.replace(".", " ").replace("_", " ")))
    return any(token in tokens for token in config.identity_tokens)


def _propagate_neighbors(
    assignment: dict[str, str],
    reasons: dict[str, str],
    graph: Any,
    components: list[dict[str, Any]],
) -> None:
    pending = [str(row["name"]) for row in components if str(row["name"]) not in assignment]
    changed = True
    while changed and pending:
        changed = False
        remaining = []
        for name in pending:
            votes = Counter()
            if name in graph:
                for neighbor in graph.neighbors(name):
                    area = assignment.get(str(neighbor))
                    if area and area not in {"uncertain", "shared_identity"}:
                        votes[area] += 1
            if len(votes) == 1:
                assignment[name] = next(iter(votes))
                reasons[name] = "call_graph_neighbor_majority"
                changed = True
            elif votes:
                top = votes.most_common()
                if len(top) == 1 or top[0][1] > top[1][1]:
                    assignment[name] = top[0][0]
                    reasons[name] = "call_graph_neighbor_majority"
                    changed = True
                else:
                    remaining.append(name)
            else:
                remaining.append(name)
        pending = remaining


def _camel_tokens(name: str) -> list[str]:
    parts = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|$)", name)
    return [part.lower() for part in parts if part]


def _words(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if token not in STOPWORDS and len(token) >= 3
    }
