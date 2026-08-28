from __future__ import annotations

from typing import Any

from analysis.load import float_or_none

TABLE_A_FIELDS = [
    "method",
    "n_services",
    "pairwise_precision",
    "pairwise_recall",
    "pairwise_f1",
    "ari",
    "nmi",
    "cross_service_coupling",
    "db_ownership_conflicts",
    "cycles",
]
TABLE_B_FIELDS = [
    "model",
    "condition",
    "n_runs",
    "pairwise_f1",
    "rule_compliance",
    "stability",
    "uncertain_decisions",
    "unsupported_assumptions",
]
TABLE_C_FIELDS = ["evidence", "method", "pairwise_f1", "modularity", "cross_service_coupling"]
TABLE_D_FIELDS = ["service", "rule_based_rank", "llm_rank", "expert_rank", "historical_rank"]


def build_paper_markdown(
    *,
    run_id: str,
    manifest: dict[str, Any],
    tables: dict[str, list[dict[str, str]]],
    phase10: list[dict[str, str]] | None = None,
    expert_pairwise: dict[str, Any] | None = None,
) -> str:
    table_a = tables.get("table_a") or []
    table_b = tables.get("table_b") or []
    table_c = tables.get("table_c") or []
    table_d = tables.get("table_d") or []
    load_rows = phase10 or []
    expert = expert_pairwise or {}
    parts = [
        _integrity(run_id, manifest, expert),
        _methods(),
        _table_block(
            "Table A — deterministic methods vs historical reference",
            table_a,
            TABLE_A_FIELDS,
        ),
        _interpret_a(table_a),
        _table_block("Table B — LLM conditions C0–C3", table_b, TABLE_B_FIELDS),
        _interpret_b(table_b),
        _table_block("Table C — evidence ablation", table_c, TABLE_C_FIELDS),
        _interpret_c(table_c),
        _table_block("Table D — migration ranking", table_d, TABLE_D_FIELDS),
        _interpret_d(table_d),
        _research_questions(table_a, table_b, table_c, expert),
        _phase9(),
        _phase10(load_rows),
        _threats(load_rows, expert),
        _not_claimed(load_rows, expert),
    ]
    return "\n\n".join(parts).rstrip() + "\n"


def _integrity(run_id: str, manifest: dict[str, Any], expert: dict[str, Any] | None = None) -> str:
    original = manifest.get("is_original_sems_source")
    gold_eval = manifest.get("gold_used_for_evaluation_only")
    fabricated = manifest.get("llm_outputs_fabricated")
    git = manifest.get("git") if isinstance(manifest.get("git"), dict) else {}
    commit = git.get("commit") if git else None
    expert = expert or {}
    n_reviewers = len(_reviewer_ids(expert))
    followup = expert.get("followup") or {}
    expert_ranks_filled = bool(followup.get("expert_rank") or expert.get("expert_rank"))
    if n_reviewers and expert_ranks_filled:
        expert_line = (
            f"- Independent architect pairwise sheets: {n_reviewers} reviewers scored. "
            "Table D expert ranks are the median of their extract-first lists"
        )
        rank_integrity = (
            "- Historical migration ranks: blank; no documented extract-first order exists"
        )
    elif n_reviewers:
        expert_line = (
            f"- Independent architect pairwise sheets: {n_reviewers} reviewers scored. "
            "Table D expert migration ranks remain blank; not inferred from pairwise sheets"
        )
        rank_integrity = "- Expert and historical migration ranks: blank; not fabricated"
    else:
        expert_line = "- Independent architect ranks: blank until humans fill the expert packet"
        rank_integrity = "- Expert and historical migration ranks: blank; not fabricated"
    return "\n".join(
        [
            "# SEMS-R decomposition report",
            "",
            "**Integrity.** This report describes **SEMS-R** "
            "(Reconstructed Legacy Education System), "
            "a controlled reconstruction. It is **not** the original production SEMS source. "
            "Numbers below are measurements of SEMS-R. They must not be pooled with historical "
            "SEMS paper measurements.",
            "",
            f"- Snapshot: `{run_id}`",
            f"- Original SEMS source: `{original}`",
            f"- Historical gold used for evaluation only: `{gold_eval}`",
            f"- LLM outputs fabricated: `{fabricated}`",
            f"- Git commit: `{commit}` (unavailable if null)",
            expert_line,
            rank_integrity,
        ]
    )


