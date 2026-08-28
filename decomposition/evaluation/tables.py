from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


TABLE_A_FIELDS = [
    "method",
    "n_services",
    "pairwise_precision",
    "pairwise_recall",
    "pairwise_f1",
    "ari",
    "nmi",
    "cross_service_coupling",
    "db_ownership_conflicts",
    "cycles",
]

TABLE_B_FIELDS = [
    "model",
    "condition",
    "n_runs",
    "pairwise_f1",
    "rule_compliance",
    "stability",
    "uncertain_decisions",
    "unsupported_assumptions",
]
TABLE_C_FIELDS = [
    "evidence",
    "method",
    "pairwise_f1",
    "modularity",
    "cross_service_coupling",
]

TABLE_D_FIELDS = [
    "service",
    "rule_based_rank",
    "llm_rank",
    "expert_rank",
    "historical_rank",
]


def table_a_rows(scores: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for payload in scores:
        if not payload.get("available"):
            continue
        pair = payload.get("pairwise") or {}
        rows.append(
            {
                "method": payload.get("method"),
                "n_services": payload.get("n_services"),
                "pairwise_precision": pair.get("precision"),
                "pairwise_recall": pair.get("recall"),
                "pairwise_f1": pair.get("f1"),
                "ari": payload.get("ari"),
                "nmi": payload.get("nmi"),
                "cross_service_coupling": payload.get("cross_service_coupling"),
                "db_ownership_conflicts": payload.get("db_ownership_conflicts"),
                "cycles": payload.get("n_cycle_groups"),
            }
        )
    return rows


def table_b_rows(aggregates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for payload in aggregates:
        rows.append(
            {
                "model": payload.get("model"),
                "condition": payload.get("condition"),
                "n_runs": payload.get("n_runs"),
                "pairwise_f1": payload.get("pairwise_f1"),
                "rule_compliance": payload.get("rule_compliance"),
                "stability": payload.get("stability"),
                "uncertain_decisions": payload.get("uncertain_decisions"),
                "unsupported_assumptions": payload.get("unsupported_assumptions"),
            }
        )
    return rows


def table_c_rows(scores: list[dict[str, Any]]) -> list[dict[str, Any]]:
    evidence_map = {
        "graph_static": "static_call",
        "static_only": "static_call_plus_data",
        "runtime_only": "runtime",
        "combined_graph": "static_plus_runtime",
    }
    rows = []
    for payload in scores:
        method = str(payload.get("method") or "")
        if method not in evidence_map or not payload.get("available"):
            continue
        rows.append(
            {
                "evidence": evidence_map[method],
                "method": method,
                "pairwise_f1": (payload.get("pairwise") or {}).get("f1"),
                "modularity": payload.get("modularity"),
                "cross_service_coupling": payload.get("cross_service_coupling"),
            }
        )
    return rows


def table_d_rows(scores: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rule = next((row for row in scores if row.get("method") == "rule_based" and row.get("available")), None)
    if not rule:
        return []
    rows = []
    for item in rule.get("migration_priority") or []:
        rows.append(
            {
                "service": item.get("service"),
                "rule_based_rank": item.get("rank"),
                "llm_rank": "",
                "expert_rank": "",
                "historical_rank": "",
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def markdown_table(rows: list[dict[str, Any]], fieldnames: list[str], title: str) -> str:
    lines = [f"# {title}", ""]
    lines.append("| " + " | ".join(fieldnames) + " |")
    lines.append("| " + " | ".join("---" for _ in fieldnames) + " |")
    for row in rows:
        lines.append("| " + " | ".join(_cell(row.get(key)) for key in fieldnames) + " |")
    lines += [
        "",
        "SEMS-R reconstruction. Pairwise scores exclude shared identity (`AuthService`, `UserRepository`).",
        "Expert and historical migration ranks are blank until data exist; they are not fabricated.",
        "",
    ]
    return "\n".join(lines)


def _cell(value: Any) -> str:
    if value is None:
        return ""
    return str(value)
