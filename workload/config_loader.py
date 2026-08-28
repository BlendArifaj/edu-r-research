from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent
CONFIG_DIR = ROOT / "config"

DEFAULT_MIX = {
    "student_dashboard": 35,
    "grades": 20,
    "registration": 15,
    "finance": 10,
    "attendance": 10,
    "library": 5,
    "faculty_admin": 5,
}

JOURNEY_NAMES = tuple(DEFAULT_MIX.keys())


@dataclass(frozen=True)
class WorkloadConfig:
    name: str
    users: int
    spawn_rate: float
    duration: str
    wait_min_s: float
    wait_max_s: float
    mix: dict[str, int]
    host: str
    saturation: dict[str, Any]
    integrity: str
    note: str


def load_config(name_or_path: str) -> WorkloadConfig:
    path = Path(name_or_path)
    if not path.suffix:
        path = CONFIG_DIR / f"{name_or_path}.yaml"
    elif not path.exists():
        path = CONFIG_DIR / path.name
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    mix = {**DEFAULT_MIX, **(raw.get("mix") or {})}
    if sum(mix.values()) != 100:
        raise ValueError(f"workload mix must sum to 100, got {sum(mix.values())} in {path}")
    return WorkloadConfig(
        name=str(raw.get("name", path.stem)),
        users=int(raw["users"]),
        spawn_rate=float(raw.get("spawn_rate", raw["users"])),
        duration=str(raw["duration"]),
        wait_min_s=float(raw.get("wait_min_s", 0.05)),
        wait_max_s=float(raw.get("wait_max_s", 0.3)),
        mix={key: int(mix[key]) for key in JOURNEY_NAMES},
        host=str(raw.get("host", "http://127.0.0.1:8000")),
        saturation=dict(raw.get("saturation") or {}),
        integrity=str(
            raw.get(
                "integrity",
                "synthetic_experimental_workload_not_production_sems",
            )
        ),
        note=str(raw.get("note", "")),
    )


def list_config_names() -> list[str]:
    return sorted(path.stem for path in CONFIG_DIR.glob("*.yaml"))
