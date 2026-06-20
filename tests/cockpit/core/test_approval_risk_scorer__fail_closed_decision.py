"""Adversarial + property tests for the fail-closed approval decision — security-critical.

The scorer governs what agents may do UNATTENDED, so the suite is built to FAIL if any
edge leaks toward auto-approval (CLAUDE.md §3.6, §5.6). It pins: the per-tier truth table
for the auto-approvable case; that every always-gated kind, every irreversible/critical
action, and every tier-forbidden kind escalate to a human (never auto); that the most
dangerous combination is refused outright; monotonicity (raising risk never makes a
decision MORE permissive); and fail-closed behaviour against malformed inputs. No
tautological asserts — every assertion targets a specific mutant.
"""

from __future__ import annotations

import itertools

import pytest
from hypothesis import given
from hypothesis import strategies as st

from autofirm.cockpit.core.approval_risk_model import (
    ApprovalDecision,
    PendingAction,
    ReversibilityClass,
    RiskLevel,
)
from autofirm.cockpit.core.approval_risk_scorer import decide_approval
from autofirm.cockpit.core.autonomy_tier_model import (
    ActionKind,
    AutonomyTier,
    tier_permits,
)

# --- builders --------------------------------------------------------------------------


def _benign(
    *,
    kind: ActionKind = ActionKind.READ,
    risk: RiskLevel = RiskLevel.LOW,
    rev: ReversibilityClass = ReversibilityClass.REVERSIBLE,
    external: bool = False,
    blast: int = 0,
) -> PendingAction:
    """A maximally-safe action; individual tests perturb ONE axis to probe a boundary."""
    return PendingAction(
        action_kind=kind,
        risk_level=risk,
        reversibility=rev,
        requires_external_call=external,
        estimated_blast_radius=blast,
    )


_ALL_KINDS = list(ActionKind)
_ALL_RISKS = list(RiskLevel)
_ALL_REV = list(ReversibilityClass)
_ALL_TIERS = list(AutonomyTier)

_ALWAYS_GATED = {ActionKind.KILL_SWITCH, ActionKind.SPEND_COMMIT}

# The blast-radius ceiling for auto-approval is part of the contract: strictly greater
# than this many affected entities can never be auto-approved (must go to a human).
_BLAST_CEILING = 5


# --- The single happy path: a benign, low-risk, reversible, in-tier action -------------


@pytest.mark.parametrize("tier", [AutonomyTier.SUPERVISED, AutonomyTier.FULL])
def test_low_risk_reversible_internal_write_auto_approves_when_tier_permits(
    tier: AutonomyTier,
) -> None:
    action = _benign(kind=ActionKind.INTERNAL_WRITE, blast=_BLAST_CEILING)
    assert decide_approval(action, tier) is ApprovalDecision.AUTO_APPROVE


def test_read_only_auto_approves_a_pure_read() -> None:
    # A pure read at the lowest tier is the canonical auto-approve.
    assert decide_approval(_benign(kind=ActionKind.READ), AutonomyTier.READ_ONLY) is (
        ApprovalDecision.AUTO_APPROVE
    )


# --- Always-gated kinds escalate to a human at EVERY tier (never auto, never refuse) ----


@pytest.mark.parametrize(("tier", "kind"), list(itertools.product(_ALL_TIERS, _ALWAYS_GATED)))
def test_always_gated_kinds_require_human_at_every_tier(
    tier: AutonomyTier, kind: ActionKind
) -> None:
    # Even at FULL with LOW risk and reversible, kill-switch / spend-commit need a human.
    action = _benign(kind=kind)
    assert decide_approval(action, tier) is ApprovalDecision.REQUIRE_HUMAN


def test_always_gated_kind_is_never_auto_even_at_full() -> None:
    # Direct security assertion: a mutant opening the gate at FULL is killed here.
    for kind in _ALWAYS_GATED:
        assert (
            decide_approval(_benign(kind=kind), AutonomyTier.FULL)
            is not ApprovalDecision.AUTO_APPROVE
        )


# --- A tier-forbidden kind is never auto (escalates) -----------------------------------


