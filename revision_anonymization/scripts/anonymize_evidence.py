#!/usr/bin/env python3
"""Produce anonymized architectural evidence (identity aliases opaque)."""

from __future__ import annotations

import copy
import csv
import json
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parents[1]
COMP_MAP = BASE / "component_identifier_map.csv"
AREA_MAP = BASE / "functional_area_identifier_map.csv"
SRC = REPO / "outputs" / "evidence" / "architectural_evidence.json"
OUT = BASE / "evidence" / "architectural_evidence_anonymized.json"
MODULE_OUT = BASE / "evidence" / "module_path_map.csv"
FILE_OUT = BASE / "evidence" / "file_path_map.csv"


def load_component_map() -> tuple[dict[str, dict[str, str]], dict[str, str], dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    forward: dict[str, str] = {}
    with COMP_MAP.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            orig = row["original_identifier"]
            rows[orig] = row
            forward[orig] = row["anonymized_identifier"]
    reverse = {v: k for k, v in forward.items()}
    return rows, forward, reverse


def load_area_map() -> dict[str, str]:
    mapping: dict[str, str] = {}
    with AREA_MAP.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            mapping[row["original_area_id"]] = row["anonymized_area_id"]
    return mapping


def replace_components_in_string(text: str, forward: dict[str, str]) -> str:
    if not text or not isinstance(text, str):
        return text
    out = text
    for original in sorted(forward, key=len, reverse=True):
        out = out.replace(original, forward[original])
    return out


def walk_replace_components(obj: Any, forward: dict[str, str]) -> Any:
    if isinstance(obj, str):
        return replace_components_in_string(obj, forward)
    if isinstance(obj, list):
        return [walk_replace_components(item, forward) for item in obj]
    if isinstance(obj, dict):
        return {key: walk_replace_components(val, forward) for key, val in obj.items()}
    return obj


def anonymize_component_records(evidence: dict[str, Any], comp_meta: dict[str, dict[str, str]]) -> None:
    module_rows = []
    file_rows = []
    for row in evidence.get("components") or []:
        orig_name = str(row.get("name") or "")
        meta = comp_meta.get(orig_name, {})
        anon = meta.get("anonymized_identifier", orig_name)
        orig_mod = str(row.get("module") or "")
        orig_file = str(row.get("file") or "")
        row["name"] = anon
        row["module"] = meta.get("anonymized_module", f"Module_{anon.split('_')[1]}")
        row["file"] = meta.get("anonymized_file", f"artifacts/{anon}.py")
        metrics = row.get("metrics")
        if isinstance(metrics, dict) and metrics.get("component"):
            metrics["component"] = anon
        module_rows.append(
            {
                "original_module": orig_mod,
                "anonymized_module": row["module"],
                "component": anon,
            }
        )
        file_rows.append(
            {
                "original_file": orig_file,
                "anonymized_file": row["file"],
                "component": anon,
            }
        )
    MODULE_OUT.parent.mkdir(parents=True, exist_ok=True)
    with MODULE_OUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["original_module", "anonymized_module", "component"]
        )
        writer.writeheader()
        writer.writerows(module_rows)
    with FILE_OUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["original_file", "anonymized_file", "component"]
        )
        writer.writeheader()
        writer.writerows(file_rows)


def anonymize_functional_area_ids(evidence: dict[str, Any], area_map: dict[str, str]) -> None:
    domain = evidence.get("domain_descriptions") or {}
    for area in domain.get("functional_areas") or []:
        orig = str(area.get("id") or "")
        if orig in area_map:
            area["id"] = area_map[orig]


def anonymize_system_paths(evidence: dict[str, Any]) -> None:
    system = evidence.get("system") or {}
    if system.get("app_root"):
        system["app_root"] = "artifacts/app"
    if system.get("traces_path"):
        system["traces_path"] = "artifacts/runtime_traces.jsonl"


def replace_module_path_aliases(obj: Any, module_pairs: list[tuple[str, str]]) -> Any:
    if isinstance(obj, str):
        out = obj
        for original, anonymized in sorted(module_pairs, key=lambda p: len(p[0]), reverse=True):
            if original:
                out = out.replace(original, anonymized)
        return out
    if isinstance(obj, list):
        return [replace_module_path_aliases(item, module_pairs) for item in obj]
    if isinstance(obj, dict):
        return {k: replace_module_path_aliases(v, module_pairs) for k, v in obj.items()}
    return obj


def main() -> None:
    comp_meta, forward, _ = load_component_map()
    area_map = load_area_map()
    payload = json.loads(SRC.read_text(encoding="utf-8"))
    anon = copy.deepcopy(payload)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    anonymize_component_records(anon, comp_meta)
    anonymize_functional_area_ids(anon, area_map)
    anonymize_system_paths(anon)
    anon = walk_replace_components(anon, forward)
    with MODULE_OUT.open(encoding="utf-8") as handle:
        module_pairs = [
            (row["original_module"], row["anonymized_module"])
            for row in csv.DictReader(handle)
            if row.get("original_module")
        ]
    anon = replace_module_path_aliases(anon, module_pairs)
    OUT.write_text(json.dumps(anon, indent=2) + "\n", encoding="utf-8")
    semantic_copy = BASE / "evidence" / "architectural_evidence_semantic_frozen_ref.json"
    semantic_copy.write_text(SRC.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
