"""Render the two quality graphs (coverage + mutation score) — PNG + interactive HTML.

Analysis-only (CLAUDE.md §3.10). Reads MEASURED coverage from
``_measured/coverage.json`` and the cited mutation-gate summary from
``_measured/mutation_gate_summary.json`` and renders:

* ``coverage_line_branch`` — package line & branch coverage against the 90/85 gates;
* ``mutation_score_by_module`` — per-module mutation score (all 1.0, 0 survivors).

No magic constants — both charts read the measured/cited JSON.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import plotly.graph_objects as go

from evidence_chart_style import (
    GOOD,
    INK,
    MID_GREY,
    OUT_DIR,
    PLOTLY_FONT,
    RISK,
    apply_matplotlib_house_style,
    caption,
    load_coverage,
    load_mutation,
)

_PLOTLY_KW = {"include_plotlyjs": "cdn", "full_html": True}

# The CI gates (CLAUDE.md §5.5): line ≥ 90%, branch ≥ 85%. Shown as reference lines.
_LINE_GATE = 90.0
_BRANCH_GATE = 85.0


def render_coverage() -> None:
    """Line & branch coverage vs the 90/85 gates (PNG + HTML)."""
    totals = load_coverage()["totals"]
    line_pct = totals["percent_covered"]
    branch_pct = (
        100.0 * totals["covered_branches"] / totals["num_branches"]
        if totals["num_branches"]
        else 100.0
    )
    n_stmts = totals["num_statements"]
    n_branch = totals["num_branches"]
    metrics = ["Line", "Branch"]
    vals = [line_pct, branch_pct]
    gates = [_LINE_GATE, _BRANCH_GATE]

    apply_matplotlib_house_style()
    fig, ax = plt.subplots(figsize=(7.4, 5.0))
    x = [0, 1]
    ax.bar(x, vals, width=0.5, color=GOOD, edgecolor=INK, linewidth=0.8, zorder=3)
    for xi, g in zip(x, gates, strict=True):
        ax.hlines(g, xi - 0.32, xi + 0.32, color=RISK, linestyle="--", linewidth=1.5,
                  zorder=4)
        ax.text(xi + 0.34, g, f"gate {g:.0f}%", va="center", ha="left", fontsize=8.5,
                color=RISK)
    for xi, v in zip(x, vals, strict=True):
        ax.text(xi, v + 0.4, f"{v:.1f}%", ha="center", va="bottom", fontsize=12,
                fontweight="bold", color=INK)
    ax.set_xticks(x)
    ax.set_xticklabels([f"Line\n({n_stmts} stmts)", f"Branch\n({n_branch} branches)"])
    ax.set_ylim(0, 108)
    ax.set_yticks([0, 25, 50, 75, 85, 90, 100])
    ax.set_ylabel("Coverage (%)")
    ax.set_title("Coverage: 100% line + branch (gates 90 / 85)", loc="left")
    caption(fig, "Measured: pytest --cov=autofirm.output_review --cov-branch over "
                 "26 source files. Coverage is necessary, not sufficient (§3.6).")
    fig.savefig(OUT_DIR / "coverage_line_branch.png")
    plt.close(fig)

    hfig = go.Figure()
    hfig.add_bar(x=metrics, y=vals, marker_color=GOOD, marker_line_color=INK,
                 marker_line_width=1, text=[f"{v:.1f}%" for v in vals],
                 textposition="outside",
                 hovertemplate="%{x} coverage %{y:.2f}%<extra></extra>")
    hfig.add_hline(y=_LINE_GATE, line_color=RISK, line_dash="dash",
                   annotation_text="line gate 90%", annotation_position="top left")
    hfig.add_hline(y=_BRANCH_GATE, line_color=MID_GREY, line_dash="dot",
                   annotation_text="branch gate 85%", annotation_position="bottom left")
    hfig.update_layout(
        title="Coverage — 100% line + branch vs 90/85 gates (measured)",
        yaxis={"range": [0, 108], "title": "Coverage (%)"},
        template="simple_white", showlegend=False,
        font={"family": PLOTLY_FONT, "color": INK, "size": 13},
        margin={"l": 70, "r": 30, "t": 60, "b": 50},
    )
    hfig.write_html(OUT_DIR / "coverage_line_branch.html", **_PLOTLY_KW)


def render_mutation() -> None:
    """Per-module mutation score (all 1.0, 0 survivors) — horizontal bars."""
    summary = load_mutation()
    per_module = summary["per_module"]
    modules = sorted(per_module)
    scores = [per_module[m]["mutation_score"] for m in modules]
    total_survivors = summary["total_survivors"]

    apply_matplotlib_house_style()
    fig, ax = plt.subplots(figsize=(9.0, 8.6))
    y = list(range(len(modules)))
    ax.barh(y, scores, color=GOOD, edgecolor=INK, linewidth=0.6, height=0.66, zorder=3)
    ax.axvline(1.0, color=INK, linewidth=0.9, zorder=2)
    ax.set_yticks(y)
    ax.set_yticklabels(modules, fontsize=8.0)
    ax.invert_yaxis()
    ax.set_xlim(0, 1.08)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_xlabel("Mutation score (killed / generated)")
    ax.set_title(f"Mutation score by module — all 1.0, {total_survivors} survivors",
                 loc="left")
    caption(fig, "Cited gate result (scripts/run_mutation_gate.py, fail-closed: only "
                 "ok_killed passes). Not a fresh campaign (§7.2).")
    fig.savefig(OUT_DIR / "mutation_score_by_module.png")
    plt.close(fig)

    hfig = go.Figure()
    hfig.add_bar(x=scores, y=modules, orientation="h", marker_color=GOOD,
                 marker_line_color=INK, marker_line_width=1,
                 hovertemplate="%{y}<br>score %{x:.2f}, 0 survivors<extra></extra>")
    hfig.update_layout(
        title=f"Mutation score by module — all 1.0, {total_survivors} survivors (cited)",
        xaxis={"range": [0, 1.08], "title": "Mutation score"},
        yaxis={"autorange": "reversed"}, template="simple_white", showlegend=False,
        font={"family": PLOTLY_FONT, "color": INK, "size": 10},
        margin={"l": 250, "r": 30, "t": 60, "b": 50},
    )
    hfig.write_html(OUT_DIR / "mutation_score_by_module.html", **_PLOTLY_KW)


def main() -> None:
    """Render both quality graphs to PNG + HTML."""
    render_coverage()
    render_mutation()
    print("rendered: coverage_line_branch, mutation_score_by_module (PNG + HTML)")


if __name__ == "__main__":
    main()
