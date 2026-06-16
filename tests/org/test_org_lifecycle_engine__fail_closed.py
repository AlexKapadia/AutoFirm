"""Engine fail-closed tests: every refused transition is denied AND audited.

Exercises each adversarial path the engine must refuse — spawn without a valid
spec, self-authoring, authoring by a non-manager, double-assigned artifact, cyclic
re-parent, firing the root, firing a manager with orphaned reports — and asserts
(a) the operation raises :class:`RoleLifecycleError`, (b) the refusal is recorded as
``MUTATION_REFUSED`` on the error's audited state, and (c) the original engine is
left immutable. Synthetic only; no network (CLAUDE.md §3.6/§5.5/§5.6).
"""

from __future__ import annotations

import pytest

from autofirm.org.gap_detection_contract import GapKind, OrgGap
from autofirm.org.org_identifiers import ArtifactId, RoleId, SequentialIdGenerator
from autofirm.org.org_lifecycle_engine import DynamicOrg, RoleLifecycleError
from autofirm.org.org_lifecycle_events import OrgEventKind
from autofirm.org.role_charter_contract import ROOT_AUTHOR, RoleCharter

from .synthetic_org_factory import charter, founded_org, fresh_clock, root_charter


def _assert_refused_and_audited(call) -> str:
    """Run ``call`` expecting a refusal; assert the denial was audited. Returns reason."""
    with pytest.raises(RoleLifecycleError) as exc:
        call()
    # The denial is recorded (not dropped) on the error's audited state (§5.6).
    assert exc.value.audited_state.trail.kinds()[-1] is OrgEventKind.MUTATION_REFUSED
    return str(exc.value)


# --------------------------------------------------------------------------- #
# found() guards                                                              #
# --------------------------------------------------------------------------- #


@pytest.mark.security
def test_found_refuses_root_not_authored_by_founder() -> None:
    bad_root = RoleCharter(
        role_id=RoleId("ceo"), title="CEO", responsibilities=("run",),
        ownership_scope="all", success_signal="value",
        owned_artifacts=frozenset(), manager_id=None, authored_by=RoleId("someone"),
    )
    with pytest.raises(RoleLifecycleError):
        DynamicOrg.found(bad_root, fresh_clock(), SequentialIdGenerator())


# --------------------------------------------------------------------------- #
# hire() guards                                                               #
# --------------------------------------------------------------------------- #


@pytest.mark.security
def test_hire_refuses_root_charter() -> None:
    org = founded_org()
    before = org.state.trail.kinds()
    _assert_refused_and_audited(lambda: org.hire(root_charter("rogue")))
    assert org.state.trail.kinds() == before  # original immutable


@pytest.mark.security
def test_hire_refuses_unknown_manager() -> None:
    org = founded_org()
    _assert_refused_and_audited(lambda: org.hire(charter("x", "ghost", "ghost")))


@pytest.mark.security
def test_hire_refuses_spec_not_authored_by_manager() -> None:
    org = founded_org()
    # ceo exists and is the manager, but the spec claims a different author -> deny.
    _assert_refused_and_audited(lambda: org.hire(charter("x", "ceo", "x")))


@pytest.mark.security
def test_hire_refuses_double_assigned_artifact() -> None:
    org = founded_org("ceo", artifacts=frozenset({"shared.md"}))
    # ceo already owns shared.md; a new role claiming it must be refused (single-writer).
    reason = _assert_refused_and_audited(
        lambda: org.hire(charter("cfo", "ceo", "ceo", frozenset({"shared.md"}))),
    )
    assert "single-writer" in reason
    assert org.state.ownership.owner_of(ArtifactId("shared.md")) == RoleId("ceo")


# --------------------------------------------------------------------------- #
# rescope() guards                                                            #
# --------------------------------------------------------------------------- #


@pytest.mark.security
def test_rescope_refuses_unknown_role() -> None:
    org = founded_org()
    _assert_refused_and_audited(lambda: org.rescope(charter("ghost", "ceo", "ceo")))


