"""Shared black-&-white visual style + data loading for every showcase generator.

One place defines the institution-grade look (typography, B&W palette, generous
margins) so every PNG and diagram is visually consistent and clean — no clipping,
no overlap, deliberate spacing (CLAUDE.md §3.10, §3.14). Analysis-only.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib as mpl

_HERE = Path(__file__).resolve().parent
EVIDENCE_DIR = _HERE.parent
RAW_DIR = EVIDENCE_DIR / "_raw"
GRAPHS_DIR = EVIDENCE_DIR / "graphs"
DIAGRAMS_DIR = EVIDENCE_DIR / "diagrams"
STATS_DIR = EVIDENCE_DIR / "stats"
_DATA = RAW_DIR / "evidence_data.json"

# Institution-grade B&W palette: paper white, near-black ink, two greys for fills.
INK = "#111111"
PAPER = "#ffffff"
GREY_DARK = "#3a3a3a"
GREY_MID = "#6f6f6f"
GREY_LIGHT = "#d6d6d6"
GREY_FAINT = "#ededed"

# The DPI every PNG is rendered at: crisp on a high-density README without bloat.
PNG_DPI = 200


def apply_house_style() -> None:
    """Install the shared matplotlib rcParams (call once per generator process)."""
    mpl.rcParams.update(
        {
            "figure.facecolor": PAPER,
            "axes.facecolor": PAPER,
            "savefig.facecolor": PAPER,
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "axes.edgecolor": INK,
            "axes.labelcolor": INK,
            "axes.titlecolor": INK,
            "axes.linewidth": 1.0,
            "xtick.color": INK,
            "ytick.color": INK,
            "text.color": INK,
            "axes.grid": False,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.autolayout": False,  # we set explicit margins for tight control
        }
    )


def load_evidence() -> dict:
    """Load the single real-evidence payload produced by ``collect_real_evidence``."""
    return json.loads(_DATA.read_text(encoding="utf-8"))


def package_coverage_rows() -> list[tuple[str, float, float]]:
    """Return (package, line%, branch%) rows for the 18 real platform packages.

    The trivial ``autofirm`` root ``__init__`` (a single statement, no behaviour)
    is excluded so the chart grids the genuine components only.
    """
    data = load_evidence()["per_package_coverage"]
    rows = [
        (pkg, c["line_pct"], c["branch_pct"])
        for pkg, c in data.items()
        if pkg != "autofirm"
    ]
    return sorted(rows, key=lambda row: row[0])
