"""Mode A sequential Locust comparison: monolith vs gateway. Measured artifacts only."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from workload.compare_report import write_comparison
from workload.resources import (
    ROOT,
    assert_compose_matches_mode_a,
    assert_compose_matches_mode_b,
    assert_compose_matches_mode_c,
    assert_compose_matches_mode_d,
    assert_compose_matches_mode_e,
    assert_docker_capacity,
    assert_mode_a_totals,
    assert_mode_b_declared,
    assert_mode_c_declared,
    assert_mode_d_declared,
    assert_mode_e_declared,
    counted_replicas,
    extras_vs_mode_a,
    load_mode_a,
    load_mode_b,
    load_mode_c,
    load_mode_d,
    load_mode_e,
    profiles_to_stop,
    replica_counts,
    scale_args,
)

COMPOSE = ["docker", "compose"]
SCALE_MODES = frozenset({"C", "D"})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SEMS-R Locust comparison")
    parser.add_argument("--mode", choices=["A", "B", "C", "D", "E"], default="A")
    parser.add_argument("--mode-a", default="", help="path to mode_a.yaml")
    parser.add_argument("--mode-b", default="", help="path to mode_b.yaml")
    parser.add_argument("--mode-c", default="", help="path to mode_c.yaml")
    parser.add_argument("--mode-d", default="", help="path to mode_d.yaml")
    parser.add_argument("--mode-e", default="", help="path to mode_e.yaml")
    parser.add_argument("--configs", default="", help="comma-separated Locust configs")
    parser.add_argument("--seed-scale", default="", help="tiny or small")
    parser.add_argument("--outdir", default="", help="comparison artifact directory")
    parser.add_argument(
        "--skip-docker",
        action="store_true",
        help="rebuild tables from existing summaries",
    )
    parser.add_argument(
        "--from-summaries",
        default="",
        help="root with architecture/config/summary.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    mode_a = load_mode_a(Path(args.mode_a) if args.mode_a else None)
    assert_mode_a_totals(mode_a)
    mode_letter = args.mode
    budget = mode_a
    if mode_letter == "B":
        budget = load_mode_b(Path(args.mode_b) if args.mode_b else None)
        assert_mode_b_declared(budget, mode_a)
        if not args.skip_docker:
            assert_compose_matches_mode_b(budget)
    elif mode_letter == "C":
        budget = load_mode_c(Path(args.mode_c) if args.mode_c else None)
        assert_mode_c_declared(budget, mode_a)
        if not args.skip_docker:
            assert_compose_matches_mode_c(budget)
    elif mode_letter == "D":
        budget = load_mode_d(Path(args.mode_d) if args.mode_d else None)
        assert_mode_d_declared(budget, mode_a)
        if not args.skip_docker:
            assert_compose_matches_mode_d(budget)
            assert_docker_capacity(budget)
    elif mode_letter == "E":
        budget = load_mode_e(Path(args.mode_e) if args.mode_e else None)
        assert_mode_e_declared(budget, mode_a)
        if not args.skip_docker:
            assert_compose_matches_mode_e(budget)
    elif not args.skip_docker:
        assert_compose_matches_mode_a(mode_a)
    stamp = datetime.now(UTC).strftime("%Y-%m-%d_%H%M%S")
    default_out = ROOT / "outputs" / "performance" / "comparisons" / stamp
    outdir = Path(args.outdir) if args.outdir else default_out
    if args.from_summaries:
        source = Path(args.from_summaries)
        tables = write_comparison(source)
        print(f"Wrote comparison tables from {source}")
        print(json.dumps({"runs": len(tables["runs"]), "deltas": len(tables["deltas"])}))
        return
    outdir.mkdir(parents=True, exist_ok=True)
    configs = _csv(args.configs) or list(budget["configs"])
    seed_scale = args.seed_scale or str(budget["seed_scale"])
    base_url = str(budget["base_url"])
    extras = extras_vs_mode_a(budget, mode_a) if mode_letter in {"B", "C", "D"} else {}
    if mode_letter == "A":
        budget_note = "Mode A is equal-total."
    elif mode_letter == "B":
        budget_note = "Mode B is not equal-total; extras are declared."
    elif mode_letter == "C":
        budget_note = (
            "Mode C is not equal-total; nginx plus declared replicas. "
            "Not a production 10k-user replay."
        )
    elif mode_letter == "E":
        budget_note = (
            "Mode E is a dependency-clustered campus plus library, equal-total "
            "with Mode A. Not the historical six-service gold. "
            "Not a production 10k-user replay."
        )
    else:
        budget_note = (
            "Mode D is not equal-total; monolith 2 GB vs microservices 16 GB. "
            "Not a production 10k-user replay."
        )
    plan = {
        "integrity": "sems-r-reconstruction-measured",
        "mode": mode_letter,
        "note": (
            "Sequential exclusive Compose profiles. "
            "Locust is on the host, outside the container budget. "
            + budget_note
        ),
        "stamp": stamp,
        "configs": configs,
        "seed_scale": seed_scale,
        "base_url": base_url,
        "extra_vs_mode_a": extras,
        "replicas": replica_counts(budget, "microservices")
        if mode_letter in SCALE_MODES
        else {},
        "load_balancer": budget.get("load_balancer", ""),
        "docker_requires": budget.get("docker_requires") or {},
        "monolith_vs_mode_a": budget.get("monolith_vs_mode_a") or {},
        "total_cpus": budget.get("total_cpus"),
        "total_memory_mb": budget.get("total_memory_mb"),
        "profiles": budget["profiles"],
    }
    (outdir / "plan.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    if args.skip_docker:
        write_comparison(outdir)
        return
    inspections: dict[str, Any] = {}
    locust_failures: list[str] = []
    for architecture in budget["architectures"]:
        _bring_up(
            str(architecture),
            mode_letter,
            extra_up=scale_args(budget)
            if mode_letter in SCALE_MODES and architecture == "microservices"
            else None,
        )
        inspections[str(architecture)] = {
            "limits": _inspect_limits(str(architecture), mode_letter),
            "stats_before": _docker_stats(str(architecture), mode_letter),
        }
        if mode_letter in SCALE_MODES and architecture == "microservices":
            expected = {
                name: count
                for name, count in replica_counts(budget).items()
                if count > 1
            }
            observed = counted_replicas(inspections[str(architecture)]["limits"])
            missing = {
                name: count
                for name, count in expected.items()
                if observed.get(name) != count
            }
            if missing:
                raise RuntimeError(
                    f"Mode {mode_letter} replica counts {observed} missing {missing}"
                )
        _seed(str(architecture), seed_scale, base_url, str(budget["monolith_database_url"]))
        for config in configs:
            artifact = outdir / str(architecture) / config
            code = _run_load(config, base_url, str(architecture), artifact)
            if code != 0:
                locust_failures.append(f"{architecture}/{config} exit {code}")
        inspections[str(architecture)]["stats_after"] = _docker_stats(
            str(architecture), mode_letter
        )
        _compose(str(architecture), ["down", "-v"], mode_letter)
    (outdir / "resources_inspected.json").write_text(
        json.dumps(inspections, indent=2) + "\n", encoding="utf-8"
    )
    write_comparison(outdir)
    print(f"Wrote SEMS-R Mode {mode_letter} comparison to {outdir}")
    print("These are measurements of the experimental reconstruction, not production SEMS.")
    if locust_failures:
        raise SystemExit("Locust failures: " + "; ".join(locust_failures))


def _csv(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def _compose_base(profile: str, mode: str = "A") -> list[str]:
    command = [*COMPOSE, "-f", str(ROOT / "docker-compose.yml")]
    if mode == "B" and profile == "microservices":
        command += ["-f", str(ROOT / "docker-compose.mode-b.yml")]
    if mode == "C" and profile == "microservices":
        command += ["-f", str(ROOT / "docker-compose.mode-c.yml")]
    if mode == "D":
        command += ["-f", str(ROOT / "docker-compose.mode-d.yml")]
    if mode == "E" or profile == "clustered":
        command += ["-f", str(ROOT / "docker-compose.mode-e.yml")]
    command += ["--profile", profile]
    return command


def _compose(profile: str, extra: list[str], mode: str = "A") -> None:
    command = [*_compose_base(profile, mode), *extra]
    completed = subprocess.run(command, cwd=ROOT, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"{' '.join(command)} exited {completed.returncode}")


def _bring_up(
    architecture: str, mode: str = "A", extra_up: list[str] | None = None
) -> None:
    for other in profiles_to_stop(architecture):
        _compose(other, ["down"], mode)
    _compose(architecture, ["down", "-v"], mode)
    up = ["up", "--build", "-d"]
    if extra_up:
        up.extend(extra_up)
    if mode == "E":
        up += ["--wait", "--wait-timeout", "180"]
    _compose(architecture, up, mode)
    _wait_health("http://127.0.0.1:8000", attempts=180 if mode in SCALE_MODES or mode == "E" else 90)


def _wait_health(base_url: str, attempts: int = 90) -> None:
    last: BaseException | None = None
    for _ in range(attempts):
        try:
            response = httpx.get(f"{base_url.rstrip('/')}/health", timeout=2.0)
            if response.status_code == 200:
                return
            last = RuntimeError(f"health HTTP {response.status_code}")
        except httpx.HTTPError as exc:
            last = exc
        time.sleep(1)
    raise RuntimeError(f"API not healthy after {attempts}s: {last}")


def _seed(_architecture: str, scale: str, base_url: str, _monolith_db: str) -> None:
    command = [
        sys.executable,
        str(ROOT / "workload" / "seed_microservices.py"),
        "--scale",
        scale,
        "--base-url",
        base_url,
    ]
    completed = subprocess.run(command, cwd=ROOT, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"HTTP seed exited {completed.returncode}")


def _run_load(config: str, base_url: str, architecture: str, outdir: Path) -> int:
    command = [
        sys.executable,
        str(ROOT / "workload" / "run_load.py"),
        "--config",
        config,
        "--base-url",
        base_url,
        "--architecture",
        architecture,
        "--outdir",
        str(outdir),
    ]
    completed = subprocess.run(command, cwd=ROOT, check=False)
    return completed.returncode


def _inspect_limits(profile: str, mode: str = "A") -> list[dict[str, Any]]:
    ids = _compose_ids(profile, mode)
    if not ids:
        return []
    raw = subprocess.check_output(["docker", "inspect", *ids], cwd=ROOT)
    payload = json.loads(raw)
    rows = []
    for item in payload:
        host = item.get("HostConfig") or {}
        nano = int(host.get("NanoCpus") or 0)
        memory = int(host.get("Memory") or 0)
        rows.append(
            {
                "name": (item.get("Name") or "").lstrip("/"),
                "nano_cpus": nano,
                "cpus": nano / 1_000_000_000 if nano else 0.0,
                "memory_bytes": memory,
                "memory_mb": round(memory / (1024 * 1024), 3) if memory else 0.0,
                "limits_applied": nano > 0 and memory > 0,
            }
        )
    return rows


def _compose_ids(profile: str, mode: str = "A") -> list[str]:
    command = [*_compose_base(profile, mode), "ps", "-q"]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return []
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def _docker_stats(profile: str, mode: str = "A") -> list[dict[str, str]]:
    ids = _compose_ids(profile, mode)
    if not ids:
        return []
    completed = subprocess.run(
        ["docker", "stats", "--no-stream", "--format", "{{json .}}", *ids],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return [{"error": completed.stderr.strip()}]
    rows = []
    for line in completed.stdout.splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


if __name__ == "__main__":
    main()
