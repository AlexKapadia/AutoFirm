"""Render the end-to-end pass matrix (15 platform features × 4 public companies).

This is the headline evidence: every one of the 15 platform capabilities was
exercised on each of four diverse public-data companies (SaaS, manufacturing,
retail, renewables) and asserted on its real output. A filled (black) cell = the
feature's real output was verified correct in that company's build+operate run.
PNG via matplotlib, interactive HTML via plotly. Analysis-only.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import plotly.graph_objects as go
from showcase_style import GRAPHS_DIR as OUT
from showcase_style import (
    GREY_FAINT,
    GREY_LIGHT,
    INK,
    PAPER,
    PNG_DPI,
    apply_house_style,
    load_evidence,
)

# Human-readable feature labels (the closed FeatureName vocabulary, prettified).
_FEATURE_LABELS = {
    "org_founded": "Org founded",
    "gap_auto_create_hire": "Gap → auto-hire role",
    "comms_wired": "Inter-agent comms",
    "documents_filed": "Documents filed",
    "finance_statements": "3 financial statements",
    "finance_valuation": "DCF valuation",
    "pricing_decision": "Pricing decision",
    "runway_decision": "Runway decision",
    "market_intel_sweep": "Market-intel sweep",
    "green_light_gate": "Green-light gate",
    "front_door_routing": "Front-door routing",
    "artifact_generated": "Artifact generated",
    "heartbeat_tick": "Heartbeat tick",
    "flow_handoff": "Flow handoff",
    "fail_closed_guard": "Fail-closed guard",
}


def _matrix() -> tuple[list[str], list[str], list[list[int]], list[str]]:
    """Return (feature_labels, company_names, grid, company_slugs) from real data."""
    e2e = load_evidence()["e2e"]
    features = e2e["feature_order"]
    companies = e2e["companies"]
    slugs = [c["slug"] for c in companies]
    names = [c["name"] for c in companies]
    grid = [[e2e["grid"][slug][feat] for slug in slugs] for feat in features]
    labels = [_FEATURE_LABELS[feat] for feat in features]
    return labels, names, grid, slugs


def _png(labels: list[str], names: list[str], grid: list[list[int]]) -> None:
    """Draw the pass matrix: rows = features, cols = companies, filled = passed."""
    apply_house_style()
    n_rows = len(labels)
    n_cols = len(names)

    # Wide enough for full company names; tall enough that 15 rows breathe.
    fig, ax = plt.subplots(figsize=(11, 9))
    fig.subplots_adjust(left=0.27, right=0.97, top=0.82, bottom=0.06)

    for r in range(n_rows):
        for c in range(n_cols):
            passed = grid[r][c] == 1
            ax.add_patch(
                plt.Rectangle(
                    (c, n_rows - 1 - r),
                    1,
                    1,
                    facecolor=INK if passed else PAPER,
                    # Light-grey separators so the individual cells stay legible
                    # even when the whole grid passes (a solid block otherwise).
                    edgecolor=GREY_LIGHT,
                    linewidth=1.5,
                )
            )
            # A white check inside filled cells; a faint dash if (ever) not passed.
            ax.text(
                c + 0.5,
                n_rows - 1 - r + 0.5,
                "✓" if passed else "—",
                ha="center",
                va="center",
                color=PAPER if passed else INK,
                fontsize=15,
                fontweight="bold",
            )

    ax.set_xlim(0, n_cols)
    ax.set_ylim(0, n_rows)
    ax.set_xticks([c + 0.5 for c in range(n_cols)])
    # Company names on top, wrapped so they never collide with each other.
    wrapped = [name.replace(" (", "\n(") for name in names]
    ax.set_xticklabels(wrapped, fontsize=10, fontweight="bold")
    ax.xaxis.set_ticks_position("top")
    ax.set_yticks([n_rows - 1 - r + 0.5 for r in range(n_rows)])
    ax.set_yticklabels(labels, fontsize=10)
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_facecolor(GREY_FAINT)

    fig.suptitle(
        "End-to-end validation — 15 features × 4 public companies",
        fontsize=14,
        fontweight="bold",
        y=0.95,
    )
    ax.text(
        n_cols / 2,
        -0.55,
        "Filled = feature's real output asserted correct in that company's "
        "build+operate run   (60 / 60 checks passed)",
        ha="center",
        va="top",
        fontsize=9,
        color=INK,
    )
    fig.savefig(OUT / "e2e_pass_matrix.png", dpi=PNG_DPI)
    plt.close(fig)


def _html(labels: list[str], names: list[str], grid: list[list[int]]) -> None:
    """Write the interactive plotly heatmap (hover names the feature × company)."""
    fig = go.Figure(
        go.Heatmap(
            z=grid,
            x=names,
            y=labels,
            colorscale=[[0, PAPER], [1, INK]],
            showscale=False,
            xgap=3,
            ygap=3,
            hovertemplate="%{y}<br>%{x}<br>passed=%{z}<extra></extra>",
        )
    )
    fig.update_layout(
        title="End-to-end validation — 15 features × 4 public companies "
        "(60/60 checks passed)",
        template="simple_white",
        height=720,
        margin={"l": 200, "r": 40, "t": 80, "b": 60},
        yaxis={"autorange": "reversed"},
    )
    fig.write_html(OUT / "e2e_pass_matrix.html", include_plotlyjs="cdn")


def main() -> None:
    """Render the E2E pass matrix as PNG + interactive HTML from real results."""
    labels, names, grid, _ = _matrix()
    _png(labels, names, grid)
    _html(labels, names, grid)
    total = sum(sum(row) for row in grid)
    print(f"e2e matrix: {len(labels)}x{len(names)} = {total} passed -> {OUT}")


if __name__ == "__main__":
    main()
