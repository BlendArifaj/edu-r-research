from __future__ import annotations

from collections import defaultdict
from typing import Any

from decomposition.extraction.static_analysis import StaticEvidence, _is_component


def build_database_matrix(
    static: StaticEvidence,
    runtime_entity_counts: dict[str, dict[str, int]] | None = None,
) -> list[dict[str, Any]]:
    """Component × entity usage. Runtime counts are measured; 0 if no traces."""
    runtime_entity_counts = runtime_entity_counts or {}
    repo_entities: dict[str, set[str]] = defaultdict(set)
    direct: dict[str, set[str]] = defaultdict(set)
    for mention in static.entity_mentions:
        component, entity = mention["component"], mention["entity"]
        if not _is_component(component):
            continue
        direct[component].add(entity)
        if component.endswith("Repository"):
            repo_entities[component].add(entity)

    via_repo: dict[str, set[str]] = defaultdict(set)
    for call in static.calls:
        src, dst = call["from_component"], call["to_component"]
        if not _is_component(src):
            continue
        if dst in repo_entities:
            via_repo[src].update(repo_entities[dst])

    components = sorted(
        {row["name"] for row in static.classes if row["is_component"]}
        | {name for name in direct if _is_component(name)}
        | {name for name in via_repo if _is_component(name)}
    )
    entities = sorted(set(static.tablenames) | {e for used in via_repo.values() for e in used})
    rows: list[dict[str, Any]] = []
    for component in components:
        for entity in entities:
            static_direct = entity in direct[component]
            static_via = entity in via_repo[component]
            if not static_direct and not static_via:
                continue
            table = static.tablenames.get(entity, _guess_table(entity))
            runtime = int(runtime_entity_counts.get(component, {}).get(table, 0))
            runtime += int(runtime_entity_counts.get(component, {}).get(entity, 0))
            rows.append(
                {
                    "component": component,
                    "entity": entity,
                    "table": table,
                    "static_direct": static_direct,
                    "static_via_repository": static_via,
                    "runtime_cooccurrence_count": runtime,
                }
            )
    return rows


def entity_ownership(matrix: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Candidate owner = component with max combined access. Ties are UNCERTAIN.

    This does not use the historical six-service assignment.
    """
    by_entity: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in matrix:
        by_entity[row["entity"]].append(row)
    results = []
    for entity, rows in sorted(by_entity.items()):
        components = {row["component"] for row in rows}
        scores: dict[str, float] = defaultdict(float)
        for row in rows:
            score = 1.0 if row["static_direct"] else 0.0
            score += 0.5 if row["static_via_repository"] else 0.0
            # Runtime is request-level co-occurrence on an existing static edge,
            # not SQL-to-component attribution. Used only as a volume tie-breaker.
            score += min(int(row.get("runtime_cooccurrence_count") or 0), 1000) / 1000.0
            scores[row["component"]] += score
        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        top_score = ranked[0][1] if ranked else 0.0
        tied = [name for name, score in ranked if abs(score - top_score) < 1e-9]
        owner = tied[0] if len(tied) == 1 else "UNCERTAIN"
        results.append(
            {
                "entity": entity,
                "table": rows[0]["table"],
                "sharing_degree": len(components),
                "candidate_owner": owner,
                "tied_components": tied if len(tied) > 1 else [],
                "accessing_components": sorted(components),
                "data_coupling": round(len(components) / max(len({r["component"] for r in matrix}), 1), 4),
            }
        )
    return results


def _guess_table(entity: str) -> str:
    if entity.endswith("y"):
        return entity[:-1].lower() + "ies"
    if entity.endswith("s"):
        return entity.lower()
    return entity.lower() + "s"
