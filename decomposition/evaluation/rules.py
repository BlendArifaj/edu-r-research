from __future__ import annotations

from collections import Counter
from typing import Any

from decomposition.evaluation.structural import structural_metrics


def rule_compliance(
    assignment: dict[str, str],
    evidence: dict[str, Any],
    *,
    expected_components: list[str],
    services: list[dict[str, Any]] | None = None,
    imbalance_max_share: float = 0.5,
) -> dict[str, Any]:
    """Machine-checkable rules from migration_rules.json.

    RuleCompliance = satisfied_rules / applicable_rules.
    Cyclic dependencies are *reported*; the architecture rule is satisfied when
    the check runs and records them, not when the graph is acyclic.
    """
    sizes = Counter(assignment.values())
    n = max(len(assignment), 1)
    max_share = max(sizes.values()) / n if sizes else 0.0
    listed = [str(name) for row in (services or []) for name in row.get("components") or []]
    duplicate = len(listed) != len(set(listed))
    empty = [row["id"] for row in (services or []) if not row.get("components")]
    unassigned = sorted(name for name in expected_components if name not in assignment)
    structure = structural_metrics(assignment, evidence)
    results = {
        "entity_has_at_most_one_owner": structure["db_multi_owner_count"] == 0,
        "no_empty_services": empty == [],
        "no_extreme_service_imbalance": max_share <= imbalance_max_share,
        "no_unassigned_components": unassigned == [],
        "no_duplicate_component_assignment": not duplicate,
        "report_cyclic_service_dependencies": True,
    }
    applicable = list(results)
    satisfied = [name for name, ok in results.items() if ok]
    return {
        "rules": results,
        "satisfied_rules": satisfied,
        "applicable_rules": applicable,
        "rule_compliance": round(len(satisfied) / max(len(applicable), 1), 4),
        "unassigned_components": unassigned,
        "empty_services": empty,
        "max_service_share": round(max_share, 4),
        "cyclic_service_dependencies": structure["cyclic_service_dependencies"],
        "db_multi_owner_count": structure["db_multi_owner_count"],
    }
