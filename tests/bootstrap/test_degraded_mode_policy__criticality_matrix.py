"""Adversarial + property tests for the PURE degraded-mode policy (the load-bearing matrix).

These tests are the teeth behind the mutation-critical
:func:`autofirm.bootstrap.degraded_mode_policy.decide_degraded_action`: a mutant that flips a
fail-closed branch to a hard-block or to PROCEED, or that degrades a SECURITY control, MUST
be killed here. The whole degraded-mode safety property is asserted exhaustively over the
full (criticality x present) matrix, plus boundary/adversarial cases.
"""

from __future__ import annotations

import dataclasses

import pytest
from hypothesis import given
from hypothesis import strategies as st

from autofirm.bootstrap.bootstrap_step_contract import Criticality
from autofirm.bootstrap.degraded_mode_policy import (
    DegradedAction,
    DegradedDecision,
    DependencyStatus,
    decide_degraded_action,
)

_ALL_CRITICALITIES = tuple(Criticality)


def test_degraded_action__enum_values_are_the_exact_audit_strings() -> None:
    """The enum's wire/audit string values are pinned exactly (kills value-mutating mutants).

    These strings appear in audit events and status output; a mutant that changes a value
    would silently corrupt the audit trail, so the values are asserted literally.
    """
    assert DegradedAction.PROCEED.value == "proceed"
    assert DegradedAction.DEGRADE_CAPABILITY.value == "degrade_capability"
    assert DegradedAction.FAIL_CLOSED.value == "fail_closed"


def test_decide_degraded_action__reasons_are_exact_audited_strings() -> None:
    """Each branch's reason string is pinned exactly (kills reason-string mutants).

    The reason is the explain-every-decision audit field (§3.11); a mutated reason would
    misreport WHY a capability degraded or a path was refused, so each is asserted literally.
    """
    present = decide_degraded_action(
        DependencyStatus(name="d", criticality=Criticality.OPTIONAL, present=True)
    )
    optional_absent = decide_degraded_action(
        DependencyStatus(name="d", criticality=Criticality.OPTIONAL, present=False)
    )
    security_absent = decide_degraded_action(
        DependencyStatus(name="d", criticality=Criticality.SECURITY, present=False)
    )
    assert present.reason == "dependency_present"
    assert optional_absent.reason == "optional_dependency_absent_capability_degraded"
    assert security_absent.reason == "critical_dependency_absent_path_refused"
    # The dependency name is threaded through unchanged into every decision (audit linkage).
    assert present.dependency_name == "d"


