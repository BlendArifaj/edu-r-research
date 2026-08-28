from __future__ import annotations

import json
import os
import platform
import random
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from importlib import metadata
from pathlib import Path
from typing import Any

from decomposition.baselines.runner import run_from_paths
from decomposition.extraction.evidence_builder import build_evidence_package, write_package
from decomposition.llm.providers import MissingCredentialsError, credentials_available, get_provider
from decomposition.llm.runner import run_llm_experiments

PACKAGES = ("fastapi", "sqlalchemy", "networkx", "pydantic", "httpx", "numpy")


def next_run_dir(runs_root: Path, when: datetime | None = None) -> Path:
    moment = when or datetime.now()
    day = moment.strftime("%Y-%m-%d")
    runs_root.mkdir(parents=True, exist_ok=True)
    serial = 1
    for path in runs_root.glob(f"{day}_*"):
        suffix = path.name.split("_")[-1]
        if suffix.isdigit():
            serial = max(serial, int(suffix) + 1)
    return runs_root / f"{day}_{serial:03d}"


def load_matrix_config(path: Path) -> dict[str, Any]:
    import yaml

    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(loaded, dict):
        raise ValueError("matrix config must be a mapping")
    return loaded


def run_matrix(
    *,
    repo_root: Path,
    config_path: Path,
    skip_extract: bool = False,
    skip_llm: bool = False,
    runs_root: Path | None = None,
    only_providers: list[str] | None = None,
    only_ids: list[str] | None = None,
    reuse_llm_from: Path | None = None,
) -> dict[str, Any]:
    config = load_matrix_config(config_path)
    seed = int(config.get("seed", 42))
    _seed_rng(seed)
    run_dir = next_run_dir(runs_root or repo_root / "outputs" / "runs")
    run_dir.mkdir(parents=True, exist_ok=True)
    steps: list[dict[str, Any]] = []
    llm_cfg = config.get("llm") or {}
    providers = [name.lower() for name in (only_providers or [])]
    ids = [name.upper() for name in (only_ids or [])]
    manifest: dict[str, Any] = {
        "run_id": run_dir.name,
        "started_at": datetime.now(UTC).isoformat(),
        "system": "SEMS-R",
        "is_original_sems_source": False,
        "gold_used_for_evaluation_only": True,
        "llm_outputs_fabricated": False,
        "seed": seed,
        "python": sys.version,
        "platform": platform.platform(),
        "git": _git_state(repo_root),
        "package_versions": _package_versions(),
        "config_path": str(config_path),
        "planned_llm_slots": llm_cfg.get("models") or [],
        "only_providers": providers or None,
        "only_ids": ids or None,
        "reuse_llm_from": str(reuse_llm_from) if reuse_llm_from else None,
        "steps": steps,
    }
    _copy_configs(repo_root, run_dir)
    evidence_path = _prepare_evidence(repo_root, run_dir, skip_extract, steps)
    if config.get("baselines", True):
        _run_baselines(repo_root, run_dir, evidence_path, steps)
    if reuse_llm_from is not None:
        copied = _reuse_llm_runs(Path(reuse_llm_from), run_dir / "decompositions")
        steps.append(
            {
                "name": "reuse-llm",
                "status": "ok" if copied else "skipped",
                "from": str(reuse_llm_from),
                "copied": copied,
            }
        )
    skip_missing = bool(llm_cfg.get("skip_if_missing_credentials", True))
    _run_llm_slots(
        run_dir,
        evidence_path,
        llm_cfg,
        skip_llm=skip_llm,
        skip_if_missing=skip_missing,
        only_providers=providers,
        only_ids=ids,
        steps=steps,
    )
    if config.get("evaluate", True):
        _run_evaluate(repo_root, run_dir, evidence_path, steps)
    _write_index(run_dir, steps)
    manifest["finished_at"] = datetime.now(UTC).isoformat()
    manifest["run_dir"] = str(run_dir)
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def _prepare_evidence(
    repo_root: Path, run_dir: Path, skip_extract: bool, steps: list[dict[str, Any]]
) -> Path:
    dest = run_dir / "evidence"
    dest.mkdir(parents=True, exist_ok=True)
    traces_src = repo_root / "outputs" / "evidence" / "runtime_traces.jsonl"
    traces_dest = dest / "runtime_traces.jsonl"
    if traces_src.exists() and not traces_dest.exists():
        shutil.copy2(traces_src, traces_dest)
    if skip_extract:
        src = repo_root / "outputs" / "evidence" / "architectural_evidence.json"
        if not src.exists():
            raise FileNotFoundError("no frozen evidence to copy")
        shutil.copy2(src, dest / "architectural_evidence.json")
        md = src.with_suffix(".md")
        if md.exists():
            shutil.copy2(md, dest / "architectural_evidence.md")
        steps.append({"name": "extract-evidence", "status": "copied", "path": str(src)})
        return dest / "architectural_evidence.json"
    package = build_evidence_package(
        app_root=repo_root / "monolith" / "app",
        traces_path=traces_dest if traces_dest.exists() else None,
        domain_path=repo_root / "reference" / "domain_description.json",
        rules_path=repo_root / "reference" / "migration_rules.json",
    )
    write_package(package, dest)
    steps.append(
        {"name": "extract-evidence", "status": "ok", "runtime_traces": traces_dest.exists()}
    )
    return dest / "architectural_evidence.json"


