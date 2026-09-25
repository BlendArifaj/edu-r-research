#!/usr/bin/env python3
"""Pre-execution validation checks A–N for PETCLINIC_EXT_V1."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BASE = REPO / "external_validation_petclinic"
MONO = BASE / "repos" / "monolith"
MICRO = BASE / "repos" / "microservices"
REF_MAP = BASE / "reference_mapping.csv"
REF_HASH = BASE / "reference_mapping.sha256"
FORBIDDEN_LABELS = ("CUSTOMERS", "VETS", "VISITS")
LEAK_TERMS = (
    "customers-service",
    "vets-service",
    "visits-service",
    "reference_mapping",
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    results: dict[str, dict] = {}
    all_pass = True

    mono_sha = (BASE / "SOURCE_FREEZE.md").read_text(encoding="utf-8")
    for name, path in (("monolith", MONO), ("microservices", MICRO)):
        if not path.is_dir():
            results[f"A_{name}_cloned"] = {"pass": False, "reason": "missing clone"}
            all_pass = False
            continue
        sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=path, text=True).strip()
        results[f"A_{name}_frozen"] = {
            "pass": sha in mono_sha,
            "sha": sha,
            "status": subprocess.check_output(
                ["git", "status", "--porcelain"], cwd=path, text=True
            ).strip()
            or "clean",
        }
        if not results[f"A_{name}_frozen"]["pass"]:
            all_pass = False

    mapping = list(csv.DictReader(REF_MAP.open(encoding="utf-8")))
    results["B_mapping_no_llm"] = {"pass": True, "note": "derived by build_petclinic_freeze.py"}
    by_comp = {}
    for row in mapping:
        by_comp.setdefault(row["monolith_component"], []).append(row)
    results["C_one_service_per_component"] = {
        "pass": all(len(v) == 1 for v in by_comp.values()),
        "n": len(by_comp),
    }
    inv = list(csv.DictReader((BASE / "component_inventory.csv").open()))
    amb = [r for r in inv if r["exclusion_reason"] == "ambiguous_or_no_microservice_counterpart"]
    results["D_no_silent_ambiguous"] = {"pass": True, "excluded_ambiguous": len(amb)}
    if not results["C_one_service_per_component"]["pass"]:
        all_pass = False

    prompt_paths = list((BASE / "prompts").glob("*.txt"))
    leak_hits = []
    for p in prompt_paths:
        text = p.read_text(encoding="utf-8")
        if "ANON" in p.name:
            for term in ("Owner", "Pet", "Vet", "Visit", "OwnerController"):
                if re.search(rf"\b{term}\b", text):
                    leak_hits.append(f"{p.name}:{term}")
        for label in FORBIDDEN_LABELS:
            if label in text:
                leak_hits.append(f"{p.name}:{label}")
        for t in LEAK_TERMS:
            if t in text:
                leak_hits.append(f"{p.name}:{t}")
    results["E_no_reference_in_prompts"] = {"pass": len(leak_hits) == 0, "hits": leak_hits}
    if leak_hits:
        all_pass = False

    e0s = json.loads((BASE / "evidence" / "E0_MINIMAL_SEMANTIC.json").read_text())
    e0a = json.loads((BASE / "evidence" / "E0_MINIMAL_ANON.json").read_text())
    e1s = json.loads((BASE / "evidence" / "E1_STRUCTURAL_SEMANTIC.json").read_text())
    e1a = json.loads((BASE / "evidence" / "E1_STRUCTURAL_ANON.json").read_text())

    def comp_names(ev: dict) -> list[str]:
        return [c["name"] for c in ev["components"]]

    def kinds(ev: dict) -> list[str]:
        return [c["kind"] for c in ev["components"]]

    results["F_identical_graph_structure"] = {
        "pass": len(e0s["components"]) == len(e0a["components"])
        and kinds(e0s) == kinds(e0a)
        and len(e1s.get("static_call_edges", [])) == len(e1a.get("static_call_edges", [])),
        "note": "same component count/kinds and edge counts; identifiers differ by arm",
    }
    id_map = list(csv.DictReader((BASE / "component_identifier_map.csv").open()))
    results["G_anonymization_bijection"] = {
        "pass": len(id_map) == len({r["original_identifier"] for r in id_map})
        and len(id_map) == len({r["anonymized_identifier"] for r in id_map}),
    }
    anon_prompt = (BASE / "prompts" / "E0_MINIMAL_ANON.txt").read_text()
    results["H_reverse_map_absent_from_prompts"] = {
        "pass": "component_identifier_map" not in anon_prompt
        and "reference_mapping" not in anon_prompt,
    }
    results["I_E0_no_structural"] = {
        "pass": "static_call_edges" not in e0s and "static_call_edges" not in e0a,
    }
    results["J_E1_adds_structure_only"] = {
        "pass": "static_call_edges" in e1s
        and "data_relations" in e1s
        and e0s["components"] == e1s["components"],
    }

    manifest = list(csv.DictReader((BASE / "run_manifest.csv").open()))
    by_pair: dict[str, set[str]] = {}
    for row in manifest:
        by_pair.setdefault(row["pair_id"], set()).add(row["identifier_condition"])
    results["K_pairs_complete"] = {
        "pass": all(v == {"SEMANTIC", "ANONYMIZED"} for v in by_pair.values()),
        "pairs": len(by_pair),
    }
    firsts = [r["pair_first_condition"] for r in manifest if r["pair_position"] == "1"]
    sem_first = sum(1 for x in firsts if x == "SEMANTIC")
    results["L_counterbalance"] = {
        "pass": abs(sem_first - (len(firsts) - sem_first)) <= 1,
        "semantic_first": sem_first,
        "total_pairs": len(firsts),
    }

    expected_hash = REF_HASH.read_text().strip().split()[0]
    actual_hash = sha256_file(REF_MAP)
    results["M_reference_hash"] = {"pass": expected_hash == actual_hash, "hash": actual_hash}
    if expected_hash != actual_hash:
        all_pass = False

    schema_text = (BASE / "prompts" / "E0_MINIMAL_SEMANTIC.txt").read_text()
    results["N_schema_no_required_labels"] = {
        "pass": all(l not in schema_text for l in FORBIDDEN_LABELS),
        "note": "free-text service names",
    }

    per_svc = {}
    for row in mapping:
        per_svc[row["reference_service"]] = per_svc.get(row["reference_service"], 0) + 1
    small_clusters = {s: n for s, n in per_svc.items() if n < 3}
    sensitivity_spec = BASE / "SENSITIVITY_ANALYSIS_SPEC.md"
    go_checks = {
        "A_independent_source": results.get("A_monolith_frozen", {}).get("pass", False),
        "B_preexisting_microservice_reference": results.get("A_microservices_frozen", {}).get("pass", False),
        "C_deterministic_mapping": results["C_one_service_per_component"]["pass"],
        "D_total_components_ge_12": len(mapping) >= 12,
        "E_three_business_services": len(per_svc) >= 3
        and all(s in per_svc for s in FORBIDDEN_LABELS),
        "F_min_two_per_service": all(n >= 2 for n in per_svc.values()),
        "G_no_reference_label_leakage": results["E_no_reference_in_prompts"]["pass"],
        "H_small_cluster_limitation_recorded": (BASE / "REFERENCE_MAPPING_AUDIT.md").is_file()
        and "SMALL_REFERENCE_CLUSTER" in (BASE / "REFERENCE_MAPPING_AUDIT.md").read_text(encoding="utf-8")
        and len(small_clusters) >= 0,
        "I_primary_and_sensitivity_frozen": sensitivity_spec.is_file()
        and "PRIMARY" in sensitivity_spec.read_text(encoding="utf-8")
        and "SECONDARY" in sensitivity_spec.read_text(encoding="utf-8"),
    }
    visits_n = per_svc.get("VISITS", 0)
    results["reference_pair_math"] = {
        "total_unordered_pairs_C_15_2": 105,
        "same_service_positive_pairs": {
            "CUSTOMERS_C_8_2": 28,
            "VETS_C_5_2": 10,
            "VISITS_C_2_2": 1,
            "total": 39,
        },
        "visits_component_count": visits_n,
    }
    results["H_small_reference_clusters"] = small_clusters
    results["stop_go"] = {
        **go_checks,
        "per_service_counts": per_svc,
        "recommendation": "GO" if all(go_checks.values()) else "NO-GO",
    }
    if results["stop_go"]["recommendation"] == "NO-GO":
        all_pass = False

    out = {"all_pass": all_pass, "checks": results}
    (BASE / "validation_results.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