def _methods() -> str:
    return "\n".join(
        [
            "## Methods (this snapshot)",
            "",
            "Deterministic baselines and LLM prompts read architectural evidence only "
            "(`domain_description`, component catalog, call/data/runtime summaries, migration "
            "rules R1–R9). They do **not** read `reference/historical_architecture.json`.",
            "",
            "Evaluation scores already-produced assignments against the historical six-service "
            "reference on the 24-component six-way universe (`AuthService` and `UserRepository` "
            "excluded as shared identity). Pairwise F1, ARI, and NMI "
            "are computed on that universe.",
            "",
            "LLM conditions: **C0** domain + catalog; **C1** adds call/data/runtime; **C2** adds "
            "R1–R9; **C3** adds self-critique. Temperature 0.2, three runs per cell. Invalid JSON "
            "is stored as `parsed.json = null`; it is not replaced with a guessed architecture.",
            "",
            "Combined-graph weights are α=β=γ=1.0 and were not fit on gold. "
            "Louvain *k* is unconstrained.",
            "",
            "Figures in this report are rendered from the measured Table A–C CSVs. They are not "
            "redrawn from gold labels.",
            "",
            "Phase 10 reports the Mode E equal-resource Locust comparison "
            "(monolith vs clustered campus at 4 CPU / 4 GB). "
            "Those numbers are read from `outputs/performance/comparisons/` and are not merged "
            "into the Phase 1–8 metrics snapshot. "
            "Locust mix 35/20/15/10/10/5/5 is synthetic. Locust ran on the host, "
            "outside the container CPU/RAM budget.",
        ]
    )


def _table_block(title: str, rows: list[dict[str, str]], fields: list[str]) -> str:
    if not rows:
        return f"## {title}\n\n*No rows in this snapshot. Values were not invented.*"
    lines = [f"## {title}", "", "| " + " | ".join(fields) + " |"]
    lines.append("| " + " | ".join("---" for _ in fields) + " |")
    for row in rows:
        lines.append("| " + " | ".join(_cell(row.get(key)) for key in fields) + " |")
    return "\n".join(lines)


