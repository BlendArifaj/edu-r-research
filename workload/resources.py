"""Mode A resource budget. Compose limits must match experiments/configs/mode_a.yaml."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
MODE_A_PATH = ROOT / "experiments" / "configs" / "mode_a.yaml"
MODE_B_PATH = ROOT / "experiments" / "configs" / "mode_b.yaml"
MODE_C_PATH = ROOT / "experiments" / "configs" / "mode_c.yaml"
MODE_D_PATH = ROOT / "experiments" / "configs" / "mode_d.yaml"
MODE_E_PATH = ROOT / "experiments" / "configs" / "mode_e.yaml"
COMPOSE_PATH = ROOT / "docker-compose.yml"
COMPOSE_MODE_B_PATH = ROOT / "docker-compose.mode-b.yml"
COMPOSE_MODE_C_PATH = ROOT / "docker-compose.mode-c.yml"
COMPOSE_MODE_D_PATH = ROOT / "docker-compose.mode-d.yml"
COMPOSE_MODE_E_PATH = ROOT / "docker-compose.mode-e.yml"
OTHER_PROFILE = {"monolith": "microservices", "microservices": "monolith", "clustered": "monolith"}
ALL_PROFILES = ("monolith", "microservices", "clustered")
APP_REPLICA_SERVICES = (
    "gateway",
    "faculty",
    "student",
    "grade",
    "finance",
    "attendance",
    "library",
    "campus",
    "library-clustered",
)


def load_mode_a(path: Path | None = None) -> dict[str, Any]:
    target = path or MODE_A_PATH
    raw = yaml.safe_load(target.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Mode A config is not a mapping: {target}")
    return raw


def memory_to_mb(value: str) -> int:
    text = str(value).strip().upper()
    if text.endswith("GIB") or text.endswith("GB"):
        return int(float(text[:-2]) * 1024)
    if text.endswith("MIB") or text.endswith("MB"):
        return int(float(text[:-2]))
    if text.endswith("G"):
        return int(float(text[:-1]) * 1024)
    if text.endswith("M"):
        return int(float(text[:-1]))
    return int(round(int(text) / (1024 * 1024)))


def service_scaled(item: dict[str, Any]) -> tuple[float, int]:
    replicas = int(item.get("replicas", 1))
    return float(item["cpus"]) * replicas, int(item["memory_mb"]) * replicas


def profile_totals(mode_a: dict[str, Any], profile: str) -> tuple[float, int]:
    services = mode_a["profiles"][profile]
    cpus = 0.0
    memory_mb = 0
    for item in services.values():
        service_cpus, service_memory = service_scaled(item)
        cpus += service_cpus
        memory_mb += service_memory
    return round(cpus, 4), memory_mb


def assert_mode_a_totals(mode_a: dict[str, Any]) -> None:
    expected_cpus = float(mode_a["total_cpus"])
    expected_memory = int(mode_a["total_memory_mb"])
    for profile in mode_a["profiles"]:
        cpus, memory_mb = profile_totals(mode_a, profile)
        if abs(cpus - expected_cpus) > 1e-6:
            raise ValueError(f"{profile} CPU total {cpus} != {expected_cpus}")
        if memory_mb != expected_memory:
            raise ValueError(f"{profile} memory {memory_mb} MB != {expected_memory} MB")


def parse_compose_limits(
    compose_path: Path | None = None,
) -> dict[str, dict[str, dict[str, float | int]]]:
    raw = yaml.safe_load((compose_path or COMPOSE_PATH).read_text(encoding="utf-8"))
    by_profile: dict[str, dict[str, dict[str, float | int]]] = {}
    for name, service in raw.get("services", {}).items():
        limits = ((service.get("deploy") or {}).get("resources") or {}).get("limits") or {}
        if "cpus" not in limits or "memory" not in limits:
            continue
        entry = {
            "cpus": float(limits["cpus"]),
            "memory_mb": memory_to_mb(str(limits["memory"])),
        }
        for profile in service.get("profiles") or []:
            by_profile.setdefault(profile, {})[name] = entry
    return by_profile


def load_mode_b(path: Path | None = None) -> dict[str, Any]:
    target = path or MODE_B_PATH
    raw = yaml.safe_load(target.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Mode B config is not a mapping: {target}")
    return raw


def extras_vs_mode_a(mode: dict[str, Any], mode_a: dict[str, Any]) -> dict[str, dict[str, float]]:
    extras: dict[str, dict[str, float]] = {}
    baseline_profile = mode_a["profiles"]["microservices"]
    for name, budget in mode["profiles"]["microservices"].items():
        got_cpus, got_memory = service_scaled(budget)
        if name in baseline_profile:
            base_cpus, base_memory = service_scaled(baseline_profile[name])
            delta_cpus = got_cpus - base_cpus
            delta_memory = got_memory - base_memory
        else:
            delta_cpus, delta_memory = got_cpus, got_memory
        if abs(delta_cpus) > 1e-6 or delta_memory != 0:
            extras[name] = {"cpus": delta_cpus, "memory_mb": float(delta_memory)}
    return extras


def assert_mode_b_declared(mode_b: dict[str, Any], mode_a: dict[str, Any]) -> None:
    cpus_mono, mem_mono = profile_totals(mode_b, "monolith")
    cpus_ms, mem_ms = profile_totals(mode_b, "microservices")
    if abs(cpus_mono - float(mode_b["total_cpus"]["monolith"])) > 1e-6:
        raise ValueError("Mode B monolith CPU total mismatch")
    if mem_mono != int(mode_b["total_memory_mb"]["monolith"]):
        raise ValueError("Mode B monolith memory total mismatch")
    if abs(cpus_ms - float(mode_b["total_cpus"]["microservices"])) > 1e-6:
        raise ValueError("Mode B microservices CPU total mismatch")
    if mem_ms != int(mode_b["total_memory_mb"]["microservices"]):
        raise ValueError("Mode B microservices memory total mismatch")
    extras = extras_vs_mode_a(mode_b, mode_a)
    declared = {
        name: {"cpus": float(item["cpus"]), "memory_mb": float(item["memory_mb"])}
        for name, item in (mode_b.get("extra_vs_mode_a") or {}).items()
    }
    if extras != declared:
        raise ValueError(f"Mode B extras {extras} != declared {declared}")


def parse_service_limits(compose_path: Path) -> dict[str, dict[str, float | int]]:
    text = compose_path.read_text(encoding="utf-8")
    for tag in ("!reset ", "!override "):
        text = text.replace(tag, "")
    raw = yaml.safe_load(text)
    out: dict[str, dict[str, float | int]] = {}
    for name, service in (raw.get("services") or {}).items():
        limits = ((service.get("deploy") or {}).get("resources") or {}).get("limits") or {}
        if "cpus" not in limits or "memory" not in limits:
            continue
        out[name] = {
            "cpus": float(limits["cpus"]),
            "memory_mb": memory_to_mb(str(limits["memory"])),
        }
    return out


def assert_compose_matches_mode_b(mode_b: dict[str, Any]) -> None:
    parsed = parse_compose_limits()
    overlay = parse_service_limits(COMPOSE_MODE_B_PATH)
    parsed.setdefault("microservices", {}).update(overlay)
    for profile, services in mode_b["profiles"].items():
        if set(parsed[profile]) != set(services):
            raise ValueError(
                f"{profile} services {sorted(parsed[profile])} != {sorted(services)}"
            )
        for name, budget in services.items():
            got = parsed[profile][name]
            if abs(float(got["cpus"]) - float(budget["cpus"])) > 1e-6:
                raise ValueError(f"{name} cpus {got['cpus']} != {budget['cpus']}")
            if int(got["memory_mb"]) != int(budget["memory_mb"]):
                raise ValueError(f"{name} memory {got['memory_mb']} != {budget['memory_mb']}")


def load_mode_c(path: Path | None = None) -> dict[str, Any]:
    target = path or MODE_C_PATH
    raw = yaml.safe_load(target.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Mode C config is not a mapping: {target}")
    return raw


def load_mode_d(path: Path | None = None) -> dict[str, Any]:
    target = path or MODE_D_PATH
    raw = yaml.safe_load(target.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Mode D config is not a mapping: {target}")
    return raw


def load_mode_e(path: Path | None = None) -> dict[str, Any]:
    target = path or MODE_E_PATH
    raw = yaml.safe_load(target.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Mode E config is not a mapping: {target}")
    return raw


def profiles_to_stop(architecture: str) -> tuple[str, ...]:
    if architecture not in ALL_PROFILES:
        raise ValueError(f"unknown architecture {architecture}")
    return tuple(profile for profile in ALL_PROFILES if profile != architecture)


def replica_counts(mode: dict[str, Any], profile: str = "microservices") -> dict[str, int]:
    return {
        name: int(item.get("replicas", 1))
        for name, item in mode["profiles"][profile].items()
    }


def scale_args(mode: dict[str, Any]) -> list[str]:
    args: list[str] = []
    for name, count in replica_counts(mode).items():
        if count > 1:
            args.extend(["--scale", f"{name}={count}"])
    return args


def assert_mode_c_declared(mode_c: dict[str, Any], mode_a: dict[str, Any]) -> None:
    cpus_mono, mem_mono = profile_totals(mode_c, "monolith")
    cpus_ms, mem_ms = profile_totals(mode_c, "microservices")
    if abs(cpus_mono - float(mode_c["total_cpus"]["monolith"])) > 1e-6:
        raise ValueError("Mode C monolith CPU total mismatch")
    if mem_mono != int(mode_c["total_memory_mb"]["monolith"]):
        raise ValueError("Mode C monolith memory total mismatch")
    if abs(cpus_ms - float(mode_c["total_cpus"]["microservices"])) > 1e-6:
        raise ValueError("Mode C microservices CPU total mismatch")
    if mem_ms != int(mode_c["total_memory_mb"]["microservices"]):
        raise ValueError("Mode C microservices memory total mismatch")
    extras = extras_vs_mode_a(mode_c, mode_a)
    declared = {
        name: {"cpus": float(item["cpus"]), "memory_mb": float(item["memory_mb"])}
        for name, item in (mode_c.get("extra_vs_mode_a") or {}).items()
    }
    if extras != declared:
        raise ValueError(f"Mode C extras {extras} != declared {declared}")
    declared_replicas = {
        name: int(count) for name, count in (mode_c.get("replicas") or {}).items()
    }
    if replica_counts(mode_c) != declared_replicas:
        raise ValueError("Mode C replica map does not match profiles")


def docker_capacity() -> tuple[float, int]:
    raw = subprocess.check_output(["docker", "info", "--format", "{{json .}}"])
    info = json.loads(raw)
    cpus = float(info.get("NCPU") or 0)
    memory_mb = int((info.get("MemTotal") or 0) / (1024 * 1024))
    return cpus, memory_mb


def assert_docker_capacity(mode: dict[str, Any]) -> None:
    required = mode.get("docker_requires") or {}
    if not required:
        return
    need_cpus = float(required["cpus"])
    need_memory = int(required["memory_mb"])
    cpus, memory_mb = docker_capacity()
    if cpus + 1e-6 < need_cpus or memory_mb < need_memory:
        raise RuntimeError(
            f"Docker VM is {cpus} CPU / {memory_mb} MB; this mode needs "
            f">={need_cpus} CPU / >={need_memory} MB. Set Docker Desktop "
            "Resources to 10 CPUs and 18 GB so a 16 GB container budget is real."
        )


def assert_mode_d_declared(mode_d: dict[str, Any], mode_a: dict[str, Any]) -> None:
    cpus_mono, mem_mono = profile_totals(mode_d, "monolith")
    cpus_ms, mem_ms = profile_totals(mode_d, "microservices")
    if abs(cpus_mono - float(mode_d["total_cpus"]["monolith"])) > 1e-6:
        raise ValueError("Mode D monolith CPU total mismatch")
    if mem_mono != int(mode_d["total_memory_mb"]["monolith"]):
        raise ValueError("Mode D monolith memory total mismatch")
    if abs(cpus_ms - float(mode_d["total_cpus"]["microservices"])) > 1e-6:
        raise ValueError("Mode D microservices CPU total mismatch")
    if mem_ms != int(mode_d["total_memory_mb"]["microservices"]):
        raise ValueError("Mode D microservices memory total mismatch")
    extras = extras_vs_mode_a(mode_d, mode_a)
    declared = {
        name: {"cpus": float(item["cpus"]), "memory_mb": float(item["memory_mb"])}
        for name, item in (mode_d.get("extra_vs_mode_a") or {}).items()
    }
    if extras != declared:
        raise ValueError(f"Mode D extras {extras} != declared {declared}")
    declared_replicas = {
        name: int(count) for name, count in (mode_d.get("replicas") or {}).items()
    }
    if replica_counts(mode_d) != declared_replicas:
        raise ValueError("Mode D replica map does not match profiles")
    if mem_mono != 2048:
        raise ValueError("Mode D monolith must be 2 GB total")
    if mem_ms != 16384:
        raise ValueError("Mode D microservices must be 16 GB total")


def assert_compose_matches_mode_d(mode_d: dict[str, Any]) -> None:
    parsed = parse_compose_limits()
    overlay = parse_service_limits(COMPOSE_MODE_D_PATH)
    for profile, names in (
        ("monolith", mode_d["profiles"]["monolith"]),
        ("microservices", mode_d["profiles"]["microservices"]),
    ):
        parsed.setdefault(profile, {})
        for name in names:
            if name in overlay:
                parsed[profile][name] = overlay[name]
    for profile, services in mode_d["profiles"].items():
        if set(parsed[profile]) != set(services):
            raise ValueError(
                f"{profile} services {sorted(parsed[profile])} != {sorted(services)}"
            )
        for name, budget in services.items():
            got = parsed[profile][name]
            if abs(float(got["cpus"]) - float(budget["cpus"])) > 1e-6:
                raise ValueError(f"{name} cpus {got['cpus']} != {budget['cpus']}")
            if int(got["memory_mb"]) != int(budget["memory_mb"]):
                raise ValueError(f"{name} memory {got['memory_mb']} != {budget['memory_mb']}")


def assert_mode_e_declared(mode_e: dict[str, Any], mode_a: dict[str, Any]) -> None:
    expected_cpus = float(mode_e["total_cpus"])
    expected_memory = int(mode_e["total_memory_mb"])
    if abs(expected_cpus - float(mode_a["total_cpus"])) > 1e-6:
        raise ValueError("Mode E total CPU must match Mode A")
    if expected_memory != int(mode_a["total_memory_mb"]):
        raise ValueError("Mode E total memory must match Mode A")
    for profile in mode_e["profiles"]:
        cpus, memory_mb = profile_totals(mode_e, profile)
        if abs(cpus - expected_cpus) > 1e-6:
            raise ValueError(f"{profile} CPU total {cpus} != {expected_cpus}")
        if memory_mb != expected_memory:
            raise ValueError(f"{profile} memory {memory_mb} MB != {expected_memory} MB")
    if mode_e["profiles"]["monolith"] != mode_a["profiles"]["monolith"]:
        raise ValueError("Mode E monolith profile must match Mode A")
    if list(mode_e["architectures"]) != ["monolith", "clustered"]:
        raise ValueError("Mode E architectures must be monolith then clustered")


def assert_compose_matches_mode_e(mode_e: dict[str, Any]) -> None:
    parsed = parse_compose_limits()
    overlay = parse_compose_limits(COMPOSE_MODE_E_PATH)
    parsed["clustered"] = overlay.get("clustered", {})
    for profile, services in mode_e["profiles"].items():
        if set(parsed[profile]) != set(services):
            raise ValueError(
                f"{profile} services {sorted(parsed[profile])} != {sorted(services)}"
            )
        for name, budget in services.items():
            got = parsed[profile][name]
            if abs(float(got["cpus"]) - float(budget["cpus"])) > 1e-6:
                raise ValueError(f"{name} cpus {got['cpus']} != {budget['cpus']}")
            if int(got["memory_mb"]) != int(budget["memory_mb"]):
                raise ValueError(f"{name} memory {got['memory_mb']} != {budget['memory_mb']}")


def assert_compose_matches_mode_c(mode_c: dict[str, Any]) -> None:
    parsed = parse_compose_limits()
    overlay = parse_service_limits(COMPOSE_MODE_C_PATH)
    parsed.setdefault("microservices", {}).update(overlay)
    for profile, services in mode_c["profiles"].items():
        if set(parsed[profile]) != set(services):
            raise ValueError(
                f"{profile} services {sorted(parsed[profile])} != {sorted(services)}"
            )
        for name, budget in services.items():
            got = parsed[profile][name]
            if abs(float(got["cpus"]) - float(budget["cpus"])) > 1e-6:
                raise ValueError(f"{name} cpus {got['cpus']} != {budget['cpus']}")
            if int(got["memory_mb"]) != int(budget["memory_mb"]):
                raise ValueError(f"{name} memory {got['memory_mb']} != {budget['memory_mb']}")


def container_service_name(container_name: str) -> str | None:
    known = (
        *APP_REPLICA_SERVICES,
        "nginx",
        "postgres-microservices",
        "postgres-monolith",
        "postgres-clustered",
        "monolith",
    )
    for service in known:
        if container_name.endswith(f"-{service}-1") or f"-{service}-" in container_name + "-":
            suffix = container_name.rsplit(f"-{service}-", 1)
            if len(suffix) == 2 and suffix[1].isdigit():
                return service
    return None


def counted_replicas(limit_rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in limit_rows:
        service = container_service_name(str(row.get("name") or ""))
        if service:
            counts[service] = counts.get(service, 0) + 1
    return counts


def assert_compose_matches_mode_a(mode_a: dict[str, Any], compose_path: Path | None = None) -> None:
    parsed = parse_compose_limits(compose_path)
    for profile, services in mode_a["profiles"].items():
        if profile not in parsed:
            raise ValueError(f"compose has no services for profile {profile}")
        if set(parsed[profile]) != set(services):
            raise ValueError(
                f"{profile} services {sorted(parsed[profile])} != {sorted(services)}"
            )
        for name, budget in services.items():
            got = parsed[profile][name]
            if abs(float(got["cpus"]) - float(budget["cpus"])) > 1e-6:
                raise ValueError(f"{name} cpus {got['cpus']} != {budget['cpus']}")
            if int(got["memory_mb"]) != int(budget["memory_mb"]):
                raise ValueError(f"{name} memory {got['memory_mb']} != {budget['memory_mb']}")
