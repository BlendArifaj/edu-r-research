"""Mode A comparison helpers. No Docker required."""

from __future__ import annotations

import json
from pathlib import Path

from workload.compare_report import collect_runs, delta_rows, write_comparison
from workload.resources import (
    ROOT,
    assert_compose_matches_mode_a,
    assert_compose_matches_mode_b,
    assert_compose_matches_mode_c,
    assert_compose_matches_mode_d,
    assert_compose_matches_mode_e,
    assert_mode_a_totals,
    assert_mode_b_declared,
    assert_mode_c_declared,
    assert_mode_d_declared,
    assert_mode_e_declared,
    container_service_name,
    extras_vs_mode_a,
    load_mode_a,
    load_mode_b,
    load_mode_c,
    load_mode_d,
    load_mode_e,
    parse_compose_limits,
    profile_totals,
    replica_counts,
    scale_args,
)


def test_mode_a_totals_are_four_cpu_four_gb() -> None:
    mode_a = load_mode_a()
    assert_mode_a_totals(mode_a)
    for profile in ("monolith", "microservices"):
        cpus, memory_mb = profile_totals(mode_a, profile)
        assert cpus == 4.0
        assert memory_mb == 4096


def test_compose_matches_mode_a_yaml() -> None:
    assert_compose_matches_mode_a(load_mode_a())
    parsed = parse_compose_limits()
    assert parsed["microservices"]["gateway"]["cpus"] == 0.6
    assert parsed["microservices"]["gateway"]["memory_mb"] == 768
    assert parsed["monolith"]["monolith"]["memory_mb"] == 3072


def test_comparison_table_from_summaries(tmp_path: Path) -> None:
    _write_summary(tmp_path / "monolith" / "smoke", "monolith", "smoke", p95=10.0, rps=100.0)
    _write_summary(
        tmp_path / "microservices" / "smoke",
        "microservices",
        "smoke",
        p95=16.0,
        rps=90.0,
    )
    tables = write_comparison(tmp_path)
    assert tables["runs"][0]["architecture"] == "monolith"
    assert tables["runs"][1]["architecture"] == "microservices"
    delta = tables["deltas"][0]
    assert delta["config"] == "smoke"
    assert delta["p95_ms"] == 6.0
    assert delta["rps"] == -10.0
    assert (tmp_path / "comparison.md").exists()
    assert (tmp_path / "p95.svg").exists()
    markdown = (tmp_path / "comparison.md").read_text(encoding="utf-8")
    assert "Not production SEMS" in markdown
    assert "microservices" in markdown


def test_collect_runs_missing_pair_skips_delta(tmp_path: Path) -> None:
    _write_summary(tmp_path / "monolith" / "low", "monolith", "low", p95=20.0, rps=50.0)
    runs = collect_runs(tmp_path)
    assert delta_rows(runs) == []


def test_mode_a_yaml_lives_in_experiments() -> None:
    assert (ROOT / "experiments" / "configs" / "mode_a.yaml").is_file()


def test_mode_b_declares_gateway_and_student_extras() -> None:
    mode_a = load_mode_a()
    mode_b = load_mode_b()
    assert_mode_b_declared(mode_b, mode_a)
    extras = extras_vs_mode_a(mode_b, mode_a)
    assert extras["gateway"]["cpus"] == 0.6
    assert extras["gateway"]["memory_mb"] == 768
    assert extras["student"]["cpus"] == 0.4
    assert extras["student"]["memory_mb"] == 384
    cpus, memory_mb = profile_totals(mode_b, "microservices")
    assert cpus == 5.0
    assert memory_mb == 5248
    assert_compose_matches_mode_b(mode_b)


