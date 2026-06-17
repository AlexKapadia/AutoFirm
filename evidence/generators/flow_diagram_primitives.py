"""Reusable black-&-white flow-diagram primitives (matplotlib-based).

The graphviz ``dot`` binary is NOT on this Windows box, so flow diagrams are
hand-authored with matplotlib for pixel-exact control over spacing — guaranteeing
clean, unclipped, non-overlapping B&W output (CLAUDE.md §3.10). These primitives
(rounded node boxes, straight + elbow connectors, layer bands) are shared by every
diagram generator so the whole showcase has one consistent visual language.

Exports PNG (matplotlib) and a standalone HTML wrapper embedding the same PNG so
each diagram ships as BOTH HTML and PNG as the contract requires. Analysis-only.
"""

from __future__ import annotations

from dataclasses import dataclass

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from showcase_style import GREY_FAINT, GREY_LIGHT, GREY_MID, INK, PAPER, PNG_DPI


@dataclass(frozen=True)
class Node:
    """One box in a flow diagram, in axis (data) coordinates.

    ``cx``/``cy`` are the box centre; ``w``/``h`` its full width/height. ``title``
    is the bold heading; ``subtitle`` (optional) is a smaller second line. ``fill``
    chooses the B&W tone (paper / faint / light grey) so layers read distinctly.
    """

    key: str
    cx: float
    cy: float
    w: float
    h: float
    title: str
    subtitle: str = ""
    fill: str = PAPER


def new_canvas(width_in: float, height_in: float) -> tuple[Figure, Axes]:
    """Create a clean, axis-free B&W canvas sized in inches."""
    fig, ax = plt.subplots(figsize=(width_in, height_in))
    fig.patch.set_facecolor(PAPER)
    ax.set_facecolor(PAPER)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_aspect("equal")
    return fig, ax


def draw_band(
    ax: Axes, bounds: tuple[float, float, float, float], label: str
) -> None:
    """Draw a faint background band (a horizontal layer) with a left-edge label.

    Args:
        ax: The diagram axes.
        bounds: ``(x0, y0, x1, y1)`` band rectangle in data coordinates.
        label: The rotated layer label drawn in the clear left gutter.
    """
    x0, y0, x1, y1 = bounds
    ax.add_patch(
        mpatches.FancyBboxPatch(
            (x0, y0),
            x1 - x0,
            y1 - y0,
            boxstyle="round,pad=0.0,rounding_size=0.12",
            facecolor=GREY_FAINT,
            edgecolor=GREY_LIGHT,
            linewidth=1.0,
            zorder=1,
        )
    )
    # Label sits in the clear left gutter (x just left of the band), so it never
    # collides with a node whose left edge touches the band's left border.
    ax.text(
        x0 - 0.45,
        (y0 + y1) / 2,
        label,
        rotation=90,
        ha="center",
        va="center",
        fontsize=9,
        fontweight="bold",
        color=GREY_MID,
        zorder=2,
    )


def draw_node(ax: Axes, node: Node) -> None:
    """Draw one rounded node box with a bold title and optional subtitle."""
    ax.add_patch(
        mpatches.FancyBboxPatch(
            (node.cx - node.w / 2, node.cy - node.h / 2),
            node.w,
            node.h,
            boxstyle="round,pad=0.02,rounding_size=0.10",
            facecolor=node.fill,
            edgecolor=INK,
            linewidth=1.4,
            zorder=4,
        )
    )
    if node.subtitle:
        ax.text(
            node.cx,
            node.cy + node.h * 0.16,
            node.title,
            ha="center",
            va="center",
            fontsize=10,
            fontweight="bold",
            color=INK,
            zorder=5,
        )
        ax.text(
            node.cx,
            node.cy - node.h * 0.22,
            node.subtitle,
            ha="center",
            va="center",
            fontsize=7.5,
            color=GREY_MID,
            zorder=5,
        )
    else:
        ax.text(
            node.cx,
            node.cy,
            node.title,
            ha="center",
            va="center",
            fontsize=10,
            fontweight="bold",
            color=INK,
            zorder=5,
        )


def connect(
    ax: Axes,
    src: tuple[float, float],
    dst: tuple[float, float],
    *,
    style: str = "-",
    arrow: bool = True,
) -> None:
    """Draw a B&W connector (optionally arrowed) between two points."""
    ax.annotate(
        "",
        xy=dst,
        xytext=src,
        arrowprops={
            "arrowstyle": "-|>" if arrow else "-",
            "color": INK,
            "linewidth": 1.3,
            "linestyle": style,
            "shrinkA": 2,
            "shrinkB": 2,
        },
        zorder=3,
    )


def save_png_and_html(fig: Figure, png_path, title: str) -> None:
    """Save the figure as a PNG and a standalone HTML page embedding that PNG."""
    fig.savefig(png_path, dpi=PNG_DPI, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
    html_path = png_path.with_suffix(".html")
    png_name = png_path.name
    html_path.write_text(
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        f"<title>{title}</title>"
        "<style>body{background:#fff;color:#111;font-family:"
        "'DejaVu Sans',system-ui,sans-serif;margin:0;padding:32px;text-align:center}"
        "img{max-width:100%;height:auto;border:1px solid #ededed}"
        "h1{font-size:18px;font-weight:700;margin:0 0 18px}</style></head>"
        f"<body><h1>{title}</h1><img src='{png_name}' alt='{title}'></body></html>",
        encoding="utf-8",
    )
