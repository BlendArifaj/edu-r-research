from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest
from decomposition.extraction.evidence_builder import FORBIDDEN_GOLD
from experiments.matrix import next_run_dir, run_matrix

ROOT = Path(__file__).resolve().parents[2]


def test_next_run_dir_increments(tmp_path: Path) -> None:
    when = datetime(2026, 8, 27, 12, 0, 0)
    first = next_run_dir(tmp_path, when)
    assert first.name == "2026-08-27_001"
    first.mkdir()
    second = next_run_dir(tmp_path, when)
    assert second.name == "2026-08-27_002"


def test_credentials_available_without_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    from decomposition.llm.providers import credentials_available

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    monkeypatch.delenv("SEMS_ENABLE_OLLAMA", raising=False)
    ok, reason = credentials_available("openai")
    assert ok is False
    assert "OPENAI_API_KEY" in reason
    assert credentials_available("mock")[0] is False
    assert credentials_available("xai")[0] is False
    assert credentials_available("ollama")[0] is False
    assert credentials_available("ollama", allow_local_ollama=True)[0] is True


def test_matrix_skips_llm_without_keys_and_does_not_fabricate(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    repo = _stub_repo(tmp_path / "repo")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    monkeypatch.delenv("SEMS_ENABLE_OLLAMA", raising=False)

    def fail_if_called(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("LLM provider must not be called without credentials")

    monkeypatch.setattr("experiments.matrix.get_provider", fail_if_called)
    monkeypatch.setattr("experiments.matrix.run_llm_experiments", fail_if_called)
    gold_paths: list[Path] = []
    evidence_paths: list[Path] = []

    def fake_baselines(evidence_path: Path, out_dir: Path, _config_path: Path | None) -> dict:
        evidence_paths.append(evidence_path)
        assert FORBIDDEN_GOLD not in str(evidence_path)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "rule_based.json").write_text("{}\n", encoding="utf-8")
        return {}

    def fake_evaluate(**kwargs: object) -> dict:
        gold_paths.append(kwargs["gold_path"])  # type: ignore[arg-type]
        out_dir = kwargs["out_dir"]
        assert isinstance(out_dir, Path)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "table_a.md").write_text("stub\n", encoding="utf-8")
        return {}

    monkeypatch.setattr("experiments.matrix.run_from_paths", fake_baselines)
    monkeypatch.setattr("decomposition.evaluation.runner.evaluate_all", fake_evaluate)

    manifest = run_matrix(
        repo_root=repo,
        config_path=repo / "experiments" / "configs" / "matrix.yaml",
        skip_extract=True,
        runs_root=tmp_path / "runs",
    )
    skipped = [step for step in manifest["steps"] if step.get("status") == "skipped"]
    assert len(skipped) == 3
    assert all(step.get("fabricated") is False for step in skipped)
    assert all(step["name"].startswith("llm-") for step in skipped)
    assert gold_paths and gold_paths[0].name == "historical_architecture.json"
    assert evidence_paths and FORBIDDEN_GOLD not in str(evidence_paths[0])
    run_dir = Path(manifest["run_dir"])
    assert (run_dir / "manifest.json").exists()
    readme = (run_dir / "README.md").read_text(encoding="utf-8")
    assert "skipped" in readme
    assert "No LLM outputs were fabricated" in readme


def test_only_gemini_provider_skips_openai(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    repo = _stub_repo(tmp_path / "repo")
    monkeypatch.setenv("OPENAI_API_KEY", "fake-openai")
    monkeypatch.setenv("GEMINI_API_KEY", "fake-gemini")
    called: list[str] = []

    def fake_get_provider(name: str) -> object:
        called.append(name)
        return object()

    def fake_llm(**_kwargs: object) -> list[dict]:
        return [{"is_scientific_run": True}]

    def fake_baselines(*_args: object, **_kwargs: object) -> dict:
        return {}

    def fake_evaluate(**kwargs: object) -> dict:
        out_dir = kwargs["out_dir"]
        assert isinstance(out_dir, Path)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "table_a.md").write_text("stub\n", encoding="utf-8")
        return {}

    monkeypatch.setattr("experiments.matrix.get_provider", fake_get_provider)
    monkeypatch.setattr("experiments.matrix.run_llm_experiments", fake_llm)
    monkeypatch.setattr("experiments.matrix.run_from_paths", fake_baselines)
    monkeypatch.setattr("decomposition.evaluation.runner.evaluate_all", fake_evaluate)

    manifest = run_matrix(
        repo_root=repo,
        config_path=repo / "experiments" / "configs" / "matrix.yaml",
        skip_extract=True,
        runs_root=tmp_path / "runs",
        only_providers=["gemini"],
    )
    assert called == ["gemini"]
    by_name = {step["name"]: step for step in manifest["steps"]}
    assert by_name["llm-A"]["status"] == "skipped"
    assert "not selected" in by_name["llm-A"]["reason"]
    assert by_name["llm-B"]["status"] == "skipped"
    assert by_name["llm-C"]["status"] == "ok"


