"""Regenerate the entire evidence showcase from real data in one command.

Runs the collector (real coverage + real e2e harness) then every graph, diagram
and stats generator in order, so the showcase is fully reproducible:
``python evidence/generators/run_all.py``. Assumes the coverage report and test
count already exist under ``evidence/_raw/`` (written by the pytest run the README
documents); it does not re-run pytest itself. Analysis-only.
"""

from __future__ import annotations

import collect_real_evidence
import render_activation_lifecycle_flow
import render_build_operate_flow
import render_cockpit_control_plane_flow
import render_company_financials
import render_coverage_bar
import render_e2e_matrix
import render_output_review_gate_flow
import render_statistics_page
import render_system_architecture


def main() -> None:
    """Rebuild the collected evidence payload, then every showcase artifact."""
    # 1. Collect: real coverage rollup + real e2e validation into one JSON.
    payload = collect_real_evidence.write_payload()
    print(f"collected real evidence: tests={payload['test_count']}")

    # 2. Graphs (PNG + interactive HTML).
    render_coverage_bar.main()
    render_e2e_matrix.main()
    render_company_financials.main()

    # 3. Flow diagrams (B&W, PNG + HTML) — whole-system + per-component.
    render_system_architecture.main()
    render_build_operate_flow.main()
    render_activation_lifecycle_flow.main()
    render_output_review_gate_flow.main()
    render_cockpit_control_plane_flow.main()

    # 4. Statistical-evidence page (consumes the artifacts above).
    render_statistics_page.main()

    print("evidence showcase regenerated.")


if __name__ == "__main__":
    main()
