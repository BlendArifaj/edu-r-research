from __future__ import annotations

from typing import Any

from decomposition.llm import CONDITIONS

SCHEMA_INSTRUCTIONS = """
Return ONLY a JSON object with this shape (no markdown, no commentary):
{
  "services": [
    {
      "name": "candidate-service",
      "components": ["ComponentName"],
      "owned_entities": ["EntityName"],
      "responsibilities": ["..."],
      "dependencies": ["other-service"],
      "rationale": "evidence-based reason"
    }
  ],
  "migration_priority": [
    {"service": "candidate-service", "rank": 1, "confidence": 0.0, "reason": ""}
  ],
  "uncertain_decisions": [],
  "unsupported_assumptions": [],
  "rule_violations": [],
  "architectural_risks": [],
  "critique": "",
  "revised": false
}
Every listed component must appear in exactly one service.
Use UNCERTAIN in uncertain_decisions when evidence is insufficient.
Do not invent runtime measurements.
Do not use a hidden labeled historical service assignment.
SEMS-R is a reconstruction, not original production SEMS source.
""".strip()


def build_prompt(condition: str, evidence: dict[str, Any]) -> str:
    if condition not in CONDITIONS:
        raise ValueError(f"unknown condition: {condition}")
    sections = [_preamble(), _task(), SCHEMA_INSTRUCTIONS, _c0_body(evidence)]
    if condition >= "C1":
        sections.append(_c1_body(evidence))
    if condition >= "C2":
        sections.append(_c2_body(evidence))
    if condition == "C3":
        sections.append(_c3_body())
    return "\n\n".join(sections) + "\n"


def _preamble() -> str:
    return (
        "You are a software architect proposing a microservice decomposition "
        "of SEMS-R (SEMS Experimental Reconstruction). This system is a controlled "
        "reconstruction of documented education-management functional areas. "
        "It is not the original production SEMS source code."
    )


def _task() -> str:
    return (
        "Propose independently deployable services by grouping the listed "
        "application components (services, repositories, and legacy utilities). "
        "Reason only from the information in this prompt."
    )


def _c0_body(evidence: dict[str, Any]) -> str:
    domain = evidence.get("domain_descriptions") or {}
    system = domain.get("system") or evidence.get("system") or {}
    lines = [
        "## C0 High-level system description",
        system.get("description") or "",
        "",
        "### Functional areas (documented capabilities, not a labeled assignment of classes)",
    ]
    for area in domain.get("functional_areas") or []:
        caps = "; ".join(area.get("capabilities") or [])
        lines.append(f"- {area.get('id')}: {caps}")
    lines += ["", "### Known cross-domain dependencies (narrative)"]
    for item in domain.get("known_cross_domain_dependencies") or []:
        lines.append(f"- {item}")
    lines += ["", "### Components"]
    for row in evidence.get("components") or []:
        lines.append(f"- {row.get('name')} [{row.get('kind')}] module={row.get('module')}")
    return "\n".join(lines)


def _c1_body(evidence: dict[str, Any]) -> str:
    lines = [
        "## C1 Structured architectural evidence",
        "The following is extracted from SEMS-R source and measured traces.",
        "Runtime values are SEMS-R measurements, not production SEMS traffic.",
        "",
        "### Call dependencies (from → to)",
    ]
    for edge in (evidence.get("dependencies") or {}).get("G_call") or []:
        lines.append(f"- {edge.get('from')} -> {edge.get('to')}")
    lines += ["", "### Entity ownership candidates (argmax of static access; ties UNCERTAIN)"]
    for row in evidence.get("entity_ownership") or []:
        lines.append(
            f"- {row.get('entity')} table={row.get('table')} "
            f"sharing={row.get('sharing_degree')} candidate_owner={row.get('candidate_owner')} "
            f"accessors={','.join(row.get('accessing_components') or [])}"
        )
    lines += ["", "### Component × entity static usage"]
    for row in evidence.get("database_usage") or []:
        flags = []
        if row.get("static_direct"):
            flags.append("direct")
        if row.get("static_via_repository"):
            flags.append("via_repo")
        lines.append(f"- {row.get('component')} uses {row.get('entity')} ({'|'.join(flags) or 'static'})")
    runtime = evidence.get("runtime_interactions") or {}
    lines += ["", "### Runtime interactions"]
    if not runtime.get("available"):
        lines.append("No measured traces. Runtime section left empty rather than fabricated.")
    else:
        lines.append(runtime.get("note") or "Measured SEMS-R traces.")
        lines.append(f"trace_count={runtime.get('trace_count')}")
        lines.append("Busiest endpoints:")
        for row in (runtime.get("endpoints") or [])[:15]:
            lines.append(
                f"- {row.get('endpoint')} n={row.get('count')} "
                f"sql_mean={row.get('sql_query_mean')}"
            )
    return "\n".join(lines)


def _c2_body(evidence: dict[str, Any]) -> str:
    rules = evidence.get("migration_constraints") or {}
    lines = [
        "## C2 Explicit migration constraints",
        "These rules do not encode a class-to-service gold mapping.",
    ]
    for rule in rules.get("rules") or []:
        lines.append(f"- {rule.get('id')}: {rule.get('statement')}")
    checkable = rules.get("machine_checkable") or []
    if checkable:
        lines.append("Machine-checkable: " + ", ".join(checkable))
    return "\n".join(lines)


def _c3_body() -> str:
    return """## C3 Self-critique protocol
1. Propose an architecture in the JSON schema.
2. Critique your own boundaries in the critique field.
3. List unsupported assumptions.
4. List high-risk cross-service dependencies in architectural_risks.
5. Put decisions that are not justified by evidence in uncertain_decisions (use UNCERTAIN).
6. If the critique exposes a serious problem, revise the services list and set revised=true.
The JSON object you return must be the revised architecture when a revision is needed."""
