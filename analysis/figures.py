from __future__ import annotations

from pathlib import Path

from analysis.load import float_or_none


def write_baseline_f1_svg(rows: list[dict[str, str]], path: Path) -> None:
    labels = [row.get("method") or "" for row in rows]
    values = [float_or_none(row.get("pairwise_f1")) or 0.0 for row in rows]
    _bar_svg(
        path,
        labels,
        values,
        title="Table A — pairwise F1 vs historical reference (SEMS-R)",
        ylabel="pairwise F1",
    )


def write_llm_f1_svg(rows: list[dict[str, str]], path: Path) -> None:
    models = sorted({row.get("model") or "" for row in rows})
    conditions = ["C0", "C1", "C2", "C3"]
    series = {
        model: [
            next(
                (
                    float_or_none(row.get("pairwise_f1")) or 0.0
                    for row in rows
                    if row.get("model") == model and row.get("condition") == condition
                ),
                0.0,
            )
            for condition in conditions
        ]
        for model in models
    }
    _grouped_bar_svg(
        path,
        conditions,
        series,
        title="Table B — LLM pairwise F1 by condition (SEMS-R)",
        ylabel="pairwise F1",
    )


def write_ablation_f1_svg(rows: list[dict[str, str]], path: Path) -> None:
    labels = [row.get("evidence") or "" for row in rows]
    values = [float_or_none(row.get("pairwise_f1")) or 0.0 for row in rows]
    _bar_svg(
        path,
        labels,
        values,
        title="Table C — evidence ablation pairwise F1 (SEMS-R)",
        ylabel="pairwise F1",
    )


def write_stability_svg(rows: list[dict[str, str]], path: Path) -> None:
    models = sorted({row.get("model") or "" for row in rows})
    conditions = ["C0", "C1", "C2", "C3"]
    series = {
        model: [
            next(
                (
                    float_or_none(row.get("stability")) or 0.0
                    for row in rows
                    if row.get("model") == model and row.get("condition") == condition
                ),
                0.0,
            )
            for condition in conditions
        ]
        for model in models
    }
    _grouped_bar_svg(
        path,
        conditions,
        series,
        title="Table B — LLM assignment stability (SEMS-R)",
        ylabel="stability",
    )


def _bar_svg(
    path: Path,
    labels: list[str],
    values: list[float],
    *,
    title: str,
    ylabel: str,
) -> None:
    width, height = 720, 360
    left, right, top, bottom = 80, 24, 48, 88
    plot_w = width - left - right
    plot_h = height - top - bottom
    n = max(len(values), 1)
    bar_w = plot_w / n * 0.7
    ymax = 1.0
    bars = []
    for index, (label, value) in enumerate(zip(labels, values, strict=False)):
        x = left + (index + 0.15) * (plot_w / n)
        h = plot_h * min(max(value, 0.0), ymax) / ymax
        y = top + plot_h - h
        cx = x + bar_w / 2
        label_xml = _esc(label)
        bars.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" '
            f'height="{h:.1f}" fill="#334155"/>'
            f'<text x="{cx:.1f}" y="{height - 16}" text-anchor="middle" '
            f'font-size="11" transform="rotate(-28 {cx:.1f},{height - 16})">'
            f"{label_xml}</text>"
        )
    svg = _frame(width, height, left, top, plot_w, plot_h, title, ylabel, bars)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")


def _grouped_bar_svg(
    path: Path,
    categories: list[str],
    series: dict[str, list[float]],
    *,
    title: str,
    ylabel: str,
) -> None:
    width, height = 720, 360
    left, right, top, bottom = 80, 140, 48, 56
    plot_w = width - left - right
    plot_h = height - top - bottom
    names = list(series)
    palette = ["#334155", "#0f766e", "#b45309", "#6d28d9"]
    n_cat = max(len(categories), 1)
    n_ser = max(len(names), 1)
    group_w = plot_w / n_cat
    bar_w = group_w * 0.7 / n_ser
    bars = []
    for c_i, category in enumerate(categories):
        for s_i, name in enumerate(names):
            value = series[name][c_i] if c_i < len(series[name]) else 0.0
            x = left + c_i * group_w + 0.15 * group_w + s_i * bar_w
            h = plot_h * min(max(value, 0.0), 1.0)
            y = top + plot_h - h
            color = palette[s_i % len(palette)]
            bars.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" '
                f'height="{h:.1f}" fill="{color}"/>'
            )
        cx = left + (c_i + 0.5) * group_w
        bars.append(
            f'<text x="{cx:.1f}" y="{height - 16}" text-anchor="middle" '
            f'font-size="12">{_esc(category)}</text>'
        )
    for s_i, name in enumerate(names):
        ly = top + 16 + s_i * 18
        color = palette[s_i % len(palette)]
        bars.append(
            f'<rect x="{width - right + 12}" y="{ly - 10}" width="12" height="12" fill="{color}"/>'
            f'<text x="{width - right + 28}" y="{ly}" font-size="11">{_esc(name)}</text>'
        )
    svg = _frame(width, height, left, top, plot_w, plot_h, title, ylabel, bars)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")


def _frame(
    width: int,
    height: int,
    left: int,
    top: int,
    plot_w: float,
    plot_h: float,
    title: str,
    ylabel: str,
    inner: list[str],
) -> str:
    axis = (
        f'<rect x="{left}" y="{top}" width="{plot_w:.1f}" height="{plot_h:.1f}" '
        f'fill="white" stroke="#111827"/>'
        f'<text x="{width / 2}" y="24" text-anchor="middle" font-size="14">{_esc(title)}</text>'
        f'<text x="16" y="{top + plot_h / 2}" text-anchor="middle" font-size="12" '
        f'transform="rotate(-90 16,{top + plot_h / 2})">{_esc(ylabel)}</text>'
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="Helvetica, Arial, sans-serif">'
        f"{axis}{''.join(inner)}</svg>\n"
    )


def _esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
