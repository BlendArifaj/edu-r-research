from __future__ import annotations

from pathlib import Path

from analysis.narrative import build_paper_markdown
from analysis.report import generate_report

ANALYSIS_ROOT = Path(__file__).resolve().parents[1]


def test_report_from_fixture_csvs(tmp_path: Path) -> None:
    run_dir = _stub_run(tmp_path / "run")
    out_dir = tmp_path / "report"
    paper_path = generate_report(run_dir, out_dir)
    text = paper_path.read_text(encoding="utf-8")
    assert "SEMS-R" in text
    assert "not** the original production SEMS source" in text
    assert "0.9245" in text
    assert "0.9068" in text
    assert "rule_based" in text
    assert (out_dir / "figures" / "table_a_pairwise_f1.svg").exists()
    assert (out_dir / "figures" / "table_b_pairwise_f1.svg").exists()
    assert (out_dir / "tables" / "table_a.csv").exists()
    assert "historical_architecture.json" in text
    assert "They do **not** read `reference/historical_architecture.json`" in text


def test_missing_table_b_is_honest(tmp_path: Path) -> None:
    run_dir = _stub_run(tmp_path / "run", include_table_b=False)
    text = generate_report(run_dir, tmp_path / "report").read_text(encoding="utf-8")
    assert "not invented" in text.lower()
    assert "RQ2 is unanswered" in text or "Table B is missing" in text


def test_expert_ranks_stay_blank(tmp_path: Path) -> None:
    run_dir = _stub_run(tmp_path / "run")
    text = generate_report(run_dir, tmp_path / "report").read_text(encoding="utf-8")
    assert "Expert ranks blank: True" in text
    assert "not filled with guesses" in text
    table_d = (tmp_path / "report" / "tables" / "table_d.csv").read_text(encoding="utf-8")
    assert "student,1,," in table_d or "student,1,,," in table_d


def test_analysis_sources_do_not_load_gold() -> None:
    for path in ANALYSIS_ROOT.rglob("*.py"):
        if path.name == "test_report.py":
            continue
        body = path.read_text(encoding="utf-8")
        assert "load_gold" not in body
        assert "from decomposition.evaluation.gold" not in body


def test_c0_stronger_than_c1_is_stated(tmp_path: Path) -> None:
    tables = {
        "table_a": [{"method": "rule_based", "pairwise_f1": "0.9"}],
        "table_b": [
            {
                "model": "gpt-4o-mini",
                "condition": "C0",
                "n_runs": "3",
                "pairwise_f1": "0.82",
                "rule_compliance": "0.8",
                "stability": "1.0",
                "uncertain_decisions": "0",
                "unsupported_assumptions": "0",
            },
            {
                "model": "gpt-4o-mini",
                "condition": "C1",
                "n_runs": "3",
                "pairwise_f1": "0.73",
                "rule_compliance": "0.8",
                "stability": "1.0",
                "uncertain_decisions": "0",
                "unsupported_assumptions": "0",
            },
        ],
        "table_c": [{"evidence": "runtime", "pairwise_f1": "0.36"}],
        "table_d": [],
    }
    text = build_paper_markdown(run_id="fixture", manifest={}, tables=tables)
    assert "C0 has the highest pairwise F1" in text
    assert "did not improve" in text
    assert "Phase 10 equal-resource" in text
    assert "10k requests/s" not in text


def test_phase10_uses_measured_rows() -> None:
    tables = {
        "table_a": [],
        "table_b": [],
        "table_c": [],
        "table_d": [],
    }
    phase10 = [
        {
            "mode": "A",
            "architecture": "monolith",
            "config": "high",
            "users": "100",
            "request_count": "68962",
            "failure_count": "101",
            "median_ms": "110",
            "p95_ms": "210",
            "p99_ms": "290",
            "rps": "230.7441",
            "equal_total": "true",
            "stamp": "2026-08-27_204815",
            "budget": "4 CPU / 4 GB",
        },
        {
            "mode": "A",
            "architecture": "microservices",
            "config": "high",
            "users": "100",
            "request_count": "11402",
            "failure_count": "196",
            "median_ms": "570",
            "p95_ms": "30000",
            "p99_ms": "30000",
            "rps": "39.5019",
            "equal_total": "true",
            "stamp": "2026-08-27_204815",
            "budget": "4 CPU / 4 GB",
        },
        {
            "mode": "E",
            "architecture": "monolith",
            "config": "high",
            "users": "100",
            "request_count": "60048",
            "failure_count": "66",
            "median_ms": "140",
            "p95_ms": "270",
            "p99_ms": "390",
            "rps": "201.3468",
            "equal_total": "true",
            "stamp": "2026-08-27_225302",
            "budget": "4 CPU / 4 GB",
        },
        {
            "mode": "E",
            "architecture": "clustered",
            "config": "high",
            "users": "100",
            "request_count": "23000",
            "failure_count": "4",
            "median_ms": "1200",
            "p95_ms": "2500",
            "p99_ms": "3100",
            "rps": "76.9368",
            "equal_total": "true",
            "stamp": "2026-08-27_225302",
            "budget": "4 CPU / 4 GB",
        },
    ]
    text = build_paper_markdown(
        run_id="fixture", manifest={}, tables=tables, phase10=phase10
    )
    assert "76.9368" in text
    assert "3100" in text
    assert "does not exceed the monolith" in text
    assert "66 failed requests" in text
    assert "4 failed requests" in text
    assert "not 10k requests/s" in text
    assert "30000" not in text
    assert "196" not in text
    assert "Phase 9 — historical six-service materialization" in text
    assert "six-service materialization and API gateway are not done" not in text