def test_tier_forbidden_kind_escalates_to_human_not_auto() -> None:
    # INTERNAL_WRITE is forbidden at READ_ONLY -> must require a human, never auto-approve.
    action = _benign(kind=ActionKind.INTERNAL_WRITE)
    assert decide_approval(action, AutonomyTier.READ_ONLY) is ApprovalDecision.REQUIRE_HUMAN


def test_irreversible_at_supervised_escalates_to_human() -> None:
    # IRREVERSIBLE kind is permitted only at FULL; at SUPERVISED it must escalate.
    action = _benign(kind=ActionKind.IRREVERSIBLE, rev=ReversibilityClass.IRREVERSIBLE)
    assert decide_approval(action, AutonomyTier.SUPERVISED) is ApprovalDecision.REQUIRE_HUMAN


# --- Risk-level boundary: LOW auto-approves, MEDIUM+ escalates (boundary-exact) ---------


@pytest.mark.parametrize(
    ("risk", "expected_auto"),
    [
        (RiskLevel.LOW, True),  # just-under the escalation cutoff -> auto
        (RiskLevel.MEDIUM, False),  # on/just-over the cutoff -> escalate
        (RiskLevel.HIGH, False),
        (RiskLevel.CRITICAL, False),
    ],
)
def test_risk_level_cutoff_for_auto_approval_is_exact(
    risk: RiskLevel, expected_auto: bool
) -> None:
    action = _benign(kind=ActionKind.INTERNAL_WRITE, risk=risk)
    decision = decide_approval(action, AutonomyTier.FULL)
    assert (decision is ApprovalDecision.AUTO_APPROVE) is expected_auto


# --- Reversibility: only fully-reversible auto-approves ---------------------------------


@pytest.mark.parametrize(
    ("rev", "expected_auto"),
    [
        (ReversibilityClass.REVERSIBLE, True),
        (ReversibilityClass.PARTIALLY_REVERSIBLE, False),
        (ReversibilityClass.IRREVERSIBLE, False),
    ],
)
def test_only_fully_reversible_actions_auto_approve(
    rev: ReversibilityClass, expected_auto: bool
) -> None:
    action = _benign(kind=ActionKind.EXTERNAL_SIDE_EFFECT, rev=rev)
    decision = decide_approval(action, AutonomyTier.FULL)
    assert (decision is ApprovalDecision.AUTO_APPROVE) is expected_auto


# --- Blast-radius ceiling: boundary-exact on/just-over/just-under -----------------------


@pytest.mark.parametrize(
    ("blast", "expected_auto"),
    [
        (0, True),
        (_BLAST_CEILING - 1, True),  # just-under
        (_BLAST_CEILING, True),  # on the ceiling -> still auto (inclusive)
        (_BLAST_CEILING + 1, False),  # just-over -> escalate
        (10_000, False),
    ],
)
def test_blast_radius_ceiling_is_boundary_exact(blast: int, expected_auto: bool) -> None:
    action = _benign(kind=ActionKind.INTERNAL_WRITE, blast=blast)
    decision = decide_approval(action, AutonomyTier.FULL)
    assert (decision is ApprovalDecision.AUTO_APPROVE) is expected_auto


# --- REFUSE: the categorically-unsafe combination --------------------------------------


def test_critical_irreversible_external_action_is_refused_outright() -> None:
    # The maximal-danger combination is refused (not even queued to a human) at any tier.
    action = _benign(
        kind=ActionKind.IRREVERSIBLE,
        risk=RiskLevel.CRITICAL,
        rev=ReversibilityClass.IRREVERSIBLE,
        external=True,
        blast=1,
    )
    for tier in _ALL_TIERS:
        assert decide_approval(action, tier) is ApprovalDecision.REFUSE


def test_refuse_requires_all_three_danger_axes_not_just_critical() -> None:
    # CRITICAL alone (but reversible, internal) must NOT be refused — it escalates. This
    # kills a mutant that collapses REFUSE into "any critical action".
    action = _benign(
        kind=ActionKind.INTERNAL_WRITE,
        risk=RiskLevel.CRITICAL,
        rev=ReversibilityClass.REVERSIBLE,
        external=False,
    )
    assert decide_approval(action, AutonomyTier.FULL) is ApprovalDecision.REQUIRE_HUMAN


# --- Properties: never-auto invariants + monotonicity ----------------------------------


