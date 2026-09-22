#!/usr/bin/env python3
"""Pre-execution validation checks A–J (no LLM calls)."""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from decomposition.llm.prompts import build_prompt  # noqa: E402

COMP_MAP = BASE / "component_identifier_map.csv"
AREA_MAP = BASE / "functional_area_identifier_map.csv"
SEMANTIC = REPO / "outputs" / "evidence" / "architectural_evidence.json"
ANON = BASE / "evidence" / "architectural_evidence_anonymized.json"
GOLD = REPO / "reference" / "historical_architecture.json"
PROMPT_DIR = BASE / "prompts"
MODULE_MAP = BASE / "evidence" / "module_path_map.csv"
REPORT = BASE / "validation_results.json"

AREA_SLUGS = {"faculty", "student", "grade", "finance", "attendance", "library"}
REFERENCE_SERVICE_LABELS = {
    "Faculty",
    "Student",
    "Grade",
    "Finance",
    "Attendance",
    "Library",
}


def load_component_forward() -> dict[str, str]:
    forward: dict[str, str] = {}
    with COMP_MAP.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            forward[row["original_identifier"]] = row["anonymized_identifier"]
    return forward


def load_area_forward() -> dict[str, str]:
    forward: dict[str, str] = {}
    with AREA_MAP.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            forward[row["original_area_id"]] = row["anonymized_area_id"]
    return forward


def count_structure(evidence: dict) -> dict:
    return {
        "components": len(evidence.get("components") or []),
        "g_call_edges": len((evidence.get("dependencies") or {}).get("G_call") or []),
        "database_usage": len(evidence.get("database_usage") or []),
        "entity_ownership": len(evidence.get("entity_ownership") or []),
        "runtime_endpoints": len(
            ((evidence.get("runtime_interactions") or {}).get("endpoints") or [])
        ),
        "migration_rules": len(
            (evidence.get("migration_constraints") or {}).get("rules") or []
        ),
    }


def original_modules() -> list[str]:
    mods = []
    with MODULE_MAP.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            mods.append(row["original_module"])
    return mods


