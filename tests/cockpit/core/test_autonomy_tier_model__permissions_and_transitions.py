"""Adversarial behaviour tests for the autonomy dial — permissions + legal transitions.

These prove the dial has TEETH (CLAUDE.md §3.6): the tier ordering is exact, the
(tier, action-kind) permission truth-table is boundary-exact (every cell pinned, not a
spot-check), and the legal-transition matrix refuses illegal jumps. The autonomy dial
governs what agents may do unattended, so it is fail-closed: an UNKNOWN/None action kind
is never permitted, and an out-of-range or self-loop transition is refused unless
explicitly legal. A single wrong cell would let an agent act beyond its sanctioned
authority, so the suite enumerates the FULL matrix rather than sampling it.
"""

from __future__ import annotations

import itertools

import pytest
from hypothesis import given
from hypothesis import strategies as st

from autofirm.cockpit.core.autonomy_tier_model import (
    ActionKind,
    AutonomyTier,
    is_legal_transition,
    legal_next_tiers,
    tier_permits,
)

# --- Tier ordering: exact, total, and stable -------------------------------------------


def test_tiers_are_strictly_ordered_read_only_lowest_full_highest() -> None:
    # The dial is an ORDERED ladder; a mutated comparison or swapped value must be caught.
    assert AutonomyTier.READ_ONLY < AutonomyTier.SUPERVISED < AutonomyTier.FULL
    assert AutonomyTier.READ_ONLY.value == 0
    assert AutonomyTier.SUPERVISED.value == 1
    assert AutonomyTier.FULL.value == 2


def test_exactly_three_tiers_exist() -> None:
    # Pins the ladder size: an added/removed tier (mutant) changes this exactly.
    assert [t.name for t in AutonomyTier] == ["READ_ONLY", "SUPERVISED", "FULL"]


# --- Permission truth table: EVERY (tier, action_kind) cell pinned ---------------------

# The full, hand-authored authority matrix. READ_ONLY may only observe; SUPERVISED may
# additionally take low/medium side-effecting actions but NOT irreversible/destructive
# ones unattended; FULL may take everything EXCEPT the two actions that are never
# auto-permitted at any tier (kill-switch + external spend commitments are always gated).
_PERMISSION_TRUTH: dict[tuple[AutonomyTier, ActionKind], bool] = {
    # READ_ONLY: observe only.
    (AutonomyTier.READ_ONLY, ActionKind.READ): True,
    (AutonomyTier.READ_ONLY, ActionKind.INTERNAL_WRITE): False,
    (AutonomyTier.READ_ONLY, ActionKind.EXTERNAL_SIDE_EFFECT): False,
    (AutonomyTier.READ_ONLY, ActionKind.IRREVERSIBLE): False,
    (AutonomyTier.READ_ONLY, ActionKind.SPEND_COMMIT): False,
    (AutonomyTier.READ_ONLY, ActionKind.KILL_SWITCH): False,
    # SUPERVISED: read + internal writes + reversible external effects.
    (AutonomyTier.SUPERVISED, ActionKind.READ): True,
    (AutonomyTier.SUPERVISED, ActionKind.INTERNAL_WRITE): True,
    (AutonomyTier.SUPERVISED, ActionKind.EXTERNAL_SIDE_EFFECT): True,
    (AutonomyTier.SUPERVISED, ActionKind.IRREVERSIBLE): False,
    (AutonomyTier.SUPERVISED, ActionKind.SPEND_COMMIT): False,
    (AutonomyTier.SUPERVISED, ActionKind.KILL_SWITCH): False,
    # FULL: everything except the always-gated pair.
    (AutonomyTier.FULL, ActionKind.READ): True,
    (AutonomyTier.FULL, ActionKind.INTERNAL_WRITE): True,
    (AutonomyTier.FULL, ActionKind.EXTERNAL_SIDE_EFFECT): True,
    (AutonomyTier.FULL, ActionKind.IRREVERSIBLE): True,
    (AutonomyTier.FULL, ActionKind.SPEND_COMMIT): False,
    (AutonomyTier.FULL, ActionKind.KILL_SWITCH): False,
}


@pytest.mark.parametrize(("tier", "action", "expected"), [
    (t, a, e) for (t, a), e in _PERMISSION_TRUTH.items()
])
def test_permission_truth_table_is_exact(
    tier: AutonomyTier, action: ActionKind, expected: bool
) -> None:
    # Each of the 18 cells is asserted; a mutated boundary in one cell flips one row only
    # and is caught here — this is the matrix, not a sample.
    assert tier_permits(tier, action) is expected


def test_permission_table_covers_every_tier_and_action_combination() -> None:
    # Guards the truth table itself: if a tier or action kind is added without a row, the
    # cartesian product no longer matches and this fails — no silent gap.
    expected_pairs = set(itertools.product(AutonomyTier, ActionKind))
    assert set(_PERMISSION_TRUTH) == expected_pairs


def test_kill_switch_and_spend_commit_are_never_auto_permitted_at_any_tier() -> None:
    # The two always-gated actions: even FULL autonomy may not auto-fire them. A mutant
    # that opens either at the top tier is killed here (security-critical invariant).
    for tier in AutonomyTier:
        assert tier_permits(tier, ActionKind.KILL_SWITCH) is False
        assert tier_permits(tier, ActionKind.SPEND_COMMIT) is False