_pending_actions = st.builds(
    PendingAction,
    action_kind=st.sampled_from(_ALL_KINDS),
    risk_level=st.sampled_from(_ALL_RISKS),
    reversibility=st.sampled_from(_ALL_REV),
    requires_external_call=st.booleans(),
    estimated_blast_radius=st.integers(min_value=0, max_value=100_000),
)


@given(action=_pending_actions, tier=st.sampled_from(_ALL_TIERS))
def test_auto_approve_implies_every_safety_precondition_holds(
    action: PendingAction, tier: AutonomyTier
) -> None:
    # The crucial security property: IF the scorer auto-approves, THEN every precondition
    # must hold. Any mutant that auto-approves a risky action violates this and is killed.
    decision = decide_approval(action, tier)
    if decision is ApprovalDecision.AUTO_APPROVE:
        assert action.action_kind not in _ALWAYS_GATED
        assert action.risk_level == RiskLevel.LOW
        assert action.reversibility == ReversibilityClass.REVERSIBLE
        assert action.estimated_blast_radius <= _BLAST_CEILING
        # the kind must actually be permitted unattended at this tier
        assert tier_permits(tier, action.action_kind)


@given(
    kind=st.sampled_from([ActionKind.INTERNAL_WRITE, ActionKind.EXTERNAL_SIDE_EFFECT]),
    rev=st.sampled_from(_ALL_REV),
    external=st.booleans(),
    blast=st.integers(min_value=0, max_value=20),
    tier=st.sampled_from(_ALL_TIERS),
)
def test_raising_risk_never_loosens_the_decision(
    kind: ActionKind,
    rev: ReversibilityClass,
    external: bool,
    blast: int,
    tier: AutonomyTier,
) -> None:
    # Monotonicity in risk: a stricter (higher) risk level never yields a MORE permissive
    # decision. Order permissiveness AUTO_APPROVE > REQUIRE_HUMAN > REFUSE.
    rank = {
        ApprovalDecision.AUTO_APPROVE: 2,
        ApprovalDecision.REQUIRE_HUMAN: 1,
        ApprovalDecision.REFUSE: 0,
    }
    decisions = [
        rank[
            decide_approval(
                _benign(kind=kind, risk=r, rev=rev, external=external, blast=blast), tier
            )
        ]
        for r in sorted(_ALL_RISKS)
    ]
    assert decisions == sorted(decisions, reverse=True)


def test_decision_is_deterministic_across_repeats() -> None:
    action = _benign(kind=ActionKind.EXTERNAL_SIDE_EFFECT, risk=RiskLevel.MEDIUM)
    outcomes = {decide_approval(action, AutonomyTier.FULL) for _ in range(50)}
    assert len(outcomes) == 1


# --- Fail-closed on malformed inputs ---------------------------------------------------


@pytest.mark.parametrize("bad", [None, "FULL", 2, object()])
def test_unknown_tier_is_refused_fail_closed(bad: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        decide_approval(_benign(), bad)  # type: ignore[arg-type]


@pytest.mark.parametrize("bad", [None, "action", 1, object()])
def test_non_pending_action_is_refused_fail_closed(bad: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        decide_approval(bad, AutonomyTier.FULL)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"kind": "READ"},
        {"risk": 1},
        {"rev": "reversible"},
        {"external": 1},
        {"blast": -1},
        {"blast": 1.5},
    ],
)
def test_malformed_pending_action_cannot_be_constructed(kwargs: dict[str, object]) -> None:
    # The model is the first fail-closed gate: a malformed action never reaches the scorer.
    base: dict[str, object] = {
        "kind": ActionKind.READ,
        "risk": RiskLevel.LOW,
        "rev": ReversibilityClass.REVERSIBLE,
        "external": False,
        "blast": 0,
    }
    base.update(kwargs)
    with pytest.raises((TypeError, ValueError)):
        PendingAction(
            action_kind=base["kind"],  # type: ignore[arg-type]
            risk_level=base["risk"],  # type: ignore[arg-type]
            reversibility=base["rev"],  # type: ignore[arg-type]
            requires_external_call=base["external"],  # type: ignore[arg-type]
            estimated_blast_radius=base["blast"],  # type: ignore[arg-type]
        )
