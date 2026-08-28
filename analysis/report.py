from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from analysis.figures import (
    write_ablation_f1_svg,
    write_baseline_f1_svg,
    write_llm_f1_svg,
    write_stability_svg,
)
from analysis.load import load_manifest, load_run_tables
from analysis.narrative import build_paper_markdown
from analysis.phase10 import comparison_dirs, load_phase10_rows
from decomposition.evaluation.expert_followup import apply_table_d_ranks, write_table_d

DEFAULT_RUN = Path("outputs/runs/2026-08-27_005")
REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_expert_pairwise(run_dir: Path) -> dict:
    path = run_dir / "expert_review" / "expert_pairwise_scores.json"
    payload: dict = {}
    if path.is_file():
        loaded = json.loads(path.read_text(encoding="utf-8"))
        payload = loaded if isinstance(loaded, dict) else {}
    followup_path = run_dir / "expert_review" / "expert_followup_scores.json"
    if followup_path.is_file():
        followup = json.loads(followup_path.read_text(encoding="utf-8"))
        if isinstance(followup, dict):
            payload = dict(payload)
            payload["followup"] = followup
            payload["expert_rank"] = followup.get("expert_rank") or {}
            payload["llm_rank"] = followup.get("llm_rank") or {}
    return payload


def generate_report(run_dir: Path, out_dir: Path) -> Path:
    run_dir = run_dir.resolve()
    if not run_dir.is_dir():
        raise FileNotFoundError(f"run directory not found: {run_dir}")
    tables = load_run_tables(run_dir)
    manifest = load_manifest(run_dir)
    run_id = str(manifest.get("run_id") or run_dir.name)
    phase10 = load_phase10_rows(REPO_ROOT)
    expert_pairwise = _load_expert_pairwise(run_dir)
    followup = expert_pairwise.get("followup") if isinstance(expert_pairwise.get("followup"), dict) else {}
    if followup:
        tables["table_d"] = apply_table_d_ranks(tables.get("table_d") or [], followup)
        write_table_d(run_dir / "metrics", tables["table_d"])
    out_dir.mkdir(parents=True, exist_ok=True)
    paper = build_paper_markdown(
        run_id=run_id,
        manifest=manifest,
        tables=tables,
        phase10=phase10,
        expert_pairwise=expert_pairwise,
    )
    paper_path = out_dir / "paper.md"
    paper_path.write_text(paper, encoding="utf-8")
    _copy_tables(run_dir / "metrics", out_dir / "tables")
    _copy_figure_data(run_dir / "metrics" / "figure_data", out_dir / "figure_data")
    figures = out_dir / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    write_baseline_f1_svg(tables["table_a"], figures / "table_a_pairwise_f1.svg")
    if tables["table_b"]:
        write_llm_f1_svg(tables["table_b"], figures / "table_b_pairwise_f1.svg")
        write_stability_svg(tables["table_b"], figures / "table_b_stability.svg")
    else:
        (figures / "table_b_pairwise_f1.svg").write_text(
            _missing_svg("Table B missing; LLM scores were not invented."),
            encoding="utf-8",
        )
    write_ablation_f1_svg(tables["table_c"], figures / "table_c_ablation_f1.svg")
    _copy_phase10(phase10, out_dir)
    (out_dir / "README.md").write_text(_report_index(run_id, run_dir, phase10), encoding="utf-8")
    return paper_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write SEMS-R paper artifacts from a run snapshot")
    parser.add_argument(
        "--run",
        type=Path,
        default=DEFAULT_RUN,
        help="snapshot directory under outputs/runs/",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="report directory (default: outputs/reports/<run_id>)",
    )
    args = parser.parse_args(argv)
    run_dir = args.run if args.run.is_absolute() else REPO_ROOT / args.run
    out_dir = args.out
    if out_dir is None:
        out_dir = REPO_ROOT / "outputs" / "reports" / run_dir.name
    elif not out_dir.is_absolute():
        out_dir = REPO_ROOT / out_dir
    paper_path = generate_report(run_dir, out_dir)
    print(paper_path)
    return 0


def _copy_tables(metrics_dir: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for name in ("table_a", "table_b", "table_c", "table_d"):
        for suffix in (".csv", ".md"):
            src = metrics_dir / f"{name}{suffix}"
            if src.exists():
                shutil.copy2(src, dest / src.name)


def _copy_figure_data(src: Path, dest: Path) -> None:
    if not src.is_dir():
        return
    dest.mkdir(parents=True, exist_ok=True)
    for path in src.iterdir():
        if path.is_file():
            shutil.copy2(path, dest / path.name)


def _copy_phase10(rows: list[dict[str, str]], out_dir: Path) -> None:
    dest = out_dir / "tables" / "load"
    dest.mkdir(parents=True, exist_ok=True)
    figures = out_dir / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    for directory in comparison_dirs(rows, REPO_ROOT):
        stamp = directory.name
        for name in ("comparison.csv", "comparison.md", "comparison_delta.csv", "plan.json"):
            src = directory / name
            if src.exists():
                shutil.copy2(src, dest / f"{stamp}_{name}")
        p95 = directory / "p95.svg"
        if p95.exists():
            shutil.copy2(p95, figures / f"phase10_{stamp}_p95.svg")


def _missing_svg(message: str) -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="720" height="120">'
        f'<text x="24" y="64" font-size="16">{message}</text></svg>\n'
    )


def _report_index(run_id: str, run_dir: Path, phase10: list[dict[str, str]] | None = None) -> str:
    load_note = (
        "Phase 10 Locust rows: [tables/load](tables/load). Not merged into the Phase 1–8 snapshot."
        if phase10
        else "Phase 10 comparison CSVs were not found."
    )
    return "\n".join(
        [
            f"# SEMS-R report `{run_id}`",
            "",
            "Paper narrative: [paper.md](paper.md)",
            "",
            f"Source snapshot: `{run_dir}`",
            "",
            "SEMS-R reconstruction. Not original SEMS. Expert ranks are blank until filled.",
            "",
            load_note,
            "",
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