def _run_baselines(
    repo_root: Path, run_dir: Path, evidence_path: Path, steps: list[dict[str, Any]]
) -> None:
    out = run_dir / "decompositions"
    run_from_paths(evidence_path, out, repo_root / "experiments" / "configs" / "baselines.yaml")
    steps.append({"name": "baselines", "status": "ok", "out": str(out)})


def _run_llm_slots(
    run_dir: Path,
    evidence_path: Path,
    llm_cfg: dict[str, Any],
    *,
    skip_llm: bool,
    skip_if_missing: bool,
    only_providers: list[str],
    only_ids: list[str],
    steps: list[dict[str, Any]],
) -> None:
    conditions = [str(item) for item in llm_cfg.get("conditions") or ["C0", "C1", "C2", "C3"]]
    runs = int(llm_cfg.get("runs") or 3)
    temperature = float(llm_cfg.get("temperature") or 0.2)
    max_retries = int(llm_cfg.get("max_retries") or 2)
    out = run_dir / "decompositions"
    evidence: dict[str, Any] | None = None
    selected = {name.lower() for name in only_providers}
    selected_ids = {name.upper() for name in only_ids}
    ollama_selected = False
    if selected or selected_ids:
        ollama_selected = any(
            str(slot.get("provider") or "").lower() == "ollama"
            and (not selected or str(slot.get("provider") or "").lower() in selected)
            and (not selected_ids or str(slot.get("id") or "").upper() in selected_ids)
            for slot in (llm_cfg.get("models") or [])
        )
    for slot in llm_cfg.get("models") or []:
        provider_name = str(slot.get("provider") or "")
        model = str(slot.get("model") or "")
        slot_id = str(slot.get("id") or model)
        if skip_llm:
            steps.append(_skipped_llm(slot_id, provider_name, model, "skipped (--skip-llm)"))
            continue
        if selected_ids and slot_id.upper() not in selected_ids:
            steps.append(_skipped_llm(slot_id, provider_name, model, "not selected (--ids)"))
            continue
        if selected and provider_name.lower() not in selected:
            steps.append(
                _skipped_llm(slot_id, provider_name, model, "not selected (--providers)")
            )
            continue
        ready, reason = credentials_available(
            provider_name,
            allow_local_ollama=ollama_selected,
        )
        if not ready:
            steps.append(_skipped_llm(slot_id, provider_name, model, reason))
            if not skip_if_missing:
                raise MissingCredentialsError(reason)
            continue
        if evidence is None:
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        provider = get_provider(provider_name)
        try:
            results = run_llm_experiments(
                evidence=evidence,
                provider=provider,
                model=model,
                conditions=conditions,
                runs=runs,
                temperature=temperature,
                max_retries=max_retries,
                out_dir=out,
                scientific=True,
            )
            scientific = sum(1 for row in results if row.get("is_scientific_run"))
            status = "ok" if scientific else "failed"
            steps.append(
                {
                    "name": f"llm-{slot_id}",
                    "status": status,
                    "provider": provider_name,
                    "model": model,
                    "scientific_runs": scientific,
                    "attempted_runs": len(results),
                    "fabricated": False,
                }
            )
        except MissingCredentialsError as exc:
            steps.append(_skipped_llm(slot_id, provider_name, model, str(exc)))
            if not skip_if_missing:
                raise


