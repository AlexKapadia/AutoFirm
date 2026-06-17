"""Build-flow teeth: hiring + AUTOMATIC role-creation, comms, filing, and audit.

Goes beyond the green/red verdict and inspects the real platform state the build
produced: the auto-created role is actually present in the live hierarchy, its
creation is recorded as a ROLE_AUTO_CREATED event whose detail carries the gap
rationale (explainability — the 'why' matches the 'what'), the kickoff message
reached the new role's handler and was audited, and the founding document was
catalogued under the company's isolated store. Determinism is asserted directly.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from autofirm.e2e.company_build_flow import CEO_ROLE, build_company
from autofirm.e2e.isolated_company_workspace import create_isolated_company_workspace
from autofirm.e2e.public_company_scenarios import (
    PublicCompanyScenario,
    public_company_scenarios,
)
from autofirm.e2e.scenario_result_contract import FeatureName
from autofirm.org.org_identifiers import RoleId
from autofirm.org.org_lifecycle_events import OrgEventKind

_SCENARIOS = public_company_scenarios()
_IDS = [s.slug for s in _SCENARIOS]


def _build(scenario: PublicCompanyScenario, corpus_dir: Path):  # type: ignore[no-untyped-def]
    workspace = create_isolated_company_workspace(
        company_slug=scenario.slug, corpus_dir=corpus_dir
    )
    return build_company(scenario, workspace), workspace


@pytest.mark.parametrize("scenario", _SCENARIOS, ids=_IDS)
def test_gap_auto_creates_and_hires_the_missing_role(
    scenario: PublicCompanyScenario, corpus_dir: Path
) -> None:
    """The detected capability gap auto-creates + hires the scenario's role in the live org."""
    built, _ = _build(scenario, corpus_dir)
    hierarchy = built.org.state.hierarchy
    # The new role is genuinely present and reports to the CEO (a real org edge).
    assert RoleId(scenario.gap_role_id) in hierarchy
    assert hierarchy.charter(RoleId(scenario.gap_role_id)).manager_id == RoleId(CEO_ROLE)


@pytest.mark.parametrize("scenario", _SCENARIOS, ids=_IDS)
def test_auto_create_event_carries_the_gap_rationale(
    scenario: PublicCompanyScenario, corpus_dir: Path
) -> None:
    """The auto-creation is audited as ROLE_AUTO_CREATED with the gap's 'why' (explainability)."""
    built, _ = _build(scenario, corpus_dir)
    last = built.org.state.trail.events[-1]
    assert last.kind is OrgEventKind.ROLE_AUTO_CREATED
    # The audited 'why' must restate the exact gap rationale — why == what (§3.11).
    assert scenario.gap_rationale in last.detail


@pytest.mark.parametrize("scenario", _SCENARIOS, ids=_IDS)
def test_founding_document_is_filed_under_the_isolated_store(
    scenario: PublicCompanyScenario, corpus_dir: Path
) -> None:
    """The founding charter is catalogued for exactly this company in its own store."""
    built, _ = _build(scenario, corpus_dir)
    filed = built.librarian.find(company=scenario.slug)
    assert len(filed) == 1
    assert filed[0].record.logical_id == "founding-charter"
    # The filed path resolves under the company's gitignored .autofirm root.
    assert ".autofirm" in filed[0].absolute_path


@pytest.mark.parametrize("scenario", _SCENARIOS, ids=_IDS)
def test_build_checks_are_all_green_and_named(
    scenario: PublicCompanyScenario, corpus_dir: Path
) -> None:
    """The four build-phase features (org/gap/comms/docs) each pass and are present."""
    built, _ = _build(scenario, corpus_dir)
    by_feature = {c.feature: c for c in built.checks}
    expected = {
        FeatureName.ORG_FOUNDED,
        FeatureName.GAP_AUTO_CREATE_HIRE,
        FeatureName.COMMS_WIRED,
        FeatureName.DOCUMENTS_FILED,
    }
    assert set(by_feature) == expected
    assert all(check.passed() for check in built.checks)


def test_build_is_deterministic_for_a_fixed_scenario(corpus_dir: Path) -> None:
    """Identical scenario inputs produce an identical build audit trail (determinism §3.11)."""
    scenario = _SCENARIOS[0]

    def trail_fingerprint() -> tuple[object, ...]:
        built, _ = _build(scenario, corpus_dir / "run")
        return tuple(
            (e.seq, e.kind, e.subject_role_id, e.detail) for e in built.org.state.trail.events
        )

    first = trail_fingerprint()
    second = trail_fingerprint()
    assert first == second
