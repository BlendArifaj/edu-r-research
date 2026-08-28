from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from decomposition.extraction.evidence_builder import FORBIDDEN_GOLD
from decomposition.llm import CONDITIONS
from decomposition.llm.convert import proposal_to_decomposition
from decomposition.llm.parse import format_validation_error, parse_proposal
from decomposition.llm.prompts import build_prompt
from decomposition.llm.providers import LLMProvider, MissingCredentialsError, get_provider


def run_llm_experiments(
    *,
    evidence: dict[str, Any],
    provider: LLMProvider,
    model: str,
    conditions: list[str],
    runs: int,
    temperature: float,
    max_retries: int,
    out_dir: Path,
    scientific: bool,
) -> list[dict[str, Any]]:
    if FORBIDDEN_GOLD in json.dumps({k: evidence.get(k) for k in ("system", "domain_descriptions")}):
        raise RuntimeError("refusing evidence that looks like evaluation gold")
    results = []
    for condition in conditions:
        prompt = build_prompt(condition, evidence)
        if FORBIDDEN_GOLD in prompt:
            raise RuntimeError("prompt accidentally contains evaluation gold filename")
        for run_number in range(1, runs + 1):
            results.append(
                _run_one(
                    provider=provider,
                    model=model,
                    condition=condition,
                    run_number=run_number,
                    prompt=prompt,
                    temperature=temperature,
                    max_retries=max_retries,
                    out_dir=out_dir,
                    scientific=scientific,
                )
            )
    return results


def _run_one(
    *,
    provider: LLMProvider,
    model: str,
    condition: str,
    run_number: int,
    prompt: str,
    temperature: float,
    max_retries: int,
    out_dir: Path,
    scientific: bool,
) -> dict[str, Any]:
    run_dir = out_dir / _safe(model) / condition / f"run_{run_number:02d}"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
    messages = [prompt]
    raw = ""
    parsed = None
    error = None
    attempts = 0
    for attempt in range(max_retries + 1):
        attempts = attempt + 1
        try:
            raw = provider.generate(messages[-1], model=model, temperature=temperature)
            parsed = parse_proposal(raw)
            error = None
            break
        except MissingCredentialsError:
            raise
        except Exception as exc:
            error = format_validation_error(exc)
            excerpt = raw[:2000] if raw else "(empty)"
            messages.append(
                prompt
                + "\n\nPrevious output:\n"
                + excerpt
                + "\n\nYour previous output was invalid JSON for the required schema:\n"
                + error
                + "\nReturn a corrected JSON object only."
            )
    (run_dir / "raw_response.txt").write_text(raw, encoding="utf-8")
    metadata = {
        "model": model,
        "provider": getattr(provider, "name", type(provider).__name__),
        "temperature": temperature,
        "timestamp": datetime.now(UTC).isoformat(),
        "condition": condition,
        "run_number": run_number,
        "retries_used": max(attempts - 1, 0),
        "parse_ok": parsed is not None,
        "is_scientific_run": scientific and parsed is not None,
        "is_original_sems_source": False,
        "gold_labels_in_prompt": False,
        "error": error,
    }
    (run_dir / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    if parsed is None:
        (run_dir / "parsed.json").write_text("null\n", encoding="utf-8")
        return metadata
    method = f"llm_{_safe(model)}_{condition}"
    decomposition = proposal_to_decomposition(parsed, method=method, metadata=metadata)
    (run_dir / "parsed.json").write_text(json.dumps(decomposition, indent=2) + "\n", encoding="utf-8")
    return metadata


def load_config(path: Path | None) -> dict[str, Any]:
    defaults = {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "temperature": 0.2,
        "runs": 3,
        "conditions": list(CONDITIONS),
        "max_retries": 2,
    }
    if path is None or not path.exists():
        return defaults
    text = path.read_text(encoding="utf-8")
    if path.suffix in {".yaml", ".yml"}:
        import yaml

        loaded = yaml.safe_load(text) or {}
    else:
        loaded = json.loads(text)
    if not isinstance(loaded, dict):
        raise ValueError("llm config must be a mapping")
    defaults.update(loaded)
    defaults["conditions"] = [str(item) for item in defaults["conditions"]]
    return defaults


def _safe(name: str) -> str:
    return name.replace("/", "-").replace(" ", "_")