def test_higher_tiers_permit_a_superset_of_lower_tiers() -> None:
    # Monotonicity: raising the dial never REMOVES a permission. Kills a mutant that makes
    # a higher tier forbid something a lower tier allowed.
    for action in ActionKind:
        # The tiers that permit the action must form a contiguous top-suffix of the ladder:
        # if any lower tier permits it, every higher tier must too.
        for lower, higher in itertools.combinations(AutonomyTier, 2):
            if tier_permits(lower, action):
                assert tier_permits(higher, action), (
                    f"{higher.name} must permit {action.name} since {lower.name} does"
                )


@given(action=st.sampled_from(list(ActionKind)))
def test_read_only_permits_nothing_but_reads(action: ActionKind) -> None:
    # Property: at READ_ONLY the ONLY permitted action kind is READ; everything else False.
    assert tier_permits(AutonomyTier.READ_ONLY, action) is (action is ActionKind.READ)


# --- Fail-closed on unknown / wrong-typed inputs ---------------------------------------


@pytest.mark.parametrize("bad", [None, "FULL", 2, 99, object()])
def test_unknown_tier_is_refused_fail_closed(bad: object) -> None:
    # fail-closed: a non-AutonomyTier value must never be silently treated as a tier.
    with pytest.raises((TypeError, ValueError)):
        tier_permits(bad, ActionKind.READ)  # type: ignore[arg-type]


@pytest.mark.parametrize("bad", [None, "READ", 0, object()])
def test_unknown_action_kind_is_refused_fail_closed(bad: object) -> None:
    # fail-closed: an unrecognised action kind is never auto-permitted — it is refused.
    with pytest.raises((TypeError, ValueError)):
        tier_permits(AutonomyTier.FULL, bad)  # type: ignore[arg-type]


# --- Legal transition matrix -----------------------------------------------------------

# Operators may only step ONE rung at a time in either direction; jumping two rungs
# (READ_ONLY <-> FULL directly) is refused so a fat-finger cannot leap to full autonomy.
# A self-transition (no-op) is legal (idempotent re-assertion of the current tier).
_LEGAL_TRANSITIONS: set[tuple[AutonomyTier, AutonomyTier]] = {
    (AutonomyTier.READ_ONLY, AutonomyTier.READ_ONLY),
    (AutonomyTier.READ_ONLY, AutonomyTier.SUPERVISED),
    (AutonomyTier.SUPERVISED, AutonomyTier.READ_ONLY),
    (AutonomyTier.SUPERVISED, AutonomyTier.SUPERVISED),
    (AutonomyTier.SUPERVISED, AutonomyTier.FULL),
    (AutonomyTier.FULL, AutonomyTier.SUPERVISED),
    (AutonomyTier.FULL, AutonomyTier.FULL),
}


@pytest.mark.parametrize(("frm", "to"), list(itertools.product(AutonomyTier, AutonomyTier)))
def test_transition_legality_is_exact_for_every_pair(
    frm: AutonomyTier, to: AutonomyTier
) -> None:
    # All 9 ordered pairs pinned: legal iff adjacent-or-equal. The two-rung jumps
    # (READ_ONLY<->FULL) MUST be illegal — a mutant that allows the leap is killed.
    assert is_legal_transition(frm, to) is ((frm, to) in _LEGAL_TRANSITIONS)


def test_two_rung_jumps_are_refused_in_both_directions() -> None:
    # Explicit security assertion: no single step from observe-only to full autonomy.
    assert is_legal_transition(AutonomyTier.READ_ONLY, AutonomyTier.FULL) is False
    assert is_legal_transition(AutonomyTier.FULL, AutonomyTier.READ_ONLY) is False


def test_legal_next_tiers_matches_the_transition_matrix() -> None:
    # legal_next_tiers(t) must equal exactly the set of legal destinations from t.
    for frm in AutonomyTier:
        expected = {to for (f, to) in _LEGAL_TRANSITIONS if f is frm}
        assert set(legal_next_tiers(frm)) == expected


@pytest.mark.parametrize("bad", [None, "READ_ONLY", 0, object()])
def test_legal_next_tiers_with_unknown_tier_is_refused_fail_closed(bad: object) -> None:
    # fail-closed: legal_next_tiers must refuse a non-tier rather than iterate over a guess.
    with pytest.raises((TypeError, ValueError)):
        legal_next_tiers(bad)  # type: ignore[arg-type]


def test_self_transition_is_always_legal() -> None:
    # Re-asserting the current tier is idempotent and must never be refused.
    for tier in AutonomyTier:
        assert is_legal_transition(tier, tier) is True


@pytest.mark.parametrize("bad", [None, "FULL", 1, object()])
def test_transition_with_unknown_tier_is_refused_fail_closed(bad: object) -> None:
    # fail-closed: a malformed endpoint must raise, never be treated as "legal".
    with pytest.raises((TypeError, ValueError)):
        is_legal_transition(bad, AutonomyTier.FULL)  # type: ignore[arg-type]
    with pytest.raises((TypeError, ValueError)):
        is_legal_transition(AutonomyTier.FULL, bad)  # type: ignore[arg-type]