def _interpret_a(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "Table A has no measured rows."
    ranked = _rank(rows, "method", "pairwise_f1")
    lead = ranked[0] if ranked else ("", None)
    graph = [item for item in ranked if item[0] != "rule_based"]
    graph_lead = graph[0] if graph else ("", None)
    return "\n".join(
        [
            "On this reconstruction, the name/module heuristic (`rule_based`) has the highest "
            f"pairwise F1 ({_fmt(lead[1])}). Graph methods remain in a lower band "
            f"(best graph method `{graph_lead[0]}` F1 {_fmt(graph_lead[1])}). "
            "Rule-based F1 is inflated by reconstruction file and class names "
            "(`FacultyService`, and so on); treat it as an upper-bound leak, not as a fair "
            "contest against anonymous components.",
        ]
    )


def _interpret_b(rows: list[dict[str, str]]) -> str:
    if not rows:
        return (
            "Table B is missing. Scientific LLM scores were not invented for this snapshot."
        )
    by_model = _group(rows, "model")
    lines = [
        "For every model in this snapshot, **C0 has the highest pairwise F1**. Adding call-graph, "
        "data, runtime, rules, or self-critique did not raise F1 above C0.",
    ]
    for model, items in sorted(by_model.items()):
        c0 = _value(items, "C0", "pairwise_f1")
        best_later = max(
            (_value(items, cond, "pairwise_f1") or 0.0 for cond in ("C1", "C2", "C3")),
            default=0.0,
        )
        stab_c1 = _value(items, "C1", "stability")
        lines.append(
            f"- `{model}`: C0 F1 {_fmt(c0)}; strongest later condition F1 {_fmt(best_later)}; "
            f"C1 stability {_fmt(stab_c1)}."
        )
    return "\n".join(lines)


def _interpret_c(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "Table C has no measured rows."
    ranked = _rank(rows, "evidence", "pairwise_f1")
    bits = ", ".join(f"`{name}` {_fmt(score)}" for name, score in ranked)
    return (
        "Evidence-source pairwise F1 on this reconstruction (highest first): "
        f"{bits}. Combined static+runtime is strongest among graph ablations and still far "
        "below the name-leaking rule baseline. Runtime-only exceeds static-call and "
        "static-call-plus-data here."
    )


def _interpret_d(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "Table D has no measured rows."
    blank_llm = all(not (row.get("llm_rank") or "").strip() for row in rows)
    blank_expert = all(not (row.get("expert_rank") or "").strip() for row in rows)
    blank_hist = all(not (row.get("historical_rank") or "").strip() for row in rows)
    if blank_llm and blank_expert:
        return (
            "Rule-based migration ranks are filled from the locked heuristic. "
            f"LLM ranks blank: {blank_llm}. Expert ranks blank: {blank_expert}. "
            f"Historical ranks blank: {blank_hist}. Blank cells were not filled with guesses."
        )
    return (
        "Rule-based ranks are the locked heuristic. LLM ranks are `gemini-2.5-flash` C0 run 1 "
        "`migration_priority` mapped onto the six Table D names (`AuthService` and "
        "`ReportingService` are omitted because they are not Table D rows). Expert ranks are "
        "the median of five extract-first lists that used those same FacultyService/StudentService "
        "names. "
        f"Historical ranks blank: {blank_hist}. No documented historical extract order exists."
    )


def _research_questions(
    table_a: list[dict[str, str]],
    table_b: list[dict[str, str]],
    table_c: list[dict[str, str]],
    expert_pairwise: dict[str, Any] | None = None,
) -> str:
    return "\n".join(
        [
            "## Research questions (answered from this snapshot only)",
            "",
            "### RQ1 — agreement with historical reference and independent architects",
            _rq1(table_b, expert_pairwise or {}),
            "",
            "### RQ2 — does structured evidence improve LLM decomposition "
            "vs a high-level description?",
            _rq2(table_b),
            "",
            "### RQ3 — do migration constraints and self-critique improve stability and quality?",
            _rq3(table_b),
            "",
            "### RQ4 — which evidence source contributes most?",
            _rq4(table_c),
            "",
            "### RQ5 — LLM vs rule-based and graph baselines",
            _rq5(table_a, table_b),
        ]
    )


def _rq1(table_b: list[dict[str, str]], expert: dict[str, Any]) -> str:
    parts: list[str] = []
    if not table_b:
        parts.append(
            "LLM cells are empty in this snapshot, so historical-reference agreement for models "
            "cannot be reported."
        )
    else:
        c0 = [
            (row.get("model"), float_or_none(row.get("pairwise_f1")))
            for row in table_b
            if row.get("condition") == "C0"
        ]
        bits = ", ".join(f"`{model}` {_fmt(score)}" for model, score in c0)
        parts.append(f"Vs the historical six-way reference, C0 pairwise F1 is {bits}.")
    vs_gold = expert.get("vs_gold") or {}
    reviewers = _reviewer_ids(expert)
    if reviewers:
        clauses = []
        for reviewer_id in reviewers:
            row = vs_gold[reviewer_id]
            label = _architect_label(reviewer_id)
            clauses.append(
                f"{label} {_fmt(_score_num(row.get('f1')))} "
                f"(precision {_fmt(_score_num(row.get('precision')))}, "
                f"recall {_fmt(_score_num(row.get('recall')))})"
            )
        n = len(reviewers)
        parts.append(
            f"{n} architect{'s' if n != 1 else ''} filled the 325-pair sheet. "
            "On the 24-component six-way eval universe, pairwise F1 vs historical gold is "
            f"{'; '.join(clauses)}."
        )
        llm = vs_gold.get("llm") or {}
        if llm:
            parts.append(
                f"The Gemini C0 example sheet scores F1 {_fmt(_score_num(llm.get('f1')))} "
                "on that same universe."
            )
        agree_block = expert.get("agreement") or {}
        pairs = agree_block.get("expert_pairs") or {}
        if not pairs and agree_block.get("exp1_vs_exp2"):
            pairs = {"exp1_vs_exp2": agree_block["exp1_vs_exp2"]}
        if n == 2 and pairs:
            only = next(iter(pairs.values()))
            parts.append(
                f"Inter-rater agreement is {only.get('agree')}/{only.get('n')} pairs "
                f"(observed {only.get('observed')}, Cohen's kappa {only.get('kappa')}). "
                f"The two sheets differ on {only.get('n_diff')} pairs."
            )
        elif n > 2 and pairs:
            mean_k = agree_block.get("mean_pairwise_kappa")
            min_k = agree_block.get("min_pairwise_kappa")
            max_k = agree_block.get("max_pairwise_kappa")
            parts.append(
                f"Mean pairwise Cohen's kappa among {n} reviewers is {mean_k} "
                f"(range {min_k}–{max_k} across {len(pairs)} rater pairs)."
            )
        followup = expert.get("followup") or {}
        if followup.get("expert_rank"):
            parts.append(
                "Table D `expert_rank` is the median of the five extract-first lists, mapped "
                "FacultyService→faculty (and likewise for the other five Table D names). "
                "`AuthService` and `ReportingService` were ranked by reviewers but are not Table D "
                "rows. `historical_rank` is blank: no documented historical extract order exists. "
                "Do not treat the historical six-service split as proven ground truth, only as the "
                "evaluation reference used here."
            )
        else:
            parts.append(
                "Table D `expert_rank` is still blank: reviewers did not submit an extract-first "
                "list, and extra same-service=1 links are not converted into a six-way clustering. "
                "Do not treat the historical six-service split as proven ground truth, only as the "
                "evaluation reference used here."
            )
    elif not table_b:
        parts.append("Independent architect pairwise sheets are unfilled in this snapshot.")
    else:
        parts.append(
            "Independent architect pairwise agreement cannot be answered: the blind packet "
            "was unfilled in this snapshot. Do not treat the historical six-service split as "
            "proven ground truth, only as the evaluation reference used here."
        )
    return " ".join(parts)


def _rq2(table_b: list[dict[str, str]]) -> str:
    if not table_b:
        return "Table B missing; RQ2 is unanswered rather than guessed."
    worse = []
    for model, items in _group(table_b, "model").items():
        c0 = _value(items, "C0", "pairwise_f1")
        c1 = _value(items, "C1", "pairwise_f1")
        if c0 is None or c1 is None:
            continue
        worse.append(f"`{model}` C1 {_fmt(c1)} vs C0 {_fmt(c0)}")
    return (
        "No. On this reconstruction, C1 pairwise F1 is lower than C0 for every model "
        f"({'; '.join(worse)}). Structured call/data/runtime summaries did not improve "
        "boundary F1 relative to the high-level C0 prompt."
    )


def _rq3(table_b: list[dict[str, str]]) -> str:
    if not table_b:
        return "Table B missing; RQ3 is unanswered rather than guessed."
    lines = [
        "Not as a reliable F1 gain. C2 and C3 do not beat C0 for any model in this snapshot. "
        "Stability is model-dependent:",
    ]
    for model, items in sorted(_group(table_b, "model").items()):
        lines.append(
            f"- `{model}`: C0–C3 stability "
            + ", ".join(
                f"{cond} {_fmt(_value(items, cond, 'stability'))}"
                for cond in ("C0", "C1", "C2", "C3")
            )
            + f"; rule_compliance C0 {_fmt(_value(items, 'C0', 'rule_compliance'))}."
        )
    lines.append(
        "Gemini rule compliance is 1.0 across conditions; that does not imply higher F1 than C0."
    )
    return "\n".join(lines)


def _rq4(table_c: list[dict[str, str]]) -> str:
    if not table_c:
        return "Table C missing; RQ4 is unanswered rather than guessed."
    ranked = _rank(table_c, "evidence", "pairwise_f1")
    names = [name for name, _ in ranked]
    return (
        f"Ranking by pairwise F1: {' > '.join(f'`{name}`' for name in names)}. "
        "Runtime contributes more than static-call or static-call-plus-data on this "
        "reconstruction; combining static and runtime is strongest among the graph ablations. "
        "All four remain far below the name-leaking rule baseline. Database-only was not a "
        "Phase 4 method, so it is not in Table C."
    )


def _rq5(table_a: list[dict[str, str]], table_b: list[dict[str, str]]) -> str:
    rule = _lookup(table_a, "method", "rule_based", "pairwise_f1")
    combined = _lookup(table_a, "method", "combined_graph", "pairwise_f1")
    if not table_b:
        return (
            f"Rule-based F1 {_fmt(rule)}; combined graph {_fmt(combined)}. "
            "LLM comparison awaits Table B."
        )
    c0_rows = [
        (row.get("model"), float_or_none(row.get("pairwise_f1")))
        for row in table_b
        if row.get("condition") == "C0"
    ]
    best = max((score or 0.0 for _, score in c0_rows), default=0.0)
    tied = [model for model, score in c0_rows if score == best]
    models = ", ".join(f"`{name}`" for name in tied)
    return (
        f"Rule-based pairwise F1 {_fmt(rule)} exceeds all graph methods "
        f"(combined graph {_fmt(combined)}). Best LLM C0 ({models}) is {_fmt(best)}, "
        "near the rule heuristic and well above Louvain. That proximity is not a fair win for "
        "either side: both C0 and the rule method see reconstruction names and the six "
        "functional-area labels. Graph methods discover 4–5 communities vs reference 6."
    )


def _phase9() -> str:
    return "\n".join(
        [
            "## Phase 9 — historical six-service materialization",
            "",
            "The evaluation-only gold split is materialized as six FastAPI services "
            "(Faculty, Student, Grade, Finance, Attendance, Library) plus a gateway that "
            "owns `User` and preserves the monolith public `/api/v1` contract. "
            "Each service has its own logical database. Peers use HTTP or in-process ASGI "
            "in tests; services do not import `app.models`. "
            "`reference/historical_architecture.json` is not an input to this code. "
            "This is the **reference materialization** for RQ evaluation, not an LLM output "
            "and not a scored decomposition. "
            "Gateway-only Locust smoke is not an equal-resource comparison and is not reported "
            "as a Phase 10 result.",
        ]
    )


def _phase10(rows: list[dict[str, str]]) -> str:
    if not rows:
        return (
            "## Phase 10 — cost of distribution (Locust)\n\n"
            "*No comparison CSVs were found. Latency and RPS were not invented.*"
        )
    shown = _phase10_success_rows(rows)
    if not shown:
        return (
            "## Phase 10 — cost of distribution (Locust)\n\n"
            "*Equal-resource Mode E high rows were not found. Latency and RPS were not invented.*"
        )
    lines = [
        "## Phase 10 — cost of distribution (Locust)",
        "",
        "This is a cost-of-distribution check on SEMS-R, not a proof that a split is faster "
        "than the monolith, and not a replay of a historical 10k-request production incident. "
        "One Docker Desktop VM, one uvicorn worker per process, one run per arm. "
        "Locust `high` is 100 users / 300s. Seed scale is `small` via the public HTTP API.",
        "",
        "The paper load table is **Mode E equal-total 4 CPU / 4 GB**: monolith vs a "
        "dependency-clustered campus (faculty, student, grade, finance, and attendance in one "
        "process; library remains HTTP). Mode E does not replace the historical six-service gold.",
        "",
        _load_table(shown),
        "",
        _interpret_phase10(shown),
    ]
    return "\n".join(lines)


def _phase10_success_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Mode E high equal-resource comparison only (completed clustered vs monolith)."""
    return [
        row
        for row in rows
        if row.get("mode") == "E"
        and row.get("config") == "high"
        and str(row.get("equal_total") or "").lower() == "true"
        and row.get("architecture") in {"monolith", "clustered"}
    ]


def _load_table(rows: list[dict[str, str]]) -> str:
    fields = [
        "mode",
        "architecture",
        "config",
        "users",
        "requests",
        "failures",
        "median_ms",
        "p95_ms",
        "p99_ms",
        "rps",
        "equal_total",
        "stamp",
    ]
    lines = [
        "### Measured Locust rows",
        "",
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join("---" for _ in fields) + " |",
    ]
    for row in rows:
        view = {
            **row,
            "requests": row.get("request_count"),
            "failures": row.get("failure_count"),
            "rps": _fmt_rps(row.get("rps")),
        }
        lines.append("| " + " | ".join(_cell(view.get(key)) for key in fields) + " |")
    return "\n".join(lines)


def _interpret_phase10(rows: list[dict[str, str]]) -> str:
    e_clustered = _load_lookup(rows, "E", "clustered", "high")
    e_mono = _load_lookup(rows, "E", "monolith", "high")
    if not e_clustered or not e_mono:
        return "Mode E high equal-resource rows are incomplete in this snapshot."
    return "\n".join(
        [
            "Mode E Locust `high` (equal 4 CPU / 4 GB): clustered campus p99 "
            f"{_load_cell(e_clustered, 'p99_ms')} ms at {_load_cell(e_clustered, 'rps')} rps "
            f"({_load_cell(e_clustered, 'failure_count')} failed requests). "
            f"The monolith p99 {_load_cell(e_mono, 'p99_ms')} ms at "
            f"{_load_cell(e_mono, 'rps')} rps "
            f"({_load_cell(e_mono, 'failure_count')} failed requests). "
            "The monolith completed more requests and still had more failed requests. "
            "Clustered throughput does not exceed the monolith on this reconstruction. "
            "These rows are not production SEMS and are not 10k requests/s.",
        ]
    )


def _threats(rows: list[dict[str, str]], expert: dict[str, Any] | None = None) -> str:
    extra = []
    if rows:
        extra = [
            "- **Phase 10 host.** Docker Desktop cgroups on one laptop, one uvicorn worker, "
            "one Postgres per architecture, Locust on the host. Not bare metal and not a "
            "multi-host production mesh.",
            "- **One run per arm.** No repeated trials; treat tails as measured once.",
            "- **Mode E is a second materialization.** The clustered campus is for load "
            "comparison. It is not the historical six-service gold.",
        ]
    reviewers = _reviewer_ids(expert or {})
    if reviewers:
        n = len(reviewers)
        vs_llm = ((expert or {}).get("agreement") or {}).get("vs_llm") or {}
        llm_bits = ""
        if vs_llm:
            diffs = [
                f"{_architect_label(name)} {row.get('n_diff')}"
                for name, row in vs_llm.items()
                if isinstance(row, dict)
            ]
            if diffs:
                llm_bits = (
                    " Differences vs the Gemini C0 example: "
                    + "; ".join(diffs)
                    + " pairs. Anchoring on that example is a threat for reviewers who received it."
                )
        closest = _closest_expert_pair((expert or {}).get("agreement") or {})
        close_bits = ""
        if closest is not None:
            unit = "pair" if closest == 1 else "pairs"
            close_bits = f" Closest rater pair differs on {closest} {unit}."
        expert_line = (
            f"- **Architect pairwise.** {n} reviewers filled the 325-pair sheet. Extra "
            "same-service=1 links are not a transitive six-way partition; Table D uses the "
            f"separate extract-first lists, not those pairwise 1s.{llm_bits}{close_bits}"
        )
        rank_line = (
            "- **Architect ranks.** Extract-first sheets used FacultyService/StudentService names "
            "(same labels as the LLM rank example). Grouping sheets used different proposed-service "
            "names. Median Table D ranks therefore follow the rank-sheet names, not the grouping "
            "names. Anchoring on the LLM rank example is a threat."
        )
    else:
        expert_line = (
            "- **No independent architects.** Expert ranks and pairwise architect decisions remain blank."
        )
        rank_line = ""
    threats = [
            "## Threats to validity",
            "",
            "- **Naming leak.** Reconstruction class and file names encode the six areas. "
            "Rule-based F1 and LLM C0 are both exposed to that leak.",
            "- **C0 still names the six areas.** The domain description lists Faculty, Student, "
            "Grade, Finance, Attendance, and Library. C0 is not a blind clustering task.",
            expert_line,
    ]
    if rank_line:
        threats.append(rank_line)
    threats += [
            "- **Model set.** Anthropic/Claude was never run. `llama3.1` via Ollama is not "
            "size-matched to Gemini 2.5 Flash. Exact Ollama digest was not frozen in the manifest.",
            "- **Llama C1 instability.** Assignment stability 0.2712 means that cell is not a "
            "stable architecture recommendation.",
            "- **Synthetic workload.** Locust mix 35/20/15/10/10/5/5 is an experimental "
            "assumption, not production SEMS traffic.",
            "- **Not original SEMS.** Do not claim production fidelity or pool with historical "
            "paper numbers.",
            "- **Shared identity.** `User` / auth components are excluded from six-way clustering.",
            "- **Git commit unavailable** in this tree's manifests.",
            *extra,
        ]
    return "\n".join(threats)


def _not_claimed(rows: list[dict[str, str]], expert: dict[str, Any] | None = None) -> str:
    load_lines = (
        [
            "- Phase 10 does not show that a split is faster than the monolith.",
            "- Mode E clustered throughput does not beat the monolith at equal 4 CPU / 4 GB.",
            "- Mode E does not replace the historical six-service gold materialization.",
            "- These Locust rows are not production SEMS traffic and are not 10k requests/s.",
        ]
        if rows
        else [
            "- Phase 10 equal-resource Locust comparison of monolith vs microservices is not "
            "in this snapshot. No latency, RPS, or saturation numbers are reported.",
        ]
    )
    rank_claim = (
        "- Historical migration ranks are not inferred. Expert ranks are medians of submitted "
        "extract-first lists, not inferred from pairwise sheets."
        if expert and (expert.get("followup") or {}).get("expert_rank")
        else "- Expert or historical migration ranks are not inferred."
    )
    return "\n".join(
        [
            "## What this report does not claim",
            "",
            rank_claim,
            "- C1–C3 are not claimed to improve F1 on this reconstruction; "
            "the tables show the opposite.",
            *load_lines,
        ]
    )


def _cell(value: str | None) -> str:
    if value is None:
        return ""
    return str(value)


def _fmt(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.4f}"


def _score_num(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if value is None:
        return None
    return float_or_none(str(value))


def _reviewer_ids(expert: dict[str, Any]) -> list[str]:
    ids = expert.get("reviewer_ids")
    if isinstance(ids, list) and ids:
        return [str(item) for item in ids if str(item).startswith("exp")]
    vs_gold = expert.get("vs_gold") or {}
    found = [key for key in vs_gold if key.startswith("exp") and key[3:].isdigit()]
    return sorted(found, key=lambda key: int(key[3:]))


def _architect_label(reviewer_id: str) -> str:
    suffix = reviewer_id[3:] if reviewer_id.startswith("exp") else reviewer_id
    return f"architect {suffix}"


def _closest_expert_pair(agreement: dict[str, Any]) -> int | None:
    pairs = agreement.get("expert_pairs") or {}
    diffs = [
        row.get("n_diff")
        for row in pairs.values()
        if isinstance(row, dict) and row.get("n_diff") is not None
    ]
    return min(diffs) if diffs else None


def _fmt_rps(value: str | None) -> str:
    parsed = float_or_none(value)
    if parsed is None:
        return ""
    return f"{parsed:.4f}".rstrip("0").rstrip(".")


def _load_lookup(
    rows: list[dict[str, str]], mode: str, architecture: str, config: str
) -> dict[str, str] | None:
    for row in rows:
        if (
            row.get("mode") == mode
            and row.get("architecture") == architecture
            and row.get("config") == config
        ):
            return row
    return None


def _load_cell(row: dict[str, str] | None, field: str) -> str:
    if row is None:
        return "n/a"
    if field == "rps":
        return _fmt_rps(row.get("rps")) or "n/a"
    return _cell(row.get(field)) or "n/a"


def _rank(
    rows: list[dict[str, str]], name_key: str, score_key: str
) -> list[tuple[str, float | None]]:
    scored = [(row.get(name_key) or "", float_or_none(row.get(score_key))) for row in rows]
    return sorted(scored, key=lambda item: item[1] if item[1] is not None else -1.0, reverse=True)


def _group(rows: list[dict[str, str]], key: str) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(row.get(key) or "", []).append(row)
    return grouped


def _value(rows: list[dict[str, str]], condition: str, field: str) -> float | None:
    for row in rows:
        if row.get("condition") == condition:
            return float_or_none(row.get(field))
    return None


def _lookup(rows: list[dict[str, str]], key: str, name: str, field: str) -> float | None:
    for row in rows:
        if row.get(key) == name:
            return float_or_none(row.get(field))
    return None