@pytest.mark.security
def test_rescope_refuses_root_ness_flip() -> None:
    org = founded_org().hire(charter("cfo", "ceo", "ceo"))
    # Trying to promote cfo to a root (manager_id None) is refused.
    promote = RoleCharter(
        role_id=RoleId("cfo"), title="CFO", responsibilities=("x",),
        ownership_scope="s", success_signal="f", owned_artifacts=frozenset(),
        manager_id=None, authored_by=ROOT_AUTHOR,
    )
    _assert_refused_and_audited(lambda: org.rescope(promote))


@pytest.mark.security
def test_rescope_refuses_claiming_another_roles_artifact() -> None:
    org = (
        founded_org()
        .hire(charter("a", "ceo", "ceo", frozenset({"a-owned.md"})))
        .hire(charter("b", "ceo", "ceo"))
    )
    # Re-scope b to claim a-owned.md (owned by a) -> single-writer refuses it via the
    # rescope artifact-reassignment path.
    reason = _assert_refused_and_audited(
        lambda: org.rescope(charter("b", "ceo", "ceo", frozenset({"a-owned.md"}))),
    )
    assert "single-writer" in reason
    assert org.state.ownership.owner_of(ArtifactId("a-owned.md")) == RoleId("a")


@pytest.mark.security
def test_rescope_refuses_cycle() -> None:
    org = (
        founded_org()
        .hire(charter("a", "ceo", "ceo"))
        .hire(charter("b", "a", "a"))
    )
    # Re-parent a under its own descendant b -> reporting cycle -> refused.
    _assert_refused_and_audited(lambda: org.rescope(charter("a", "b", "b")))


# --------------------------------------------------------------------------- #
# fire() guards                                                               #
# --------------------------------------------------------------------------- #


@pytest.mark.security
def test_fire_refuses_root() -> None:
    org = founded_org()
    _assert_refused_and_audited(lambda: org.fire(RoleId("ceo")))


@pytest.mark.security
def test_fire_refuses_unknown_role() -> None:
    org = founded_org()
    _assert_refused_and_audited(lambda: org.fire(RoleId("ghost")))


@pytest.mark.security
def test_fire_manager_with_reports_without_reassignment_is_refused() -> None:
    org = founded_org().hire(charter("cfo", "ceo", "ceo")).hire(charter("fp", "cfo", "cfo"))
    _assert_refused_and_audited(lambda: org.fire(RoleId("cfo")))


@pytest.mark.security
def test_fire_with_invalid_reassignment_target_is_refused() -> None:
    org = founded_org().hire(charter("cfo", "ceo", "ceo")).hire(charter("fp", "cfo", "cfo"))
    _assert_refused_and_audited(
        lambda: org.fire(RoleId("cfo"), reassign_reports_to=RoleId("ghost")),
    )


# --------------------------------------------------------------------------- #
# auto_create_on_gap() guards                                                 #
# --------------------------------------------------------------------------- #


@pytest.mark.security
def test_auto_create_refuses_unknown_detector() -> None:
    org = founded_org()
    gap = OrgGap(kind=GapKind.SHORTAGE, detected_by=RoleId("ghost"), rationale="r", severity=1)
    _assert_refused_and_audited(
        lambda: org.auto_create_on_gap(gap, charter("x", "ghost", "ghost")),
    )


@pytest.mark.security
def test_auto_create_refuses_role_outside_detector_command() -> None:
    org = founded_org().hire(charter("cfo", "ceo", "ceo"))
    # Detector is cfo, but the new role reports to/authored by ceo -> outside cfo's
    # command -> refused (decision-gated authorship).
    gap = OrgGap(kind=GapKind.SKILL_GAP, detected_by=RoleId("cfo"), rationale="r", severity=2)
    _assert_refused_and_audited(
        lambda: org.auto_create_on_gap(gap, charter("tax", "ceo", "ceo")),
    )
