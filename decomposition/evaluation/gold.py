from __future__ import annotations

import json
from pathlib import Path
from typing import Any

GOLD_FILENAME = "historical_architecture.json"


def load_gold(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("gold file must be a JSON object")
    return payload


def clustering_labels(gold: dict[str, Any]) -> dict[str, str]:
    """Component → service for six-way pairwise evaluation.

    `User` identity components are omitted. ReportBuilder is faculty-adjacent
    per evaluation_notes.legacy_components_in_six_way.
    """
    assignment: dict[str, str] = {}
    for service, payload in (gold.get("services") or {}).items():
        for component in payload.get("components") or []:
            assignment[str(component)] = str(service)
    extra = (gold.get("evaluation_notes") or {}).get("legacy_components_in_six_way") or {}
    for component, service in extra.items():
        assignment[str(component)] = str(service)
    excluded = set(excluded_components(gold))
    return {name: service for name, service in assignment.items() if name not in excluded}


def excluded_components(gold: dict[str, Any]) -> list[str]:
    identity = gold.get("shared_identity") or {}
    if identity.get("excluded_from_six_way_clustering") is False:
        return []
    return [str(name) for name in identity.get("components") or []]


def entity_labels(gold: dict[str, Any]) -> dict[str, str]:
    """Entity → gold owner service. User is omitted."""
    identity = gold.get("shared_identity") or {}
    excluded_entities = {str(name) for name in identity.get("owned_entities") or []}
    labels: dict[str, str] = {}
    for service, payload in (gold.get("services") or {}).items():
        for entity in payload.get("owned_entities") or []:
            if str(entity) not in excluded_entities:
                labels[str(entity)] = str(service)
    return labels