def test_only_ollama_provider_allows_localhost(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    repo = _stub_repo(tmp_path / "repo")
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    monkeypatch.delenv("SEMS_ENABLE_OLLAMA", raising=False)
    called: list[str] = []

    def fake_get_provider(name: str) -> object:
        called.append(name)
        return object()

    def fake_llm(**_kwargs: object) -> list[dict]:
        return [{"is_scientific_run": True}]

    def fake_baselines(*_args: object, **_kwargs: object) -> dict:
        return {}

    def fake_evaluate(**kwargs: object) -> dict:
        out_dir = kwargs["out_dir"]
        assert isinstance(out_dir, Path)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "table_a.md").write_text("stub\n", encoding="utf-8")
        return {}

    monkeypatch.setattr("experiments.matrix.get_provider", fake_get_provider)
    monkeypatch.setattr("experiments.matrix.run_llm_experiments", fake_llm)
    monkeypatch.setattr("experiments.matrix.run_from_paths", fake_baselines)
    monkeypatch.setattr("decomposition.evaluation.runner.evaluate_all", fake_evaluate)

    manifest = run_matrix(
        repo_root=repo,
        config_path=repo / "experiments" / "configs" / "matrix.yaml",
        skip_extract=True,
        runs_root=tmp_path / "runs",
        only_providers=["ollama"],
    )
    assert called == ["ollama"]
    by_name = {step["name"]: step for step in manifest["steps"]}
    assert by_name["llm-A"]["status"] == "skipped"
    assert by_name["llm-C"]["status"] == "skipped"
    assert by_name["llm-B"]["status"] == "ok"


def test_only_ids_runs_selected_slot(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    repo = _stub_repo(tmp_path / "repo")
    monkeypatch.setenv("OPENAI_API_KEY", "fake-openai")
    monkeypatch.setenv("GEMINI_API_KEY", "fake-gemini")
    models: list[str] = []

    def fake_get_provider(name: str) -> object:
        return object()

    def fake_llm(**kwargs: object) -> list[dict]:
        models.append(str(kwargs["model"]))
        return [{"is_scientific_run": True}]

    def fake_baselines(*_args: object, **_kwargs: object) -> dict:
        return {}

    def fake_evaluate(**kwargs: object) -> dict:
        out_dir = kwargs["out_dir"]
        assert isinstance(out_dir, Path)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "table_a.md").write_text("stub\n", encoding="utf-8")
        return {}

    monkeypatch.setattr("experiments.matrix.get_provider", fake_get_provider)
    monkeypatch.setattr("experiments.matrix.run_llm_experiments", fake_llm)
    monkeypatch.setattr("experiments.matrix.run_from_paths", fake_baselines)
    monkeypatch.setattr("decomposition.evaluation.runner.evaluate_all", fake_evaluate)

    manifest = run_matrix(
        repo_root=repo,
        config_path=repo / "experiments" / "configs" / "matrix.yaml",
        skip_extract=True,
        runs_root=tmp_path / "runs",
        only_ids=["C"],
    )
    assert models == ["gemini-2.5-flash"]
    by_name = {step["name"]: step for step in manifest["steps"]}
    assert by_name["llm-A"]["status"] == "skipped"
    assert by_name["llm-B"]["status"] == "skipped"
    assert by_name["llm-C"]["status"] == "ok"


