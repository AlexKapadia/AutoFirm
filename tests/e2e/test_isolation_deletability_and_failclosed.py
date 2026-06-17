"""Isolation, deletability, public-data-only labelling, and fail-closed guards.

Proves the corpus is fully contained under the test's tmp_path (NEVER the real
.autofirm), that teardown removes every company without residue, that every
result is labelled "public-data only", and that the front-door / artifact / flow
checks and the per-company fail-closed edge case all hold. The boundary's own
traversal refusal is exercised so the isolation guarantee is the REAL one.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from autofirm.access.workspace_data_boundary import WorkspaceBoundaryError
from autofirm.e2e.company_build_flow import build_company
from autofirm.e2e.company_operate_flow import operate_company
from autofirm.e2e.end_to_end_validation_harness import (
    PUBLIC_DATA_LABEL,
    EndToEndValidationHarness,
)
from autofirm.e2e.isolated_company_workspace import create_isolated_company_workspace
from autofirm.e2e.public_company_scenarios import (
    PublicCompanyScenario,
    public_company_scenarios,
)
from autofirm.e2e.scenario_result_contract import (
    FeatureName,
    FeatureStatus,
    ValidationSummary,
)

_SCENARIOS = public_company_scenarios()
_IDS = [s.slug for s in _SCENARIOS]


def test_everything_written_stays_under_the_corpus_dir(
    harness: EndToEndValidationHarness, corpus_dir: Path
) -> None:
    """Every artifact + result file the run writes lives under the deletable corpus dir."""
    summary = harness.run()
    for scenario in summary.scenarios:
        root = Path(scenario.workspace_root)
        # The company root is nested under the corpus dir (no escape to the real FS).
        assert corpus_dir in root.parents
        assert root.name == ".autofirm"
        assert (root / "scenario-result.json").exists()
        assert (root / "deliverables" / "investor-update.docx").stat().st_size > 0


def test_teardown_deletes_the_whole_corpus_without_residue(
    harness: EndToEndValidationHarness,
) -> None:
    """teardown() removes every company workspace; nothing is left behind (deletability)."""
    summary = harness.run()
    roots = [Path(s.workspace_root) for s in summary.scenarios]
    assert all(root.exists() for root in roots)
    harness.teardown()
    assert all(not root.exists() for root in roots)


def test_every_result_is_labelled_public_data_only(summary: ValidationSummary) -> None:
    """Each scenario result carries the binding 'public-data only' provenance label (§3.12)."""
    assert summary.scenarios  # non-empty corpus
    assert all(s.data_source == PUBLIC_DATA_LABEL for s in summary.scenarios)


def test_boundary_refuses_traversal_for_a_company_workspace(corpus_dir: Path) -> None:
    """The real fail-closed boundary refuses a '..' escape from a company's store."""
    workspace = create_isolated_company_workspace(company_slug="probe", corpus_dir=corpus_dir)
    with pytest.raises(WorkspaceBoundaryError):
        workspace.boundary.resolve_sensitive_path("../escape.txt")
    with pytest.raises(WorkspaceBoundaryError):
        workspace.sensitive_dir("../../outside")


@pytest.mark.parametrize("scenario", _SCENARIOS, ids=_IDS)
def test_fail_closed_guard_refuses_malformed_pricing(
    scenario: PublicCompanyScenario, corpus_dir: Path
) -> None:
    """The per-company edge case: an inelastic pricing input is refused, not answered."""
    workspace = create_isolated_company_workspace(
        company_slug=scenario.slug, corpus_dir=corpus_dir
    )
    built = build_company(scenario, workspace)
    checks = operate_company(scenario, built.recording_org, built.librarian, workspace)
    guard = next(c for c in checks if c.feature is FeatureName.FAIL_CLOSED_GUARD)
    assert guard.status is FeatureStatus.PASSED
    assert guard.evidence["refused"] == "True"


@pytest.mark.parametrize("scenario", _SCENARIOS, ids=_IDS)
def test_front_door_artifact_and_flow_reach_real_outcomes(
    scenario: PublicCompanyScenario, corpus_dir: Path
) -> None:
    """Front-door routing, the filed real artifact, and the flow handoff all pass."""
    workspace = create_isolated_company_workspace(
        company_slug=scenario.slug, corpus_dir=corpus_dir
    )
    built = build_company(scenario, workspace)
    operate_checks = operate_company(scenario, built.recording_org, built.librarian, workspace)
    checks = {c.feature: c for c in operate_checks}

    front = checks[FeatureName.FRONT_DOOR_ROUTING]
    assert front.status is FeatureStatus.PASSED
    assert front.evidence["handler_role"] != ""  # a real handler received the question

    artifact = checks[FeatureName.ARTIFACT_GENERATED]
    assert artifact.status is FeatureStatus.PASSED
    assert int(artifact.evidence["bytes"]) > 0  # a real, non-empty .docx

    flow = checks[FeatureName.FLOW_HANDOFF]
    assert flow.status is FeatureStatus.PASSED
    assert flow.evidence["final_state"] == "DONE"


def test_run_all_scenarios_entry_point_is_all_green(corpus_dir: Path) -> None:
    """The showcase entry point runs the full corpus and returns an all-green summary."""
    from autofirm.e2e import run_all_scenarios

    result = run_all_scenarios(corpus_dir)
    assert result.scenarios_all_green() == result.total_scenarios()
    assert result.total_scenarios() >= 3


def test_two_runs_produce_identical_summaries(corpus_dir: Path) -> None:
    """The whole validation is deterministic: two runs yield the same pass matrix + counts."""
    first = EndToEndValidationHarness(corpus_dir / "a").run()
    second = EndToEndValidationHarness(corpus_dir / "b").run()
    assert first.feature_matrix() == second.feature_matrix()
    assert first.checks_passed() == second.checks_passed()
    assert first.total_checks() == second.total_checks()
