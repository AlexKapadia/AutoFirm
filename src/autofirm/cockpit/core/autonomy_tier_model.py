"""The autonomy dial: ordered tiers, the (tier, action) permission table, legal moves.

What this does
--------------
Defines the operator's **autonomy dial** as an ordered ladder of named tiers
(``READ_ONLY`` < ``SUPERVISED`` < ``FULL``) and two PURE decision functions over it:
:func:`tier_permits` answers "may an agent take this *kind* of action unattended at this
tier?" and :func:`is_legal_transition` answers "may the operator move the dial from tier A
to tier B?". Both are total, side-effect-free functions over frozen enums — the mutation
target for the autonomy surface (cockpit-research/PLAN.md §1.1, §5).

Why it exists / where it sits
-----------------------------
The dial governs what the fleet may do **without a human in the loop**, so it is the
security spine of the cockpit. It is deliberately pure (no clock, no IO, no state) so the
permission matrix is a deterministic function the suite can enumerate cell-by-cell and
mutmut can prove has no weak edge. Higher layers (the approval scorer, the transport)
consult it; nothing here depends on them.

Security / compliance invariants upheld
---------------------------------------
* **Fail-closed on unknown inputs (CLAUDE.md §5.6):** a non-:class:`AutonomyTier` or
  non-:class:`ActionKind` argument is *refused* (``TypeError``), never coerced — an
  unrecognised action kind must never slip through as "permitted".
* **Always-gated actions:** ``KILL_SWITCH`` and ``SPEND_COMMIT`` are *never* auto-permitted
  at ANY tier — even ``FULL`` must route them to a human/explicit confirmation.
* **No two-rung leaps:** the dial may only move one rung at a time, so a single fat-finger
  cannot jump from observe-only to full autonomy.
* **Monotonic authority:** raising the dial never removes a permission (a higher tier's
  permitted set is a superset of every lower tier's) — proven by property test.
"""

from __future__ import annotations

from enum import Enum, IntEnum

__all__ = [
    "ActionKind",
    "AutonomyTier",
    "is_legal_transition",
    "legal_next_tiers",
    "tier_permits",
]


class AutonomyTier(IntEnum):
    """The operator autonomy ladder, ordered lowest (most restrictive) to highest.

    ``IntEnum`` so the rungs compare with ``<`` and the adjacency check in
    :func:`is_legal_transition` is exact arithmetic. The integer *values* are part of the
    contract (they encode the rung order), not incidental.
    """

    READ_ONLY = 0  # observe only; agents may take no side-effecting action unattended
    SUPERVISED = 1  # internal writes + reversible external effects permitted unattended
    FULL = 2  # everything except the always-gated actions (kill-switch, spend commit)


class ActionKind(Enum):
    """The kind of action an agent wants to take, ordered by escalating blast radius.

    The dial grants permission per *kind*, not per concrete action, so the matrix stays
    small and auditable. The two highest-blast kinds are never auto-permitted.
    """

    READ = "read"  # pure observation — no state change anywhere
    INTERNAL_WRITE = "internal_write"  # mutate only AutoFirm-internal, reversible state
    EXTERNAL_SIDE_EFFECT = "external_side_effect"  # reversible effect on an external system
    IRREVERSIBLE = "irreversible"  # a side effect that cannot be undone (e.g. send/publish)
    SPEND_COMMIT = "spend_commit"  # commit real money/budget — ALWAYS gated
    KILL_SWITCH = "kill_switch"  # arm/trip the global halt — ALWAYS gated


# The hand-authored authority matrix. Each tier maps to the EXACT set of action kinds it
# auto-permits. SPEND_COMMIT and KILL_SWITCH appear in NO set: they are always gated
# (a human/explicit confirmation must intervene), even at FULL autonomy.
_PERMITTED_BY_TIER: dict[AutonomyTier, frozenset[ActionKind]] = {
    AutonomyTier.READ_ONLY: frozenset({ActionKind.READ}),
    AutonomyTier.SUPERVISED: frozenset(
        {ActionKind.READ, ActionKind.INTERNAL_WRITE, ActionKind.EXTERNAL_SIDE_EFFECT}
    ),
    AutonomyTier.FULL: frozenset(
        {
            ActionKind.READ,
            ActionKind.INTERNAL_WRITE,
            ActionKind.EXTERNAL_SIDE_EFFECT,
            ActionKind.IRREVERSIBLE,
        }
    ),
}


def tier_permits(tier: AutonomyTier, action: ActionKind) -> bool:
    """Return whether ``action`` may be taken *unattended* at autonomy ``tier`` (PURE).

    Args:
        tier: The current autonomy tier.
        action: The kind of action the agent wants to take unattended.

    Returns:
        ``True`` iff the tier auto-permits that action kind. ``SPEND_COMMIT`` and
        ``KILL_SWITCH`` return ``False`` for every tier (always gated).

    Raises:
        TypeError: If ``tier`` is not an :class:`AutonomyTier` or ``action`` is not an
            :class:`ActionKind` (fail-closed: an unknown input is refused, never permitted).
    """
    # fail-closed: refuse a non-tier so a stray int/str can never index the matrix as a tier
    if not isinstance(tier, AutonomyTier):
        raise TypeError(f"tier must be an AutonomyTier, not {type(tier).__name__}")
    # fail-closed: refuse an unknown action kind so it is never treated as auto-permitted
    if not isinstance(action, ActionKind):
        raise TypeError(f"action must be an ActionKind, not {type(action).__name__}")
    return action in _PERMITTED_BY_TIER[tier]


def is_legal_transition(frm: AutonomyTier, to: AutonomyTier) -> bool:
    """Return whether moving the dial from ``frm`` to ``to`` is a legal operator action.

    A transition is legal iff the tiers are adjacent on the ladder OR identical (a no-op
    re-assertion of the current tier is always legal). Two-rung leaps are refused so a
    single action cannot jump from observe-only to full autonomy.

    Args:
        frm: The current tier.
        to: The requested destination tier.

    Returns:
        ``True`` iff ``|to - frm| <= 1`` — i.e. one rung in either direction, or no move.

    Raises:
        TypeError: If either endpoint is not an :class:`AutonomyTier` (fail-closed).
    """
    # fail-closed: a malformed endpoint must raise, never be silently treated as legal
    if not isinstance(frm, AutonomyTier):
        raise TypeError(f"frm must be an AutonomyTier, not {type(frm).__name__}")
    if not isinstance(to, AutonomyTier):
        raise TypeError(f"to must be an AutonomyTier, not {type(to).__name__}")
    # Adjacent-or-equal: exactly one rung of movement (or none) is permitted per step.
    return abs(to.value - frm.value) <= 1


def legal_next_tiers(frm: AutonomyTier) -> tuple[AutonomyTier, ...]:
    """Return the tiers reachable from ``frm`` in one legal move, in ascending order.

    Args:
        frm: The current tier.

    Returns:
        The ordered tuple of destinations ``to`` for which :func:`is_legal_transition`
        is ``True`` (includes ``frm`` itself — the legal no-op).

    Raises:
        TypeError: If ``frm`` is not an :class:`AutonomyTier` (fail-closed).
    """
    # fail-closed: reuse the same guarded predicate so the legal set can never disagree
    # with is_legal_transition (single source of truth for legality).
    if not isinstance(frm, AutonomyTier):
        raise TypeError(f"frm must be an AutonomyTier, not {type(frm).__name__}")
    return tuple(to for to in AutonomyTier if is_legal_transition(frm, to))
