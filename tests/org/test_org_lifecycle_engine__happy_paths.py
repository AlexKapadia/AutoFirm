"""Engine efficacy tests: the lifecycle does its job correctly and exactly.

Proves the accepted transitions produce the right org shape, ownership, and a
complete, exact audit trail — determinism included (CLAUDE.md §3.6 "prove it is
GOOD at its job", §3.11 exactness). Synthetic only; no network.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from autofirm.org.gap_detection_contract import GapKind, OrgGap
from autofirm.org.org_identifiers import ArtifactId, RoleId, SequentialIdGenerator
from autofirm.org.org_lifecycle_engine import DynamicOrg
from autofirm.org.org_lifecycle_events import OrgEventKind

from .synthetic_org_factory import EPOCH, charter, founded_org, fresh_clock, root_charter


@pytest.mark.unit
def test_found_seeds_root_and_audits_exactly_one_event() -> None:
    org = founded_org("ceo", artifacts=frozenset({"c.md"}))
    assert org.state.hierarchy.root_id() == RoleId("ceo")
    assert org.state.ownership.owner_of(ArtifactId("c.md")) == RoleId("ceo")
    assert org.state.trail.kinds() == (OrgEventKind.ROLE_HIRED,)
    assert org.state.trail.events[0].timestamp == EPOCH  # deterministic clock


@pytest.mark.unit
def test_hire_adds_report_claims_artifacts_and_audits() -> None:
    org = founded_org().hire(charter("cfo", "ceo", "ceo", frozenset({"budget.xlsx"})))
    assert org.state.hierarchy.direct_reports(RoleId("ceo")) == {RoleId("cfo")}
    assert org.state.ownership.owner_of(ArtifactId("budget.xlsx")) == RoleId("cfo")
    assert org.state.trail.kinds() == (OrgEventKind.ROLE_HIRED, OrgEventKind.ROLE_HIRED)


@pytest.mark.unit
def test_rescope_releases_old_and_claims_new_artifacts() -> None:
    org = founded_org().hire(charter("cfo", "ceo", "ceo", frozenset({"old.xlsx"})))
    org = org.rescope(charter("cfo", "ceo", "ceo", frozenset({"new.xlsx"})))
    assert org.state.ownership.owner_of(ArtifactId("old.xlsx")) is None  # released
    assert org.state.ownership.owner_of(ArtifactId("new.xlsx")) == RoleId("cfo")
    assert org.state.trail.kinds()[-1] is OrgEventKind.ROLE_RESCOPED


@pytest.mark.unit
def test_rescope_can_reparent_to_a_valid_new_manager() -> None:
    org = (
        founded_org()
        .hire(charter("a", "ceo", "ceo"))
        .hire(charter("b", "ceo", "ceo"))
        .hire(charter("c", "a", "a"))
    )
    # Move c from a to b (b is not below c) -> allowed.
    org = org.rescope(charter("c", "b", "b"))
    assert org.state.hierarchy.charter(RoleId("c")).manager_id == RoleId("b")


@pytest.mark.unit
def test_fire_leaf_releases_artifacts_and_removes_role() -> None:
    org = founded_org().hire(charter("cfo", "ceo", "ceo", frozenset({"b.xlsx"})))
    org = org.fire(RoleId("cfo"))
    assert RoleId("cfo") not in org.state.hierarchy
    assert org.state.ownership.owner_of(ArtifactId("b.xlsx")) is None
    assert org.state.trail.kinds()[-1] is OrgEventKind.ROLE_FIRED


@pytest.mark.unit
def test_fire_manager_reassigns_reports_then_removes_with_no_orphans() -> None:
    org = (
        founded_org()
        .hire(charter("cfo", "ceo", "ceo"))
        .hire(charter("fp", "cfo", "cfo"))
        .hire(charter("tax", "cfo", "cfo"))
    )
    org = org.fire(RoleId("cfo"), reassign_reports_to=RoleId("ceo"))
    assert RoleId("cfo") not in org.state.hierarchy
    # Both reports re-parented to ceo (no orphans) — deterministic sorted order.
    assert org.state.hierarchy.charter(RoleId("fp")).manager_id == RoleId("ceo")
    assert org.state.hierarchy.charter(RoleId("tax")).manager_id == RoleId("ceo")
    kinds = org.state.trail.kinds()
    assert kinds[-1] is OrgEventKind.ROLE_FIRED
    assert kinds.count(OrgEventKind.REPORTS_REASSIGNED) == 2


@pytest.mark.unit
def test_auto_create_on_gap_full_pipeline() -> None:
    org = founded_org()
    gap = OrgGap(
        kind=GapKind.SKILL_GAP, detected_by=RoleId("ceo"), rationale="need tax", severity=4
    )
    org = org.auto_create_on_gap(gap, charter("tax", "ceo", "ceo"))
    assert RoleId("tax") in org.state.hierarchy
    last = org.state.trail.events[-1]
    assert last.kind is OrgEventKind.ROLE_AUTO_CREATED
    # The 'why' carries the gap kind and rationale (explainability, §3.11).
    assert "SKILL_GAP" in last.detail and "need tax" in last.detail


@pytest.mark.unit
def test_audit_timestamps_advance_with_clock() -> None:
    org = founded_org().hire(charter("cfo", "ceo", "ceo"))
    events = org.state.trail.events
    assert events[0].timestamp == EPOCH
    assert events[1].timestamp == EPOCH + timedelta(seconds=1)  # step clock


@pytest.mark.unit
def test_same_inputs_yield_identical_trail_determinism() -> None:
    def build() -> tuple[object, ...]:
        org = DynamicOrg.found(root_charter("ceo"), fresh_clock(), SequentialIdGenerator())
        org = org.hire(charter("a", "ceo", "ceo")).hire(charter("b", "a", "a"))
        org = org.fire(RoleId("a"), reassign_reports_to=RoleId("ceo"))
        return tuple(
            (e.seq, e.kind, e.subject_role_id, e.detail, e.timestamp)
            for e in org.state.trail.events
        )

    assert build() == build()  # identical inputs -> identical audit trail
