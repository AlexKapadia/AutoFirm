"""A tiny black-&-white flow-diagram toolkit (matplotlib) for the output-review lane.

Analysis-only (CLAUDE.md §3.10). The build host has no Graphviz ``dot`` binary, so —
exactly as the rest of ``evidence/`` does — diagrams are drawn directly with
matplotlib for exact, clean, strictly **black-&-white** output (CLAUDE.md §3.10:
aesthetic B&W flow diagrams, no chartjunk). Each diagram is saved as **both** a PNG
and a self-contained HTML file that embeds the crisp vector SVG.

The toolkit deliberately offers only a few primitives — process box, decision
diamond, store/cylinder, and a labelled arrow — with one restrained type + spacing
scale, so every diagram reads as one set and nothing looks vibe-coded (§3.14).
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.path import Path as MplPath

INK = "#101114"  # the single black used for every stroke + label
PAPER = "#ffffff"  # pure white ground (strict B&W)
FAINT = "#f3f4f6"  # a single very-light grey fill for emphasis panels only
_FONT = ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"]


@dataclass(frozen=True)
class Box:
    """A placed node's geometry, so arrows can anchor to its edges precisely."""

    cx: float
    cy: float
    w: float
    h: float

    @property
    def left(self) -> tuple[float, float]:
        """Mid-left anchor point."""
        return (self.cx - self.w / 2, self.cy)

    @property
    def right(self) -> tuple[float, float]:
        """Mid-right anchor point."""
        return (self.cx + self.w / 2, self.cy)

    @property
    def top(self) -> tuple[float, float]:
        """Mid-top anchor point."""
        return (self.cx, self.cy + self.h / 2)

    @property
    def bottom(self) -> tuple[float, float]:
        """Mid-bottom anchor point."""
        return (self.cx, self.cy - self.h / 2)


def new_canvas(width: float, height: float, title: str) -> tuple[Figure, Axes]:
    """Create a clean B&W canvas with a left-aligned title and no axes."""
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = _FONT
    fig, ax = plt.subplots(figsize=(width, height))
    fig.patch.set_facecolor(PAPER)
    ax.set_facecolor(PAPER)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_axis_off()
    ax.text(2, 97, title, fontsize=15, fontweight="bold", color=INK, va="top")
    return fig, ax


def process(ax: Axes, cx: float, cy: float, w: float, h: float, text: str,
            *, emphasis: bool = False, mono: bool = False) -> Box:
    """Draw a rounded process box with centred wrapped text; return its geometry."""
    box = mpatches.FancyBboxPatch(
        (cx - w / 2, cy - h / 2), w, h,
        boxstyle="round,pad=0.6,rounding_size=1.6",
        linewidth=1.5, edgecolor=INK,
        facecolor=FAINT if emphasis else PAPER, zorder=3,
    )
    ax.add_patch(box)
    ax.text(cx, cy, text, ha="center", va="center", fontsize=9.6, color=INK,
            zorder=4, family="monospace" if mono else "sans-serif",
            linespacing=1.35)
    return Box(cx, cy, w, h)


def decision(ax: Axes, cx: float, cy: float, w: float, h: float, text: str) -> Box:
    """Draw a decision diamond with centred text; return its geometry."""
    diamond = mpatches.Polygon(
        [(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)],
        closed=True, linewidth=1.5, edgecolor=INK, facecolor=PAPER, zorder=3,
    )
    ax.add_patch(diamond)
    ax.text(cx, cy, text, ha="center", va="center", fontsize=9.2, color=INK,
            zorder=4, linespacing=1.3)
    return Box(cx, cy, w, h)


def store(ax: Axes, cx: float, cy: float, w: float, h: float, text: str) -> Box:
    """Draw a data-store cylinder with centred text; return its bounding geometry."""
    ax.add_patch(mpatches.FancyBboxPatch(
        (cx - w / 2, cy - h / 2), w, h, boxstyle="round,pad=0.2,rounding_size=4.0",
        linewidth=1.5, edgecolor=INK, facecolor=PAPER, zorder=3))
    ax.add_patch(mpatches.Ellipse((cx, cy + h / 2), w, h * 0.34, linewidth=1.5,
                                  edgecolor=INK, facecolor=PAPER, zorder=4))
    ax.text(cx, cy - h * 0.06, text, ha="center", va="center", fontsize=9.4,
            color=INK, zorder=5, linespacing=1.3)
    return Box(cx, cy, w, h)


def arrow(ax: Axes, start: tuple[float, float], end: tuple[float, float],
          *, label: str = "", dashed: bool = False, label_dy: float = 1.8) -> None:
    """Draw a straight annotated arrow between two anchor points."""
    ax.annotate(
        "", xy=end, xytext=start,
        arrowprops={
            "arrowstyle": "-|>", "color": INK, "linewidth": 1.4,
            "linestyle": "--" if dashed else "-", "shrinkA": 2, "shrinkB": 2,
            "mutation_scale": 16,
        },
        zorder=2,
    )
    if label:
        mx, my = (start[0] + end[0]) / 2, (start[1] + end[1]) / 2
        ax.text(mx, my + label_dy, label, ha="center", va="bottom", fontsize=8.0,
                color=INK, style="italic", zorder=5)


def elbow(ax: Axes, start: tuple[float, float], end: tuple[float, float],
          *, via_x: float, label: str = "", dashed: bool = False) -> None:
    """Draw a right-angled (H then V) arrow routed through ``via_x`` — for feedback."""
    style = "--" if dashed else "-"
    ax.add_patch(mpatches.PathPatch(
        MplPath([start, (via_x, start[1]), (via_x, end[1]), end],
                [MplPath.MOVETO, MplPath.LINETO, MplPath.LINETO, MplPath.LINETO]),
        fill=False, edgecolor=INK, linewidth=1.4, linestyle=style, zorder=2))
    ax.annotate("", xy=end, xytext=(via_x, end[1]),
                arrowprops={"arrowstyle": "-|>", "color": INK, "linewidth": 1.4,
                            "linestyle": style, "mutation_scale": 16}, zorder=2)
    if label:
        ax.text(via_x, (start[1] + end[1]) / 2, f" {label}", ha="left", va="center",
                fontsize=8.0, color=INK, style="italic", zorder=5)


def save_png_and_html(fig: Figure, out_dir: Path, name: str, caption: str) -> None:
    """Save the figure as a PNG and a self-contained HTML embedding the SVG + caption."""
    png = out_dir / f"{name}.png"
    fig.savefig(png, dpi=170, facecolor=PAPER, bbox_inches="tight", pad_inches=0.25)
    svg = out_dir / f"{name}.svg"
    fig.savefig(svg, facecolor=PAPER, bbox_inches="tight", pad_inches=0.25)
    svg_b64 = base64.b64encode(svg.read_bytes()).decode("ascii")
    svg.unlink()  # keep only PNG + HTML; the SVG is embedded in the HTML
    (out_dir / f"{name}.html").write_text(
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        f"<title>{name}</title>"
        "<style>body{background:#fff;color:#101114;font-family:Helvetica Neue,"
        "Arial,sans-serif;margin:0;padding:32px;display:flex;flex-direction:column;"
        "align-items:center}img{max-width:100%;height:auto;border:1px solid #e6e8ec}"
        "figcaption{margin-top:14px;font-size:13px;color:#6b7280;max-width:820px;"
        "text-align:center;line-height:1.5}</style></head><body><figure>"
        f"<img alt='{name}' src='data:image/svg+xml;base64,{svg_b64}'>"
        f"<figcaption>{caption}</figcaption></figure></body></html>\n",
        encoding="utf-8",
    )
    plt.close(fig)
