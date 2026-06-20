"""One entry point to render every output-review evidence graph (PNG + HTML).

Analysis-only (CLAUDE.md §3.10). Runs the efficacy and quality renderers in turn so
the whole graph set regenerates with one command:

    python evidence/output_review/graphs/render_all_graphs.py

Requires ``pip install -r evidence/output_review/requirements-analysis.txt`` and the
measured data under ``_measured/`` (run the harness first). Imports are flat sibling
imports (the script dir is added to sys.path), matching the evidence/ convention.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import render_efficacy_graphs  # noqa: E402
import render_quality_graphs  # noqa: E402


def main() -> None:
    """Render efficacy graphs then quality graphs."""
    render_efficacy_graphs.main()
    render_quality_graphs.main()


if __name__ == "__main__":
    main()
