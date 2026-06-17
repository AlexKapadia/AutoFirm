"""Render the per-package coverage bar chart (PNG via matplotlib, HTML via plotly).

Shows the real line + branch coverage of each of the 18 platform packages against
the enforced 90%/85% gates, proving coverage is uniformly high — not propped up by
one package. Numbers come straight from the real coverage report. Analysis-only.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import plotly.graph_objects as go
from showcase_style import GRAPHS_DIR as OUT
from showcase_style import (
    GREY_LIGHT,
    GREY_MID,
    INK,
    PNG_DPI,
    apply_house_style,
    package_coverage_rows,
)

_LINE_GATE = 90.0


def _png(rows: list[tuple[str, float, float]]) -> None:
    """Draw a clean horizontal grouped bar (line vs branch) with gate markers."""
    apply_house_style()
    packages = [r[0] for r in rows]
    line_pct = [r[1] for r in rows]
    branch_pct = [r[2] for r in rows]
    n = len(packages)

    # Tall figure + generous left margin so every long package name fits unclipped.
    fig, ax = plt.subplots(figsize=(11, 9))
    fig.subplots_adjust(left=0.20, right=0.94, top=0.88, bottom=0.10)

    y = range(n)
    height = 0.38
    ax.barh(
        [i + height / 2 for i in y],
        line_pct,
        height=height,
        color=INK,
        label="Line coverage",
        zorder=3,
    )
    ax.barh(
        [i - height / 2 for i in y],
        branch_pct,
        height=height,
        color=GREY_MID,
        label="Branch coverage",
        zorder=3,
    )

    ax.set_yticks(list(y))
    ax.set_yticklabels(packages, fontsize=10)
    ax.set_xlim(0, 108)
    ax.set_xticks([0, 20, 40, 60, 80, 90, 100])
    ax.set_xlabel("Coverage (%)", fontsize=11)
    ax.set_title(
        "Per-package test coverage — 18 platform components",
        fontsize=14,
        fontweight="bold",
        pad=36,
    )

    # Gate reference lines (the enforced CI floor) so the bar is read against bar.
    ax.axvline(_LINE_GATE, color=INK, linestyle="--", linewidth=1.0, zorder=2)
    ax.text(
        _LINE_GATE,
        n - 0.3,
        " line gate 90%",
        fontsize=8,
        va="bottom",
        ha="left",
        color=INK,
    )

    # Value labels just past 100% bars sit inside the 108 xlim → never clipped.
    for i, val in zip(y, line_pct, strict=True):
        ax.text(
            min(val, 100) + 1.0,
            i + height / 2,
            f"{val:.0f}",
            va="center",
            ha="left",
            fontsize=8,
            color=INK,
        )

    # Legend ABOVE the axes (in the title gutter) so it never collides with the
    # x-axis label or tick labels at the bottom of the plot.
    ax.legend(
        loc="lower center",
        frameon=False,
        fontsize=10,
        ncol=2,
        bbox_to_anchor=(0.5, 1.01),
    )
    ax.grid(axis="x", color=GREY_LIGHT, linewidth=0.7, zorder=0)
    fig.savefig(OUT / "coverage_by_package.png", dpi=PNG_DPI)
    plt.close(fig)


def _html(rows: list[tuple[str, float, float]]) -> None:
    """Write the interactive plotly version (hover shows exact line/branch %)."""
    packages = [r[0] for r in rows]
    fig = go.Figure()
    fig.add_bar(
        y=packages,
        x=[r[1] for r in rows],
        name="Line coverage",
        orientation="h",
        marker_color=INK,
    )
    fig.add_bar(
        y=packages,
        x=[r[2] for r in rows],
        name="Branch coverage",
        orientation="h",
        marker_color=GREY_MID,
    )
    fig.add_vline(x=_LINE_GATE, line_dash="dash", line_color=INK)
    fig.update_layout(
        title="Per-package test coverage — 18 platform components",
        barmode="group",
        template="simple_white",
        height=820,
        margin={"l": 170, "r": 40, "t": 70, "b": 50},
        xaxis_title="Coverage (%)",
        xaxis_range=[0, 105],
        legend={"orientation": "h", "y": -0.08},
    )
    fig.write_html(OUT / "coverage_by_package.html", include_plotlyjs="cdn")


def main() -> None:
    """Render both the PNG and the interactive HTML coverage bar."""
    rows = package_coverage_rows()
    _png(rows)
    _html(rows)
    print(f"coverage bar: {len(rows)} packages -> {OUT}")


if __name__ == "__main__":
    main()
