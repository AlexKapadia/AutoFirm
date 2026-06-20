"""Shared chart styling + measured-data loaders for the output-review graphs.

Analysis-only (CLAUDE.md §3.10): imported solely by the graph render scripts under
``evidence/output_review/graphs/``; never by any runtime module. Centralises a
restrained, premium house style (deliberate type + spacing scale, a single accent,
no rainbow chartjunk — CLAUDE.md §3.14 anti-AI-slop) so every figure looks part of
one set, and the loaders that read the MEASURED numbers from ``_measured/`` so no
chart ever hard-codes a value.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib as mpl

_MEASURED = Path(__file__).resolve().parent.parent / "_measured"
OUT_DIR = Path(__file__).resolve().parent

# --- house palette: ink + greys + one positive accent + one risk accent ----------
INK = "#16181d"  # near-black for text / axes / good bars
MID_GREY = "#8a8f98"  # secondary text / gridlines
LIGHT_GREY = "#e6e8ec"  # fills / faint grid
GOOD = "#1f7a4d"  # measured-good (100% detection, 0 escape, full coverage)
RISK = "#b23b3b"  # the un-reviewed-human risk baseline / target line
PAPER = "#ffffff"

# Plotly equivalents (string colours reused so PNG and HTML match).
PLOTLY_FONT = "Helvetica Neue, Helvetica, Arial, sans-serif"


def apply_matplotlib_house_style() -> None:
    """Set a clean, consistent rcParams house style for every PNG."""
    mpl.rcParams.update(
        {
            "figure.facecolor": PAPER,
            "axes.facecolor": PAPER,
            "savefig.facecolor": PAPER,
            "font.family": "sans-serif",
            "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
            "font.size": 11,
            "axes.titlesize": 15,
            "axes.titleweight": "bold",
            "axes.labelsize": 11.5,
            "axes.edgecolor": INK,
            "axes.linewidth": 0.9,
            "axes.grid": True,
            "axes.axisbelow": True,
            "grid.color": LIGHT_GREY,
            "grid.linewidth": 0.8,
            "xtick.color": INK,
            "ytick.color": INK,
            "text.color": INK,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.dpi": 160,
            "savefig.dpi": 160,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.3,
        }
    )


def load_efficacy() -> dict[str, Any]:
    """Measured efficacy metrics (detection, escape, false-positive, determinism)."""
    return json.loads((_MEASURED / "efficacy_metrics.json").read_text(encoding="utf-8"))


def load_coverage() -> dict[str, Any]:
    """Measured coverage report (line + branch totals, per file)."""
    return json.loads((_MEASURED / "coverage.json").read_text(encoding="utf-8"))


def load_mutation() -> dict[str, Any]:
    """Cited per-module mutation-gate summary (all survivors 0, score 1.0)."""
    return json.loads(
        (_MEASURED / "mutation_gate_summary.json").read_text(encoding="utf-8")
    )


def caption(fig: Any, text: str) -> None:
    """Add a small, consistent provenance caption under a matplotlib figure."""
    fig.text(
        0.5,
        -0.02,
        text,
        ha="center",
        va="top",
        fontsize=8.5,
        color=MID_GREY,
        style="italic",
    )
