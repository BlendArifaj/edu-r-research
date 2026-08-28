from __future__ import annotations

from collections import Counter
from typing import Any

from decomposition.evaluation.gold import clustering_labels, entity_labels, excluded_components
from decomposition.evaluation.migration import DEFAULT_WEIGHTS, migration_priority
from decomposition.evaluation.pairwise import (
    adjusted_rand_index,
    normalized_mutual_information,
    pairwise_scores,
)
from decomposition.evaluation.rules import rule_compliance
from decomposition.evaluation.stability import stability
from decomposition.evaluation.structural import structural_metrics


def evaluate_decomposition(
    decomposition: dict[str, Any],
    gold: dict[str, Any],
    evidence: dict[str, Any],
    *,
    imbalance_max_share: float = 0.5,
    migration_weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    if not decomposition.get("available", True):
        return {
            "method": decomposition.get("method"),
            "available": False,
            "note": "Decomposition unavailable; scores left empty rather than fabricated.",
        }
    gold_components = clustering_labels(gold)
    predicted = {
        name: str(label)
        for name, label in (decomposition.get("component_assignment") or {}).items()
    }
    predicted_eval = {name: predicted.get(name, f"__unassigned_{name}") for name in gold_components}
    pair = pairwise_scores(gold_components, predicted_eval)
    structure = structural_metrics(predicted, evidence)
    compliance = rule_compliance(
        predicted,
        evidence,
        expected_components=list(gold_components),
        services=decomposition.get("services") or [],
        imbalance_max_share=imbalance_max_share,
    )
    entity_gold = entity_labels(gold)
    db_conflicts = _entity_owner_conflicts(entity_gold, gold_components, predicted, evidence)
    ranks = migration_priority(predicted, evidence, weights=migration_weights or DEFAULT_WEIGHTS)
    return {
        "method": decomposition.get("method"),
        "available": True,
        "gold_labels_used": True,
        "excluded_from_clustering": excluded_components(gold),
        "n_services": structure["service_count"],
        "n_eval_components": len(gold_components),
        "pairwise": pair,
        "ari": round(adjusted_rand_index(gold_components, predicted_eval), 4),
        "nmi": round(normalized_mutual_information(gold_components, predicted_eval), 4),
        "cross_service_coupling": structure["cross_service_call_ratio"],
        "internal_cohesion_ratio": structure["internal_cohesion_ratio"],
        "db_ownership_conflicts": db_conflicts,
        "db_multi_owner_count": structure["db_multi_owner_count"],
        "cycles": structure["cyclic_service_dependencies"],
        "n_cycle_groups": len(structure["cyclic_service_dependencies"]),
        "modularity": structure["modularity"],
        "service_size_distribution": structure["service_size_distribution"],
        "rule_compliance": compliance["rule_compliance"],
        "rule_details": compliance,
        "migration_priority": ranks,
        "stability": stability([predicted]),
        "uncertain_decisions": len(decomposition.get("uncertain_decisions") or []),
    }


def _entity_owner_conflicts(
    entity_gold: dict[str, str],
    gold_components: dict[str, str],
    predicted: dict[str, str],
    evidence: dict[str, Any],
) -> int:
    modal: dict[str, str] = {}
    by_service: dict[str, list[str]] = {}
    for component, service in gold_components.items():
        by_service.setdefault(service, []).append(predicted.get(component, f"__missing_{component}"))
    for service, labels in by_service.items():
        modal[service] = Counter(labels).most_common(1)[0][0]
    owners = {
        str(row["entity"]): str(row.get("candidate_owner") or "UNCERTAIN")
        for row in evidence.get("entity_ownership") or []
        if row.get("entity")
    }
    conflicts = 0
    for entity, gold_service in entity_gold.items():
        owner = owners.get(entity, "UNCERTAIN")
        if owner == "UNCERTAIN":
            conflicts += 1
            continue
        pred = predicted.get(owner)
        if pred != modal.get(gold_service):
            conflicts += 1
    return conflicts
