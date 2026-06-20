"""One entry point to render every output-review flow diagram (B&W PNG + HTML).

Analysis-only (CLAUDE.md §3.10). Renders the three component diagrams and the
whole-system diagram with one command:

    python evidence/output_review/diagrams/render_all_diagrams.py

Requires ``pip install -r evidence/output_review/requirements-analysis.txt``. Flat
sibling imports (the script dir is added to sys.path), matching the evidence/
convention. No Graphviz `dot` is needed — diagrams are drawn with matplotlib.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import render_component_diagrams  # noqa: E402
import render_system_diagram  # noqa: E402


def main() -> None:
    """Render component diagrams then the whole-system diagram."""
    render_component_diagrams.main()
    render_system_diagram.main()


if __name__ == "__main__":
    main()