def test_reuse_copies_only_scientific_llm_dirs(tmp_path: Path) -> None:
    from experiments.matrix import _reuse_llm_runs

    src = tmp_path / "old" / "decompositions"
    good = src / "gpt-4o-mini" / "C0" / "run_01"
    bad = src / "gemini-2.0-flash" / "C0" / "run_01"
    good.mkdir(parents=True)
    bad.mkdir(parents=True)
    (good / "metadata.json").write_text(
        json.dumps({"is_scientific_run": True, "model": "gpt-4o-mini"}) + "\n",
        encoding="utf-8",
    )
    (bad / "metadata.json").write_text(
        json.dumps({"is_scientific_run": False, "model": "gemini-2.0-flash"}) + "\n",
        encoding="utf-8",
    )
    copied = _reuse_llm_runs(tmp_path / "old", tmp_path / "new" / "decompositions")
    assert copied == ["gpt-4o-mini"]
    assert (tmp_path / "new" / "decompositions" / "gpt-4o-mini").exists()
    assert not (tmp_path / "new" / "decompositions" / "gemini-2.0-flash").exists()


def test_matrix_generators_do_not_import_gold() -> None:
    matrix_src = (ROOT / "experiments" / "matrix.py").read_text(encoding="utf-8")
    assert FORBIDDEN_GOLD in matrix_src
    extract_fn = _function_source(matrix_src, "_prepare_evidence")
    baselines_fn = _function_source(matrix_src, "_run_baselines")
    llm_fn = _function_source(matrix_src, "_run_llm_slots")
    evaluate_fn = _function_source(matrix_src, "_run_evaluate")
    assert FORBIDDEN_GOLD not in extract_fn
    assert FORBIDDEN_GOLD not in baselines_fn
    assert FORBIDDEN_GOLD not in llm_fn
    assert FORBIDDEN_GOLD in evaluate_fn


def test_run_all_module_exists() -> None:
    from experiments.run_all import parse_args

    assert parse_args.__name__ == "parse_args"


def test_matrix_real_extract_baselines_evaluate_skips_llm(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    monkeypatch.delenv("SEMS_ENABLE_OLLAMA", raising=False)
    manifest = run_matrix(
        repo_root=ROOT,
        config_path=ROOT / "experiments" / "configs" / "matrix.yaml",
        skip_llm=True,
        runs_root=tmp_path,
    )
    names = {step["name"]: step["status"] for step in manifest["steps"]}
    assert names["extract-evidence"] == "ok"
    assert names["baselines"] == "ok"
    assert names["evaluate"] == "ok"
    assert names["llm-A"] == "skipped"
    assert names["llm-B"] == "skipped"
    assert names["llm-C"] == "skipped"
    run_dir = Path(manifest["run_dir"])
    assert (run_dir / "metrics" / "table_a.md").exists()
    assert (run_dir / "decompositions" / "rule_based.json").exists()
    assert manifest["llm_outputs_fabricated"] is False
    assert manifest["gold_used_for_evaluation_only"] is True


def _function_source(module_src: str, name: str) -> str:
    marker = f"def {name}("
    start = module_src.index(marker)
    body = [module_src[start:].splitlines()[0]]
    for line in module_src[start:].splitlines()[1:]:
        if line.startswith("def "):
            break
        body.append(line)
    return "\n".join(body)


def _stub_repo(root: Path) -> Path:
    (root / "experiments" / "configs").mkdir(parents=True)
    (root / "outputs" / "evidence").mkdir(parents=True)
    (root / "reference").mkdir(parents=True)
    (root / "experiments" / "configs" / "matrix.yaml").write_text(
        (ROOT / "experiments" / "configs" / "matrix.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (root / "experiments" / "configs" / "baselines.yaml").write_text(
        (ROOT / "experiments" / "configs" / "baselines.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (root / "outputs" / "evidence" / "architectural_evidence.json").write_text(
        json.dumps(
            {
                "system": {
                    "name": "SEMS-R",
                    "is_original_sems_source": False,
                    "evidence_sources": {"historical_gold_labels": False},
                },
                "components": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "reference" / "historical_architecture.json").write_text("{}\n", encoding="utf-8")
    return root