def _reuse_llm_runs(src_run: Path, dest: Path) -> list[str]:
    src = src_run / "decompositions"
    if not src.exists():
        return []
    dest.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for child in sorted(src.iterdir()):
        if not child.is_dir() or not _has_scientific_llm_run(child):
            continue
        target = dest / child.name
        if target.exists():
            continue
        shutil.copytree(child, target)
        copied.append(child.name)
    return copied


def _has_scientific_llm_run(model_dir: Path) -> bool:
    for meta_path in model_dir.glob("C*/run_*/metadata.json"):
        try:
            metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if metadata.get("is_scientific_run"):
            return True
    return False


def _skipped_llm(slot_id: str, provider: str, model: str, reason: str) -> dict[str, Any]:
    return {
        "name": f"llm-{slot_id}",
        "status": "skipped",
        "provider": provider,
        "model": model,
        "reason": reason,
        "fabricated": False,
        "is_scientific_run": False,
    }


def _run_evaluate(
    repo_root: Path, run_dir: Path, evidence_path: Path, steps: list[dict[str, Any]]
) -> None:
    from decomposition.evaluation.runner import evaluate_all

    evaluate_all(
        gold_path=repo_root / "reference" / "historical_architecture.json",
        evidence_path=evidence_path,
        decompositions_dir=run_dir / "decompositions",
        out_dir=run_dir / "metrics",
        expert_dir=run_dir / "expert_review",
    )
    steps.append({"name": "evaluate", "status": "ok", "gold_for_evaluation_only": True})


def _write_index(run_dir: Path, steps: list[dict[str, Any]]) -> None:
    skipped = [step for step in steps if step.get("status") == "skipped"]
    lines = [
        f"# SEMS-R experiment run `{run_dir.name}`",
        "",
        "Controlled reconstruction. Not original production SEMS.",
        "Historical gold labels were used only in the evaluate step.",
        "",
        "## Steps",
        "",
    ]
    for step in steps:
        extra = f" — {step['reason']}" if step.get("reason") else ""
        lines.append(f"- `{step['name']}`: {step.get('status')}{extra}")
    if skipped:
        lines += [
            "",
            "## LLM slots skipped",
            "",
            "No LLM outputs were fabricated. Set provider API keys and rerun the matrix.",
            "",
        ]
    metrics = run_dir / "metrics" / "table_a.md"
    if metrics.exists():
        lines += ["", "## Table A", "", metrics.read_text(encoding="utf-8")]
    (run_dir / "README.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _copy_configs(repo_root: Path, run_dir: Path) -> None:
    dest = run_dir / "config"
    dest.mkdir(parents=True, exist_ok=True)
    cfg = repo_root / "experiments" / "configs"
    for name in ("matrix.yaml", "baselines.yaml", "llm.yaml"):
        src = cfg / name
        if src.exists():
            shutil.copy2(src, dest / name)


def _git_state(repo_root: Path) -> dict[str, Any]:
    def _git(*args: str) -> str:
        result = subprocess.run(
            ["git", *args], cwd=repo_root, capture_output=True, text=True, check=False
        )
        return result.stdout.strip() if result.returncode == 0 else ""

    commit = _git("rev-parse", "HEAD")
    dirty = bool(_git("status", "--porcelain"))
    return {"commit": commit or None, "dirty": dirty, "available": bool(commit)}


def _package_versions() -> dict[str, str]:
    versions = {}
    for name in PACKAGES:
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            continue
    return versions


def _seed_rng(seed: int) -> None:
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    try:
        import numpy as np

        np.random.seed(seed)
    except ImportError:
        pass
