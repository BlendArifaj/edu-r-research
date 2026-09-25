#!/usr/bin/env python3
"""PETCLINIC_EXT_V1 design freeze — inventory, mapping, evidence, prompts, manifest."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BASE = REPO / "external_validation_petclinic"
MONO = BASE / "repos" / "monolith"
MICRO = BASE / "repos" / "microservices"
DOMAIN_FILE = BASE / "DOMAIN_DESCRIPTION.txt"

SERVICE_DIRS = {
    "CUSTOMERS": MICRO / "spring-petclinic-customers-service/src/main/java",
    "VETS": MICRO / "spring-petclinic-vets-service/src/main/java",
    "VISITS": MICRO / "spring-petclinic-visits-service/src/main/java",
}

EXCLUDE_SIMPLE = {
    "package-info",
    "PetClinicApplication",
    "PetClinicRuntimeHints",
}
EXCLUDE_PREFIXES = ("system.",)
EXCLUDE_SUFFIXES = ("Formatter",)  # web formatters
EXCLUDE_MODEL_BASE = {"BaseEntity", "Person", "NamedEntity"}

KIND_RULES = (
    ("Controller", "controller"),
    ("Repository", "repository"),
    ("Validator", "validator"),
    ("Resource", "controller"),
)


def git_info(path: Path) -> dict:
    return {
        "sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=path, text=True).strip(),
        "branch": subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=path, text=True
        ).strip(),
        "date": subprocess.check_output(
            ["git", "log", "-1", "--format=%cI"], cwd=path, text=True
        ).strip(),
        "subject": subprocess.check_output(
            ["git", "log", "-1", "--format=%s"], cwd=path, text=True
        ).strip(),
        "status": subprocess.check_output(["git", "status", "--porcelain"], cwd=path, text=True).strip()
        or "clean",
    }


def monolith_java_files() -> list[Path]:
    root = MONO / "src/main/java"
    return sorted(p for p in root.rglob("*.java") if "src/test" not in str(p))


def micro_simple_index() -> dict[str, list[tuple[str, Path]]]:
    idx: dict[str, list[tuple[str, Path]]] = {}
    for svc, root in SERVICE_DIRS.items():
        if not root.is_dir():
            continue
        for p in root.rglob("*.java"):
            if "/test/" in str(p):
                continue
            idx.setdefault(p.stem, []).append((svc, p))
    return idx


def classify_kind(name: str) -> str:
    for suf, kind in KIND_RULES:
        if name.endswith(suf):
            return kind
    if name.endswith("Repository"):
        return "repository"
    return "domain"


def should_exclude(qualified: str, simple: str, rel: str) -> str | None:
    if simple in EXCLUDE_SIMPLE:
        return "bootstrap_or_package_info"
    if simple in EXCLUDE_MODEL_BASE:
        return "shared_model_base_ambiguous"
    for pref in EXCLUDE_PREFIXES:
        if pref in qualified:
            return "infrastructure_system_package"
    for suf in EXCLUDE_SUFFIXES:
        if simple.endswith(suf):
            return "ui_formatter_utility"
    if simple == "CrashController":
        return "demo_infrastructure"
    if simple.endswith("Configuration") or simple.endswith("Config"):
        return "framework_configuration"
    return None


def map_component(
    simple: str, qualified: str, pkg: str, micro_idx: dict, source_path: Path
) -> dict | None:
    # RULE 1: unique simple name match in exactly one business microservice
    hits = micro_idx.get(simple, [])
    hits = [(s, p) for s, p in hits if s in SERVICE_DIRS]
    if len(hits) == 1:
        svc, ref = hits[0]
        return {
            "reference_service": svc,
            "mapping_rule": "RULE_1_UNIQUE_SIMPLE_NAME",
            "reference_artifact": ref.name,
            "reference_path": str(ref.relative_to(MICRO)),
            "mapping_confidence": "HIGH",
        }
    if len(hits) > 1:
        return None  # ambiguous

    # RULE 2a: Controller -> Resource in same service domain
    ctrl_map = {
        "VetController": ("VETS", "VetResource", "RULE_2_CONTROLLER_TO_RESOURCE"),
        "OwnerController": ("CUSTOMERS", "OwnerResource", "RULE_2_CONTROLLER_TO_RESOURCE"),
        "PetController": ("CUSTOMERS", "PetResource", "RULE_2_CONTROLLER_TO_RESOURCE"),
        "VisitController": ("VISITS", "VisitResource", "RULE_2_CONTROLLER_TO_RESOURCE"),
    }
    if simple in ctrl_map:
        svc, res_name, rule = ctrl_map[simple]
        ref_path = next(
            (p for s, p in micro_idx.get(res_name, []) if s == svc),
            None,
        )
        if ref_path:
            return {
                "reference_service": svc,
                "mapping_rule": rule,
                "reference_artifact": res_name,
                "reference_path": str(ref_path.relative_to(MICRO)),
                "mapping_confidence": "HIGH",
            }

    # RULE 2b: Validator for entity owned by single service (Pet -> CUSTOMERS)
    if simple == "PetValidator":
        ref = next((p for s, p in micro_idx.get("Pet", []) if s == "CUSTOMERS"), None)
        if ref:
            return {
                "reference_service": "CUSTOMERS",
                "mapping_rule": "RULE_2_VALIDATOR_FOR_ENTITY_PET",
                "reference_artifact": "Pet.java",
                "reference_path": str(ref.relative_to(MICRO)),
                "mapping_confidence": "MEDIUM",
            }

    # RULE 2b-repo: Spring Data repository for entity E -> service that owns model E
    if simple.endswith("Repository"):
        text = source_path.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"Repository<\s*(\w+)", text) or re.search(
            r"extends\s+\w+<\s*(\w+)", text
        )
        if m:
            entity = m.group(1)
            hits = micro_idx.get(entity, [])
            hits = [(s, p) for s, p in hits if s in SERVICE_DIRS and "/model/" in str(p)]
            if len(hits) == 1:
                svc, ref = hits[0]
                return {
                    "reference_service": svc,
                    "mapping_rule": "RULE_2_REPOSITORY_ENTITY_TYPE",
                    "reference_artifact": ref.name,
                    "reference_path": str(ref.relative_to(MICRO)),
                    "mapping_confidence": "HIGH",
                }

    # RULE 2c: vet package aggregate Vets -> VETS (same bounded context as Vet)
    if simple == "Vets" and ".vet." in qualified:
        ref = next((p for s, p in micro_idx.get("Vet", []) if s == "VETS"), None)
        if ref:
            return {
                "reference_service": "VETS",
                "mapping_rule": "RULE_2_VET_PACKAGE_AGGREGATE",
                "reference_artifact": "Vet.java",
                "reference_path": str(ref.relative_to(MICRO)),
                "mapping_confidence": "MEDIUM",
            }

    return None


def parse_java_refs(path: Path, component_names: set[str]) -> set[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    refs: set[str] = set()
    pkg = ""
    m = re.search(r"package\s+([\w.]+)\s*;", text)
    if m:
        pkg = m.group(1)
    for imp in re.findall(r"import\s+(?:static\s+)?([\w.]+)\s*;", text):
        simple = imp.split(".")[-1]
        if simple in component_names:
            refs.add(simple)
    # same-package references by type usage
    for name in component_names:
        if name in text and name != path.stem:
            if re.search(rf"\b{name}\b", text):
                refs.add(name)
    return refs


def build_inventory_and_mapping() -> tuple[list[dict], list[dict], list[dict]]:
    micro_idx = micro_simple_index()
    inventory = []
    mapping_rows = []
    excluded = []
    cid = 0
    for path in monolith_java_files():
        rel = str(path.relative_to(MONO))
        text = path.read_text(encoding="utf-8", errors="replace")
        pkg_m = re.search(r"package\s+([\w.]+)\s*;", text)
        pkg = pkg_m.group(1) if pkg_m else ""
        simple = path.stem
        qualified = f"{pkg}.{simple}" if pkg else simple
        excl = should_exclude(qualified, simple, rel)
        included = excl is None
        cid += 1
        inv = {
            "component_id": f"PC-{cid:03d}",
            "simple_name": simple,
            "qualified_name": qualified,
            "source_path": rel,
            "component_kind": classify_kind(simple),
            "included": str(included).lower(),
            "exclusion_reason": excl or "",
        }
        inventory.append(inv)
        if not included:
            excluded.append(inv)
            continue
        mapped = map_component(simple, qualified, pkg, micro_idx, path)
        if mapped is None:
            excluded.append({**inv, "exclusion_reason": "ambiguous_or_no_microservice_counterpart"})
            inv["included"] = "false"
            inv["exclusion_reason"] = "ambiguous_or_no_microservice_counterpart"
            continue
        mapping_rows.append(
            {
                "monolith_component": simple,
                "reference_service": mapped["reference_service"],
                "mapping_rule": mapped["mapping_rule"],
                "reference_artifact": mapped["reference_artifact"],
                "reference_path": mapped["reference_path"],
                "mapping_confidence": mapped["mapping_confidence"],
                "included": "true",
            }
        )
    return inventory, mapping_rows, excluded


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def build_identifier_map(mapping: list[dict]) -> list[dict]:
    names = sorted({r["monolith_component"] for r in mapping})
    rows = []
    for i, name in enumerate(names, start=1):
        rows.append(
            {
                "original_identifier": name,
                "anonymized_identifier": f"Component_{i:02d}",
                "anonymized_module": f"Module_{i:02d}",
                "anonymized_file": f"artifacts/Component_{i:02d}.java",
            }
        )
    return rows


def component_catalog(mapping: list[dict], id_map: dict[str, str], semantic: bool) -> list[dict]:
    inv_by_name = {r["simple_name"]: r for r in inventory_global}
    out = []
    for row in mapping:
        name = row["monolith_component"]
        inv = inv_by_name[name]
        anon = id_map[name]
        out.append(
            {
                "name": name if semantic else anon["anonymized_identifier"],
                "module": inv["qualified_name"].rsplit(".", 1)[0] if semantic else anon["anonymized_module"],
                "file": inv["source_path"] if semantic else anon["anonymized_file"],
                "kind": inv["component_kind"],
            }
        )
    return out


inventory_global: list[dict] = []


def extract_relations(components: list[str]) -> tuple[list[dict], list[dict]]:
    name_set = set(components)
    call_edges = []
    data_edges = []
    path_by_name = {p.stem: p for p in monolith_java_files()}
    for name in components:
        path = path_by_name.get(name)
        if not path:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        refs = parse_java_refs(path, name_set)
        kind = classify_kind(name)
        for tgt in sorted(refs):
            if tgt == name:
                continue
            call_edges.append({"source": name, "target": tgt, "relation": "static_reference"})
        if kind == "repository":
            m = re.search(r"Repository<\s*(\w+)", text) or re.search(r"extends\s+\w+<\s*(\w+)", text)
            if m and m.group(1) in name_set:
                data_edges.append(
                    {"source": name, "target": m.group(1), "relation": "repository_entity"}
                )
        if kind == "controller" and "Repository" in text:
            for repo in name_set:
                if repo.endswith("Repository") and repo in text:
                    data_edges.append(
                        {"source": name, "target": repo, "relation": "controller_repository"}
                    )
    return call_edges, data_edges


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_evidence(
    condition: str,
    semantic: bool,
    catalog: list[dict],
    call_edges: list[dict],
    data_edges: list[dict],
    id_map: dict[str, dict],
) -> dict:
    def remap_name(n: str) -> str:
        if semantic:
            return n
        return id_map[n]["anonymized_identifier"]

    comp = catalog
    payload = {
        "experiment_id": "PETCLINIC_EXT_V1",
        "evidence_condition": condition,
        "identifier_condition": "SEMANTIC" if semantic else "ANONYMIZED",
        "generated_at": datetime.now(UTC).isoformat(),
        "domain_description_ref": "DOMAIN_DESCRIPTION.txt",
        "components": comp,
    }
    if condition == "E1_STRUCTURAL":
        payload["static_call_edges"] = [
            {"source": remap_name(e["source"]), "target": remap_name(e["target"]), "relation": e["relation"]}
            for e in call_edges
        ]
        payload["data_relations"] = [
            {"source": remap_name(e["source"]), "target": remap_name(e["target"]), "relation": e["relation"]}
            for e in data_edges
        ]
    return payload


def prompt_body(condition: str, semantic: bool, evidence_filename: str) -> str:
    ident = "SEMANTIC" if semantic else "ANONYMIZED"
    domain = DOMAIN_FILE.read_text(encoding="utf-8").strip()
    schema = """Return ONLY a JSON object with this shape (no markdown, no commentary):
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
Service names are free text; do not assume any fixed label set.
Do not use a hidden labeled reference partition."""
    cond_text = {
        "E0_MINIMAL": "E0_MINIMAL: domain description and component catalog only (no static-call or persistence relation lists).",
        "E1_STRUCTURAL": "E1_STRUCTURAL: domain description, component catalog, static-call dependencies, and data-access relations.",
    }[condition]
    return (
        "You are a software architect proposing a microservice decomposition of a legacy Spring PetClinic monolith.\n"
        "Reason only from the information in this prompt and the bundled evidence JSON.\n\n"
        f"{schema}\n\n"
        f"## Condition\n{cond_text}\n\n"
        f"## Identifier treatment\n{ident} identifiers in the evidence package.\n\n"
        f"## Domain description\n{domain}\n\n"
        f"## Evidence\nSee architectural evidence file: {evidence_filename}\n"
    )


def main() -> int:
    global inventory_global
    (BASE / "evidence").mkdir(parents=True, exist_ok=True)
    (BASE / "prompts").mkdir(parents=True, exist_ok=True)

    mono_g = git_info(MONO)
    micro_g = git_info(MICRO)

    inventory, mapping, excluded = build_inventory_and_mapping()
    inventory_global = inventory
    id_rows = build_identifier_map(mapping)
    id_map = {r["original_identifier"]: r for r in id_rows}

    components = [r["monolith_component"] for r in mapping]
    call_edges, data_edges = extract_relations(components)

    # Write core CSVs
    write_csv(
        BASE / "component_inventory.csv",
        inventory,
        list(inventory[0].keys()) if inventory else [],
    )
    write_csv(
        BASE / "reference_mapping.csv",
        mapping,
        [
            "monolith_component",
            "reference_service",
            "mapping_rule",
            "reference_artifact",
            "reference_path",
            "mapping_confidence",
            "included",
        ],
    )
    write_csv(
        BASE / "component_identifier_map.csv",
        id_rows,
        ["original_identifier", "anonymized_identifier", "anonymized_module", "anonymized_file"],
    )

    (BASE / "evidence" / "static_relations.json").write_text(
        json.dumps(
            {
                "method": "regex_import_and_type_reference_scan",
                "definition": "Directed edge source->target if source Java unit references target component simple name",
                "filter": "included monolith components only; test sources excluded",
                "node_count": len(components),
                "edge_count": len(call_edges),
                "edges": call_edges,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (BASE / "evidence" / "data_relations.json").write_text(
        json.dumps(
            {
                "method": "repository_generic_and_controller_repository_scan",
                "rules": [
                    "Repository<T> -> entity T edge",
                    "Controller referencing Repository simple name -> controller_repository edge",
                ],
                "edge_count": len(data_edges),
                "edges": data_edges,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    for condition in ("E0_MINIMAL", "E1_STRUCTURAL"):
        for semantic in (True, False):
            tag = "SEMANTIC" if semantic else "ANON"
            cat = component_catalog(mapping, id_map, semantic)
            ev = build_evidence(condition, semantic, cat, call_edges, data_edges, id_map)
            ev_path = BASE / "evidence" / f"{condition}_{tag}.json"
            ev_path.write_text(json.dumps(ev, indent=2) + "\n", encoding="utf-8")
            pr_path = BASE / "prompts" / f"{condition}_{tag}.txt"
            pr_path.write_text(prompt_body(condition, semantic, ev_path.name), encoding="utf-8")  # noqa: ev_path.name

    # reference hash
    ref_bytes = (BASE / "reference_mapping.csv").read_bytes()
    (BASE / "reference_mapping.sha256").write_text(
        hashlib.sha256(ref_bytes).hexdigest() + "  reference_mapping.csv\n", encoding="utf-8"
    )

    # manifest 60 runs
    git_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    models = [
        ("gemini-2.5-flash", "gemini-2.5-flash"),
        ("gpt-4o-mini", "gpt-4o-mini"),
        ("llama3.1", "llama3.1"),
    ]
    conditions = ["E0_MINIMAL", "E1_STRUCTURAL"]
    rows = []
    order = 0
    pair_index = 0
    for model, model_id in models:
        safe = model.replace(".", "").replace("/", "-")
        for cond in conditions:
            for rep in range(1, 6):
                pair_index += 1
                first = "SEMANTIC" if pair_index % 2 == 1 else "ANONYMIZED"
                second = "ANONYMIZED" if first == "SEMANTIC" else "SEMANTIC"
                pair_id = f"{model}|{cond}|{rep}"
                for pos, ident in ((1, first), (2, second)):
                    order += 1
                    tag = "SEMANTIC" if ident == "SEMANTIC" else "ANON"
                    prompt_path = BASE / "prompts" / f"{cond}_{tag}.txt"
                    evidence_path = BASE / "evidence" / f"{cond}_{tag}.json"
                    out = (
                        REPO
                        / "outputs/runs/petclinic_ext_v1"
                        / safe
                        / cond
                        / ident.lower()
                        / f"run_{rep:02d}"
                    )
                    rows.append(
                        {
                            "run_id": f"PET-{order:03d}",
                            "model": model,
                            "requested_model_id": model_id,
                            "resolved_model_version": "",
                            "evidence_condition": cond,
                            "identifier_condition": ident,
                            "repetition": rep,
                            "pair_id": pair_id,
                            "pair_position": pos,
                            "pair_first_condition": first,
                            "execution_order": order,
                            "prompt_path": str(prompt_path.relative_to(REPO)),
                            "evidence_path": str(evidence_path.relative_to(REPO)),
                            "temperature": "0.2",
                            "seed_if_supported": "",
                            "prompt_sha256": sha256_file(prompt_path),
                            "evidence_sha256": sha256_file(evidence_path),
                            "git_sha_monolith": mono_g["sha"],
                            "git_sha_reference": micro_g["sha"],
                            "git_sha_repo": git_sha,
                            "expected_output_path": str(out.relative_to(REPO)),
                        }
                    )
    write_csv(BASE / "run_manifest.csv", rows, list(rows[0].keys()))

    # counts
    per_svc = {}
    for r in mapping:
        per_svc[r["reference_service"]] = per_svc.get(r["reference_service"], 0) + 1
    small = {s: n for s, n in per_svc.items() if n < 3}
    summary = {
        "included_components": len(mapping),
        "per_service": per_svc,
        "excluded_count": len([i for i in inventory if i["included"] == "false"]),
        "small_reference_clusters": small,
        "go_recommendation": "GO"
        if len(mapping) >= 12 and all(n >= 2 for n in per_svc.values())
        else "NO-GO",
    }
    (BASE / "freeze_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
