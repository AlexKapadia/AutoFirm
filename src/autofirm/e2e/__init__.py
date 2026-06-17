"""End-to-end platform validation: build AND operate diverse real companies.

This is AutoFirm's FINAL validation gate (CLAUDE.md §3.12): it drives the WHOLE
platform — the org engine, comms bus, document store, finance suite, decision
models, market-intelligence plane, human front door, artifact builders,
heartbeat scheduler and flow primitive — exactly as a human operator would, to
**build** and then **operate** several diverse companies described with REAL
PUBLIC data (publicly-stated, public-style figures; never real PII or
confidential/client data — the synthetic-only-for-sensitive rule).

Each company is stood up in its OWN fully isolated, deletable workspace under a
gitignored ``.autofirm/`` root that is injected via the workspace boundary
(:class:`autofirm.access.workspace_data_boundary.WorkspaceDataBoundary`) — NEVER
the real on-disk ``.autofirm/`` — so the entire validation corpus can be deleted
without touching the platform.

Layering (low -> high):
* :mod:`.public_company_scenarios` — the labelled "public-data only" fixture set.
* :mod:`.isolated_company_workspace` — the per-company deletable workspace + boundary.
* :mod:`.scenario_result_contract` — the structured, machine-readable result/summary.
* :mod:`.company_build_flow` — found the org, auto-create+hire on a gap, wire
  comms, file initial documents, and assert the company came up.
* :mod:`.company_operate_flow` — exercise every major feature and assert it works.
* :mod:`.end_to_end_validation_harness` — run every scenario and emit the summary
  the ``evidence/`` showcase consumes.
"""

from __future__ import annotations

from autofirm.e2e.end_to_end_validation_harness import (
    EndToEndValidationHarness,
    run_all_scenarios,
)
from autofirm.e2e.scenario_result_contract import (
    FeatureCheck,
    FeatureStatus,
    ScenarioResult,
    ValidationSummary,
)

__all__ = [
    "EndToEndValidationHarness",
    "FeatureCheck",
    "FeatureStatus",
    "ScenarioResult",
    "ValidationSummary",
    "run_all_scenarios",
]