def test_report_copies_measured_phase10_tables(tmp_path: Path) -> None:
    run_dir = _stub_run(tmp_path / "run")
    out_dir = tmp_path / "report"
    text = generate_report(run_dir, out_dir).read_text(encoding="utf-8")
    assert "2026-08-27_225302" in text
    assert "clustered" in text
    assert (out_dir / "tables" / "load" / "2026-08-27_225302_comparison.csv").exists()
    assert "10k requests/s" in text
    assert "not 10k requests/s" in text


def _stub_run(path: Path, *, include_table_b: bool = True) -> Path:
    metrics = path / "metrics"
    metrics.mkdir(parents=True)
    (path / "manifest.json").write_text(
        '{"run_id":"fixture","is_original_sems_source":false,'
        '"gold_used_for_evaluation_only":true,"llm_outputs_fabricated":false}\n',
        encoding="utf-8",
    )
    (metrics / "table_a.csv").write_text(
        "method,n_services,pairwise_precision,pairwise_recall,pairwise_f1,ari,nmi,"
        "cross_service_coupling,db_ownership_conflicts,cycles\n"
        "rule_based,8,1.0,0.8596,0.9245,0.9067,0.9606,0.6327,0,1\n",
        encoding="utf-8",
    )
    if include_table_b:
        (metrics / "table_b.csv").write_text(
            "model,condition,n_runs,pairwise_f1,rule_compliance,stability,"
            "uncertain_decisions,unsupported_assumptions\n"
            "gemini-2.5-flash,C0,3,0.9068,1.0,0.9649,2,1.3333\n"
            "gemini-2.5-flash,C1,3,0.8152,1.0,0.9438,1.6667,0.6667\n",
            encoding="utf-8",
        )
    (metrics / "table_c.csv").write_text(
        "evidence,method,pairwise_f1,modularity,cross_service_coupling\n"
        "runtime,runtime_only,0.368,0.2022,0.5102\n",
        encoding="utf-8",
    )
    (metrics / "table_d.csv").write_text(
        "service,rule_based_rank,llm_rank,expert_rank,historical_rank\n"
        "student,1,,,\n",
        encoding="utf-8",
    )
    return path


def test_rq1_reports_n_architects() -> None:
    tables = {
        "table_a": [],
        "table_b": [
            {
                "model": "gpt-4o-mini",
                "condition": "C0",
                "pairwise_f1": "0.82",
            }
        ],
        "table_c": [],
        "table_d": [],
    }
    expert = {
        "reviewer_ids": ["exp1", "exp2", "exp3"],
        "vs_gold": {
            "exp1": {"f1": 0.89, "precision": 0.9, "recall": 0.8},
            "exp2": {"f1": 0.87, "precision": 0.88, "recall": 0.8},
            "exp3": {"f1": 0.86, "precision": 0.87, "recall": 0.8},
            "llm": {"f1": 0.92},
        },
        "agreement": {
            "n_reviewers": 3,
            "mean_pairwise_kappa": 0.8,
            "min_pairwise_kappa": 0.7,
            "max_pairwise_kappa": 0.9,
            "expert_pairs": {
                "exp1_vs_exp2": {"n_diff": 18, "kappa": 0.8},
                "exp1_vs_exp3": {"n_diff": 10, "kappa": 0.7},
                "exp2_vs_exp3": {"n_diff": 1, "kappa": 0.9},
            },
            "vs_llm": {
                "exp1": {"n_diff": 9},
                "exp2": {"n_diff": 9},
                "exp3": {"n_diff": 2},
            },
        },
    }
    text = build_paper_markdown(
        run_id="fixture", manifest={}, tables=tables, expert_pairwise=expert
    )
    assert "3 architects filled the 325-pair sheet" in text
    assert "Mean pairwise Cohen's kappa among 3 reviewers is 0.8" in text
    assert "Independent architect pairwise sheets: 3 reviewers scored" in text