def test_degraded_decision__is_frozen_immutable() -> None:
    """A DegradedDecision is frozen (kills the ``frozen=True`` mutant).

    The decision is an audit record; it must not be mutable after the fact, so attempting to
    mutate it raises FrozenInstanceError.
    """
    decision = decide_degraded_action(
        DependencyStatus(name="d", criticality=Criticality.OPTIONAL, present=False)
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        decision.action = DegradedAction.PROCEED  # type: ignore[misc]


def test_dependency_status__is_frozen_immutable() -> None:
    """A DependencyStatus is frozen so the observed input cannot drift mid-decision."""
    status = DependencyStatus(name="d", criticality=Criticality.OPTIONAL, present=False)
    with pytest.raises(dataclasses.FrozenInstanceError):
        status.present = True  # type: ignore[misc]


def test_degraded_decision__round_trips_its_fields() -> None:
    """Sanity: DegradedDecision carries name/action/reason faithfully (constructed value type)."""
    decision = DegradedDecision(
        dependency_name="x", action=DegradedAction.FAIL_CLOSED, reason="r"
    )
    assert (decision.dependency_name, decision.action, decision.reason) == (
        "x",
        DegradedAction.FAIL_CLOSED,
        "r",
    )


@pytest.mark.parametrize("criticality", _ALL_CRITICALITIES)
def test_decide_degraded_action__present_dependency_always_proceeds(
    criticality: Criticality,
) -> None:
    """A PRESENT dependency PROCEEDs regardless of criticality (the only path that runs)."""
    decision = decide_degraded_action(
        DependencyStatus(name="dep:x", criticality=criticality, present=True)
    )
    assert decision.action is DegradedAction.PROCEED


def test_decide_degraded_action__absent_optional_degrades_capability_only() -> None:
    """An ABSENT OPTIONAL dependency degrades ONLY its capability (bulkhead; platform UP)."""
    decision = decide_degraded_action(
        DependencyStatus(name="provider:anthropic", criticality=Criticality.OPTIONAL, present=False)
    )
    # Bulkhead (§5.6): degrade that capability — NOT proceed (would open a missing path) and
    # NOT fail-closed (an optional gap must never refuse the platform).
    assert decision.action is DegradedAction.DEGRADE_CAPABILITY


def test_decide_degraded_action__absent_security_fails_closed() -> None:
    """An ABSENT SECURITY control FAILS CLOSED — never degraded-to-off, never opened."""
    status = DependencyStatus(
        name="control:secret_scan", criticality=Criticality.SECURITY, present=False
    )
    decision = decide_degraded_action(status)
    # The mutation-critical assertion: a missing security control must FAIL_CLOSED. A mutant
    # that returns PROCEED (opens an unsafe path) or DEGRADE_CAPABILITY (silently turns the
    # control off) is killed here.
    assert decision.action is DegradedAction.FAIL_CLOSED
    assert decision.action is not DegradedAction.DEGRADE_CAPABILITY
    assert decision.action is not DegradedAction.PROCEED


def test_decide_degraded_action__absent_required_fails_closed_not_degraded() -> None:
    """An ABSENT REQUIRED dependency FAILS CLOSED for that path (not silently degraded)."""
    decision = decide_degraded_action(
        DependencyStatus(name="store:state", criticality=Criticality.REQUIRED, present=False)
    )
    assert decision.action is DegradedAction.FAIL_CLOSED
    assert decision.action is not DegradedAction.DEGRADE_CAPABILITY


def test_decide_degraded_action__no_whole_platform_block_member_exists() -> None:
    """There is deliberately NO whole-platform-halt action — the worst case is per-path.

    This guards the design mandate (§5.6, B3 §2 "never a whole-platform hard block"): the
    action enum must offer only PROCEED / DEGRADE_CAPABILITY / FAIL_CLOSED. If a future edit
    adds a "BLOCK_PLATFORM" member, this test fails loudly.
    """
    assert {a.name for a in DegradedAction} == {"PROCEED", "DEGRADE_CAPABILITY", "FAIL_CLOSED"}


@given(
    criticality=st.sampled_from(_ALL_CRITICALITIES),
    present=st.booleans(),
)
def test_decide_degraded_action__never_blocks_and_only_proceeds_when_present(
    criticality: Criticality,
    present: bool,
) -> None:
    """Property over the FULL matrix: PROCEED iff present; absent => degrade/fail-closed only.

    The two load-bearing invariants, asserted for every (criticality, present) pair:
    (1) a path PROCEEDs if and ONLY if the dependency is present (absence never runs a path);
    (2) the action is always one of the three allowed outcomes (never a platform block).
    """
    decision = decide_degraded_action(
        DependencyStatus(name="dep:any", criticality=criticality, present=present)
    )
    assert (decision.action is DegradedAction.PROCEED) == present
    assert decision.action in {
        DegradedAction.PROCEED,
        DegradedAction.DEGRADE_CAPABILITY,
        DegradedAction.FAIL_CLOSED,
    }
    if not present and criticality is not Criticality.OPTIONAL:
        # An absent critical dependency must ALWAYS fail closed — never degrade silently.
        assert decision.action is DegradedAction.FAIL_CLOSED


def test_decide_degraded_action__reason_is_deterministic_and_distinct_per_branch() -> None:
    """Each branch carries a distinct, deterministic reason (explain-every-decision §3.11)."""
    proceed = decide_degraded_action(
        DependencyStatus(name="d", criticality=Criticality.OPTIONAL, present=True)
    ).reason
    degrade = decide_degraded_action(
        DependencyStatus(name="d", criticality=Criticality.OPTIONAL, present=False)
    ).reason
    failed = decide_degraded_action(
        DependencyStatus(name="d", criticality=Criticality.SECURITY, present=False)
    ).reason
    assert len({proceed, degrade, failed}) == 3  # three distinct reasons, no collisions