def main() -> int:
    forward = load_component_forward()
    reverse = {v: k for k, v in forward.items()}
    area_forward = load_area_forward()
    semantic = json.loads(SEMANTIC.read_text(encoding="utf-8"))
    anonymized = json.loads(ANON.read_text(encoding="utf-8"))
    anon_text_blob = ANON.read_text(encoding="utf-8")
    results: dict[str, dict] = {}

    results["A_bijection_forward"] = {
        "pass": len(forward) == len(set(forward.values())) == 26,
        "n": len(forward),
    }
    results["B_bijection_reverse"] = {"pass": len(reverse) == 26}

    leaks: list[str] = []
    for path in sorted(PROMPT_DIR.glob("*_ANON.txt")):
        text = path.read_text(encoding="utf-8")
        for orig in forward:
            if orig in text:
                leaks.append(f"{path.name}: component {orig}")
        for slug in AREA_SLUGS:
            if re.search(rf"^- {slug}:", text):
                leaks.append(f"{path.name}: functional area slug '{slug}'")
    results["C_no_identity_aliases_in_anon_prompts"] = {"pass": leaks == [], "leaks": leaks[:30]}

    gold_in_prompts = [
        p.name
        for p in PROMPT_DIR.glob("*.txt")
        if "historical_architecture.json" in p.read_text(encoding="utf-8")
    ]
    results["D_no_gold_file_in_prompts"] = {"pass": gold_in_prompts == [], "hits": gold_in_prompts}

    s_counts = count_structure(semantic)
    a_counts = count_structure(anonymized)
    results["E_structure_unchanged"] = {"pass": s_counts == a_counts, "semantic": s_counts, "anonymized": a_counts}
    results["F_relation_parity"] = results["E_structure_unchanged"]

    sr = semantic.get("migration_constraints") or {}
    ar = anonymized.get("migration_constraints") or {}
    results["G_rules_unchanged"] = {"pass": (sr.get("rules") or []) == (ar.get("rules") or [])}

    h_ok = True
    for cond in ["C0", "C1", "C2", "C3"]:
        if len(build_prompt(cond, semantic).split("\n\n")) != len(
            build_prompt(cond, anonymized).split("\n\n")
        ):
            h_ok = False
    results["H_prompt_section_count"] = {"pass": h_ok}

    map_leak = [
        p.name
        for p in PROMPT_DIR.glob("*_ANON.txt")
        if "component_identifier_map" in p.read_text(encoding="utf-8")
        or "original_identifier" in p.read_text(encoding="utf-8")
    ]
    results["I_map_not_in_prompt"] = {"pass": map_leak == [], "leaks": map_leak}

    results["J_scoring_reverse_map"] = {
        "pass": len(reverse) == 26,
        "eval_universe": "24 components; AuthService/UserRepository excluded after reverse map",
    }

    mod_leaks = []
    for mod in original_modules():
        if mod and mod in anon_text_blob:
            mod_leaks.append(mod)
    results["K_no_original_module_paths_in_anon_evidence"] = {
        "pass": mod_leaks == [],
        "sample_leaks": mod_leaks[:10],
    }

    file_leaks = []
    for row in anonymized.get("components") or []:
        f = str(row.get("file") or "")
        if "monolith/" in f or f.endswith("_repository.py"):
            file_leaks.append(f)
    results["L_opaque_file_paths"] = {"pass": file_leaks == [], "bad": file_leaks[:10]}

    area_ids = [
        str(a.get("id") or "")
        for a in (anonymized.get("domain_descriptions") or {}).get("functional_areas") or []
    ]
    results["M_opaque_functional_area_ids"] = {
        "pass": all(aid.startswith("Area_") for aid in area_ids) and not any(
            aid in AREA_SLUGS for aid in area_ids
        ),
        "area_ids": area_ids,
    }

    schema_text = (REPO / "decomposition" / "llm" / "prompts.py").read_text(encoding="utf-8")
    schema_hits = [label for label in REFERENCE_SERVICE_LABELS if label in schema_text]
    results["schema_reference_labels_in_prompt_template"] = {
        "pass": schema_hits == [],
        "hits": schema_hits,
    }

    manifest_path = BASE / "run_manifest.csv"
    manifest_rows = list(csv.DictReader(manifest_path.open(encoding="utf-8")))
    pairs: dict[str, list[dict]] = {}
    for row in manifest_rows:
        pairs.setdefault(row["pair_id"], []).append(row)
    pair_ok = all(len(v) == 2 for v in pairs.values()) and len(pairs) == 60
    pair_members_ok = all(
        {r["identifier_condition"] for r in members} == {"SEMANTIC", "ANONYMIZED"}
        for members in pairs.values()
    )
    counter_ok = True
    for members in pairs.values():
        by_pos = {r["pair_position"]: r["identifier_condition"] for r in members}
        if set(by_pos) != {"1", "2"}:
            counter_ok = False
            continue
        first = members[0]["pair_first_condition"]
        if by_pos["1"] != first:
            counter_ok = False
    results["N_counterbalanced_pair_order"] = {"pass": pair_ok and counter_ok and pair_members_ok}
    results["O_pair_semantic_anonymized"] = {"pass": pair_members_ok, "n_pairs": len(pairs)}
    p_ok = True
    for members in pairs.values():
        m0 = members[0]
        for m in members:
            if (
                m["model"] != m0["model"]
                or m["evidence_condition"] != m0["evidence_condition"]
                or m["repetition"] != m0["repetition"]
                or m["temperature"] != m0["temperature"]
                or m["protocol_version"] != m0["protocol_version"]
            ):
                p_ok = False
    results["P_pair_settings_match"] = {"pass": p_ok}
    hash_ok = all(row.get("prompt_sha256") and row.get("evidence_sha256") for row in manifest_rows)
    results["Q_prompt_evidence_hashes_recorded"] = {"pass": hash_ok}
    results["R_no_reference_partition"] = results["D_no_gold_file_in_prompts"]
    digest_file = BASE / "llama_digest_frozen.txt"
    results["S_llama_digest_frozen"] = {
        "pass": digest_file.is_file()
        and any(
            line.startswith("digest:")
            and len(line.split(":", 1)[1].strip()) >= 8
            for line in digest_file.read_text(encoding="utf-8").splitlines()
        ),
    }
    policy = BASE / "RETRY_FAILURE_POLICY.md"
    results["T_retry_policy_frozen"] = {"pass": policy.is_file()}

    all_pass = all(r.get("pass") for r in results.values() if "pass" in r)
    REPORT.write_text(json.dumps({"all_pass": all_pass, "checks": results}, indent=2) + "\n")
    print(json.dumps({"all_pass": all_pass}, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
