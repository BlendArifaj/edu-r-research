from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from decomposition.llm.schema import DecompositionProposal


def proposal_to_decomposition(
    proposal: DecompositionProposal,
    *,
    method: str,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    assignment: dict[str, str] = {}
    services = []
    duplicates: list[str] = []
    for service in proposal.services:
        label = service.name.strip() or "unnamed"
        for component in service.components:
            if component in assignment:
                duplicates.append(component)
            assignment[component] = label
        services.append(
            {
                "id": label,
                "label": label,
                "components": list(service.components),
                "owned_entities": list(service.owned_entities),
            }
        )
    return {
        "schema_version": "1",
        "method": method,
        "method_family": "llm",
        "system": {
            "name": "SEMS-R",
            "is_original_sems_source": False,
            "gold_labels_used": False,
            "integrity": (
                "SEMS-R LLM decomposition. Not original production SEMS. "
                "This output does not consume evaluation gold labels."
            ),
            "generated_at": datetime.now(UTC).isoformat(),
        },
        "config": {
            "provider": metadata.get("provider"),
            "model": metadata.get("model"),
            "temperature": metadata.get("temperature"),
            "condition": metadata.get("condition"),
            "run_number": metadata.get("run_number"),
            "is_scientific_run": metadata.get("is_scientific_run", False),
        },
        "available": True,
        "component_assignment": dict(sorted(assignment.items())),
        "services": services,
        "uncertain_decisions": [
            {"component": item, "reason": item} if not isinstance(item, dict) else item
            for item in proposal.uncertain_decisions
        ],
        "unsupported_assumptions": proposal.unsupported_assumptions,
        "rule_violations": proposal.rule_violations + (
            [f"duplicate assignment: {name}" for name in duplicates]
        ),
        "architectural_risks": proposal.architectural_risks,
        "critique": proposal.critique,
        "revised": proposal.revised,
        "migration_priority": [item.model_dump() for item in proposal.migration_priority],
        "notes": ["Parsed from LLM JSON. Gold labels were not in the prompt."],
    }
