from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_WEIGHTS = {"alpha": 1.0, "beta": 1.0, "gamma": 1.0}


@dataclass(frozen=True)
class BaselineConfig:
    """Un-tuned defaults. Do not fit these weights on the reference architecture."""

    seed: int = 42
    louvain_resolution: float = 1.0
    alpha: float = 1.0
    beta: float = 1.0
    gamma: float = 1.0
    normalize_layers: bool = True
    identity_tokens: tuple[str, ...] = ("auth", "user")
    drop_suffixes: tuple[str, ...] = ("service", "repository", "builder")

    def as_dict(self) -> dict[str, Any]:
        return {
            "seed": self.seed,
            "louvain_resolution": self.louvain_resolution,
            "combined_weights": {"alpha": self.alpha, "beta": self.beta, "gamma": self.gamma},
            "normalize_layers": self.normalize_layers,
            "identity_tokens": list(self.identity_tokens),
            "weights_tuned_on_gold": False,
        }


def load_config(path: Path | None) -> BaselineConfig:
    if path is None or not path.exists():
        return BaselineConfig()
    payload = _read_mapping(path)
    weights = payload.get("combined_weights") or {}
    identity = payload.get("identity_tokens") or ("auth", "user")
    return BaselineConfig(
        seed=int(payload.get("seed", 42)),
        louvain_resolution=float(payload.get("louvain_resolution", 1.0)),
        alpha=float(weights.get("alpha", DEFAULT_WEIGHTS["alpha"])),
        beta=float(weights.get("beta", DEFAULT_WEIGHTS["beta"])),
        gamma=float(weights.get("gamma", DEFAULT_WEIGHTS["gamma"])),
        normalize_layers=bool(payload.get("normalize_layers", True)),
        identity_tokens=tuple(str(token).lower() for token in identity),
    )


def _read_mapping(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix in {".yaml", ".yml"}:
        import yaml

        loaded = yaml.safe_load(text) or {}
        if not isinstance(loaded, dict):
            raise ValueError(f"baseline config must be a mapping: {path}")
        return loaded
    import json

    loaded = json.loads(text)
    if not isinstance(loaded, dict):
        raise ValueError(f"baseline config must be a mapping: {path}")
    return loaded
