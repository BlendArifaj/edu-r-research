from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def load_traces(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def analyze_runtime(traces: list[dict[str, Any]]) -> dict[str, Any]:
    if not traces:
        return {
            "available": False,
            "trace_count": 0,
            "note": (
                "No runtime traces found. Section left empty rather than fabricated. "
                "component_entity_counts are request-level co-occurrence, not per-query access."
            ),
            "status_counts": {},
            "endpoints": [],
            "component_entity_counts": {},
            "interactions": [],
        }
    status_counts = Counter(int(row.get("status_code") or 0) for row in traces)
    by_endpoint: dict[str, dict[str, Any]] = {}
    component_entity: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    interactions: list[dict[str, Any]] = []
    for row in traces:
        endpoint = str(row.get("endpoint") or "")
        bucket = by_endpoint.setdefault(
            endpoint,
            {
                "endpoint": endpoint,
                "count": 0,
                "sql_query_total": 0,
                "duration_ms_total": 0.0,
                "status_counts": Counter(),
                "components": Counter(),
                "entities": Counter(),
            },
        )
        bucket["count"] += 1
        bucket["sql_query_total"] += int(row.get("sql_query_count") or 0)
        bucket["duration_ms_total"] += float(row.get("duration_ms") or 0)
        bucket["status_counts"][int(row.get("status_code") or 0)] += 1
        components = list(row.get("components") or [])
        entities = list(row.get("database_entities") or [])
        for component in components:
            bucket["components"][component] += 1
            for entity in entities:
                component_entity[component][entity] += 1
        for entity in entities:
            bucket["entities"][entity] += 1
        interactions.append(
            {
                "request_id": row.get("request_id"),
                "endpoint": endpoint,
                "status_code": row.get("status_code"),
                "duration_ms": row.get("duration_ms"),
                "components": components,
                "database_entities": entities,
                "sql_query_count": row.get("sql_query_count"),
            }
        )
    endpoints = []
    for bucket in by_endpoint.values():
        count = max(int(bucket["count"]), 1)
        endpoints.append(
            {
                "endpoint": bucket["endpoint"],
                "count": bucket["count"],
                "sql_query_mean": round(bucket["sql_query_total"] / count, 3),
                "duration_ms_mean": round(bucket["duration_ms_total"] / count, 3),
                "status_counts": dict(bucket["status_counts"]),
                "components": dict(bucket["components"]),
                "entities": dict(bucket["entities"]),
            }
        )
    endpoints.sort(key=lambda item: item["count"], reverse=True)
    return {
        "available": True,
        "trace_count": len(traces),
        "integrity": "sems-r-reconstruction-measured",
        "note": (
            "Measured SEMS-R traces. Not production SEMS traffic. "
            "component_entity_counts are request-level co-occurrence "
            "(component on the same request as a queried table), not per-query attribution."
        ),
        "status_counts": dict(status_counts),
        "endpoints": endpoints,
        "component_entity_counts": {k: dict(v) for k, v in component_entity.items()},
        "interactions_sample": interactions[:50],
        "interaction_count": len(interactions),
    }