def test_mode_c_declares_replicas_and_nginx() -> None:
    mode_a = load_mode_a()
    mode_c = load_mode_c()
    assert_mode_c_declared(mode_c, mode_a)
    assert_compose_matches_mode_c(mode_c)
    extras = extras_vs_mode_a(mode_c, mode_a)
    assert extras["nginx"]["cpus"] == 0.25
    assert extras["gateway"]["cpus"] == 0.6
    assert extras["student"]["cpus"] == 0.4
    cpus, memory_mb = profile_totals(mode_c, "microservices")
    assert cpus == 7.25
    assert memory_mb == 7296
    assert replica_counts(mode_c)["student"] == 2
    assert replica_counts(mode_c)["nginx"] == 1
    assert "--scale" in scale_args(mode_c)
    assert "student=2" in scale_args(mode_c)
    assert container_service_name("sems-research-student-2") == "student"
    assert container_service_name("sems-research-gateway-1") == "gateway"
    assert (ROOT / "workload" / "nginx" / "mode-c.conf").is_file()
    assert (ROOT / "docker-compose.mode-c.yml").is_file()


def test_mode_d_starves_monolith_and_gives_sixteen_gb() -> None:
    mode_a = load_mode_a()
    mode_d = load_mode_d()
    assert_mode_d_declared(mode_d, mode_a)
    assert_compose_matches_mode_d(mode_d)
    extras = extras_vs_mode_a(mode_d, mode_a)
    assert extras["postgres-microservices"]["memory_mb"] == 3072
    assert extras["nginx"]["cpus"] == 0.4
    cpus_mono, mem_mono = profile_totals(mode_d, "monolith")
    cpus_ms, mem_ms = profile_totals(mode_d, "microservices")
    assert cpus_mono == 1.5
    assert mem_mono == 2048
    assert cpus_ms == 10.0
    assert mem_ms == 16384
    assert replica_counts(mode_d)["student"] == 2
    assert "student=2" in scale_args(mode_d)
    assert (ROOT / "docker-compose.mode-d.yml").is_file()


def test_mode_e_equal_total_clustered_campus() -> None:
    mode_a = load_mode_a()
    mode_e = load_mode_e()
    assert_mode_e_declared(mode_e, mode_a)
    assert_compose_matches_mode_e(mode_e)
    for profile in ("monolith", "clustered"):
        cpus, memory_mb = profile_totals(mode_e, profile)
        assert cpus == 4.0
        assert memory_mb == 4096
    assert mode_e["architectures"] == ["monolith", "clustered"]
    assert "campus" in mode_e["profiles"]["clustered"]
    assert "library-clustered" in mode_e["profiles"]["clustered"]
    assert "gateway" not in mode_e["profiles"]["clustered"]
    assert (ROOT / "docker-compose.mode-e.yml").is_file()


def test_clustered_comparison_delta(tmp_path: Path) -> None:
    _write_summary(tmp_path / "monolith" / "high", "monolith", "high", p95=20.0, rps=100.0)
    _write_summary(tmp_path / "clustered" / "high", "clustered", "high", p95=30.0, rps=80.0)
    (tmp_path / "plan.json").write_text('{"mode": "E"}\n', encoding="utf-8")
    tables = write_comparison(tmp_path)
    assert tables["runs"][0]["architecture"] == "monolith"
    assert tables["runs"][1]["architecture"] == "clustered"
    delta = tables["deltas"][0]
    assert delta["delta"] == "clustered_minus_monolith"
    assert delta["p95_ms"] == 10.0
    assert delta["rps"] == -20.0
    markdown = (tmp_path / "comparison.md").read_text(encoding="utf-8")
    assert "Mode E" in markdown
    assert "clustered" in markdown
    assert "Not the historical six-service gold" in markdown


def _write_summary(
    directory: Path,
    architecture: str,
    config: str,
    *,
    p95: float,
    rps: float,
) -> None:
    directory.mkdir(parents=True)
    payload = {
        "architecture": architecture,
        "config": config,
        "users": 5,
        "duration": "60s",
        "locust_exit_code": 0,
        "stats": {
            "request_count": 100,
            "failure_count": 0,
            "median_ms": 5.0,
            "p95_ms": p95,
            "p99_ms": 30.0,
            "rps": rps,
        },
    }
    (directory / "summary.json").write_text(json.dumps(payload) + "\n", encoding="utf-8")
