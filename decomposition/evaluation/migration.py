from __future__ import annotations

from collections import defaultdict
from typing import Any

from decomposition.evaluation.structural import structural_metrics

SKIP_RANK = {"shared_identity", "uncertain"}
DEFAULT_WEIGHTS = {
    "independence": 0.2,
    "cohesion": 0.2,
    "load": 0.2,
    "data_isolation": 0.2,
    "risk": 0.2,
}


def migration_priority(
    assignment: dict[str, str],
    evidence: dict[str, Any],
    *,
    weights: dict[str, float] | None = None,
) -> list[dict[str, Any]]:
    """Transparent ranking. Weights are configuration, not learned."""
    weights = dict(weights or DEFAULT_WEIGHTS)
    runtime = evidence.get("runtime_interactions") or {}
    if not runtime.get("available"):
        weights["load"] = 0.0
    total_w = sum(abs(value) for key, value in weights.items() if key != "risk") + abs(weights.get("risk", 0))
    if total_w == 0:
        total_w = 1.0
    grouped: dict[str, list[str]] = defaultdict(list)
    for component, service in assignment.items():
        grouped[service].append(component)
    n = max(sum(len(members) for members in grouped.values()), 1)
    load_by_service = _runtime_load(grouped, runtime)
    isolation_by_service = _data_isolation(grouped, evidence)
    structure = structural_metrics(assignment, evidence)
    coupling = float(structure["cross_service_call_ratio"])
    cohesion = float(structure["internal_cohesion_ratio"])
    rows = []
    for service, members in grouped.items():
        if service in SKIP_RANK:
            continue
        independence = _service_independence(service, members, assignment, evidence)
        size_risk = len(members) / n
        score = (
            weights.get("independence", 0) * independence
            + weights.get("cohesion", 0) * cohesion
            + weights.get("load", 0) * load_by_service.get(service, 0.0)
            + weights.get("data_isolation", 0) * isolation_by_service.get(service, 0.0)
            - weights.get("risk", 0) * size_risk
        ) / total_w
        rows.append(
            {
                "service": service,
                "score": round(score, 4),
                "independence": round(independence, 4),
                "cohesion": round(cohesion, 4),
                "load": round(load_by_service.get(service, 0.0), 4),
                "data_isolation": round(isolation_by_service.get(service, 0.0), 4),
                "risk": round(size_risk, 4),
                "size": len(members),
                "global_coupling_used": coupling,
                "load_available": bool(runtime.get("available")),
            }
        )
    rows.sort(key=lambda row: (-row["score"], row["service"]))
    for rank, row in enumerate(rows, start=1):
        row["rank"] = rank
    return rows


def _service_independence(
    service: str,
    members: list[str],
    assignment: dict[str, str],
    evidence: dict[str, Any],
) -> float:
    member_set = set(members)
    internal = 0
    external = 0
    for edge in (evidence.get("dependencies") or {}).get("G_call") or []:
        src, dst = str(edge.get("from") or ""), str(edge.get("to") or "")
        if src not in member_set and dst not in member_set:
            continue
        if src in member_set and dst in member_set:
            internal += 1
        else:
            external += 1
    total = internal + external
    if total == 0:
        return 1.0
    return 1.0 - (external / total)


def _runtime_load(grouped: dict[str, list[str]], runtime: dict[str, Any]) -> dict[str, float]:
    if not runtime.get("available"):
        return {service: 0.0 for service in grouped}
    totals = {service: 0.0 for service in grouped}
    grand = 0.0
    for row in runtime.get("endpoints") or []:
        count = float(row.get("count") or 0)
        if count <= 0:
            continue
        names = set((row.get("components") or {}).keys())
        grand += count
        for service, members in grouped.items():
            if names.intersection(members):
                totals[service] += count
    if grand <= 0:
        return totals
    return {service: value / grand for service, value in totals.items()}


def _data_isolation(grouped: dict[str, list[str]], evidence: dict[str, Any]) -> dict[str, float]:
    sharing = {
        str(row["entity"]): int(row.get("sharing_degree") or 0)
        for row in evidence.get("entity_ownership") or []
        if row.get("entity")
    }
    owned: dict[str, list[str]] = defaultdict(list)
    for row in evidence.get("entity_ownership") or []:
        owner = str(row.get("candidate_owner") or "")
        entity = str(row.get("entity") or "")
        if owner == "UNCERTAIN" or not entity:
            continue
        for service, members in grouped.items():
            if owner in members:
                owned[service].append(entity)
    isolation = {}
    for service in grouped:
        entities = owned.get(service) or []
        if not entities:
            isolation[service] = 1.0
            continue
        shared = sum(1 for entity in entities if sharing.get(entity, 0) > 1)
        isolation[service] = 1.0 - (shared / len(entities))
    return isolation
