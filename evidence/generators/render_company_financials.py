"""Render the four public companies' headline financials (PNG + interactive HTML).

Shows the real numbers the platform's finance engine produced for each public-data
company: net income, total assets, and the DCF enterprise value. These are the
*outputs* of the deterministic finance package during the operate phase — proof the
platform produces sensible, company-shaped financials across four diverse business
models, not just that the code runs. Analysis-only.
"""

from __future__ import annotations

from decimal import Decimal

import matplotlib.pyplot as plt
import plotly.graph_objects as go
from showcase_style import GRAPHS_DIR as OUT
from showcase_style import (
    GREY_LIGHT,
    GREY_MID,
    INK,
    PNG_DPI,
    apply_house_style,
    load_evidence,
)

# Short company labels for a compact x-axis (full names live in the matrix).
_SHORT = {
    "northwind-saas": "Northwind\n(SaaS)",
    "ironforge-mfg": "Ironforge\n(Mfg)",
    "brightcart-retail": "Brightcart\n(Retail)",
    "solaris-energy": "Solaris\n(Energy)",
}


def _series() -> tuple[list[str], list[float], list[float], list[float]]:
    """Pull (labels, net_income, total_assets, dcf_value) in $M from real evidence."""
    companies = load_evidence()["e2e"]["companies"]
    labels, net_income, assets, dcf = [], [], [], []
    for company in companies:
        ev = company["evidence"]
        labels.append(_SHORT[company["slug"]])
        net_income.append(float(Decimal(ev["finance_statements"]["net_income"]) / 1_000_000))
        assets.append(float(Decimal(ev["finance_statements"]["total_assets"]) / 1_000_000))
        dcf.append(float(Decimal(ev["finance_valuation"]["dcf_value"]) / 1_000_000))
    return labels, net_income, assets, dcf


def _png(
    labels: list[str], net_income: list[float], assets: list[float], dcf: list[float]
) -> None:
    """Grouped bar of net income / total assets / DCF value across the four firms."""
    apply_house_style()
    n = len(labels)
    x = range(n)
    width = 0.26

    fig, ax = plt.subplots(figsize=(11, 7))
    fig.subplots_adjust(left=0.10, right=0.97, top=0.84, bottom=0.12)

    bars = [
        ("Net income", net_income, INK),
        ("Total assets", assets, GREY_MID),
        ("DCF enterprise value", dcf, GREY_LIGHT),
    ]
    for offset, (label, values, color) in zip((-width, 0.0, width), bars, strict=True):
        positions = [i + offset for i in x]
        ax.bar(
            positions,
            values,
            width=width,
            color=color,
            edgecolor=INK,
            linewidth=0.8,
            label=label,
            zorder=3,
        )
        for pos, val in zip(positions, values, strict=True):
            ax.text(
                pos,
                val + max(dcf) * 0.012,
                f"{val:,.1f}",
                ha="center",
                va="bottom",
                fontsize=8,
                color=INK,
            )

    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel("USD, millions", fontsize=11)
    ax.set_ylim(0, max(dcf) * 1.16)
    ax.set_title(
        "Operate-phase financials produced for four public companies",
        fontsize=14,
        fontweight="bold",
        pad=34,
    )
    ax.legend(
        loc="lower center",
        frameon=False,
        fontsize=10,
        ncol=3,
        bbox_to_anchor=(0.5, 1.01),
    )
    ax.grid(axis="y", color=GREY_LIGHT, linewidth=0.7, zorder=0)
    fig.savefig(OUT / "company_financials.png", dpi=PNG_DPI)
    plt.close(fig)


def _html(
    labels: list[str], net_income: list[float], assets: list[float], dcf: list[float]
) -> None:
    """Interactive plotly grouped bar (hover shows exact $M per metric)."""
    flat = [lbl.replace("\n", " ") for lbl in labels]
    fig = go.Figure()
    fig.add_bar(x=flat, y=net_income, name="Net income", marker_color=INK)
    fig.add_bar(x=flat, y=assets, name="Total assets", marker_color=GREY_MID)
    fig.add_bar(x=flat, y=dcf, name="DCF enterprise value", marker_color=GREY_LIGHT)
    fig.update_layout(
        title="Operate-phase financials produced for four public companies",
        barmode="group",
        template="simple_white",
        height=560,
        margin={"l": 70, "r": 40, "t": 80, "b": 60},
        yaxis_title="USD, millions",
        legend={"orientation": "h", "y": -0.18},
    )
    fig.write_html(OUT / "company_financials.html", include_plotlyjs="cdn")


def main() -> None:
    """Render the company-financials chart as PNG + interactive HTML."""
    labels, net_income, assets, dcf = _series()
    _png(labels, net_income, assets, dcf)
    _html(labels, net_income, assets, dcf)
    print(f"financials: {len(labels)} companies -> {OUT}")


if __name__ == "__main__":
    main()
