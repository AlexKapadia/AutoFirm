"""The fail-closed, risk-scored approval decision — the cockpit's unattended-action gate.

What this does
--------------
:func:`decide_approval` is a PURE function ``(PendingAction, AutonomyTier) ->
ApprovalDecision`` that decides whether an agent may take an action UNATTENDED
(``AUTO_APPROVE``), must wait for a human (``REQUIRE_HUMAN``), or is refused outright
(``REFUSE``). It is the most security-critical decision in the cockpit: a wrong
auto-approval lets an agent act beyond its sanctioned authority, so the function is
written to FAIL CLOSED — anything missing, ambiguous, dangerous, or beyond the tier's
authority escalates to a human (or refuses), and only a fully-benign, in-tier action is
auto-approved (cockpit-research/PLAN.md §1.1, §5; the ~100% mutation target).

Decision order (first matching rule wins; ordered so the SAFEST verdict dominates)
----------------------------------------------------------------------------------
1. **REFUSE** the categorically-unsafe action: a ``CRITICAL``-risk, ``IRREVERSIBLE``,
   external action is refused at every tier — too dangerous even to queue to a human
   from the cockpit; it must be raised out-of-band.
2. **REQUIRE_HUMAN** for an always-gated kind (``KILL_SWITCH`` / ``SPEND_COMMIT``) at any
   tier — never auto, never silently refused; a human always decides.
3. **REQUIRE_HUMAN** if any single danger axis trips: risk above ``LOW``, any
   non-fully-reversible effect, or a blast radius beyond the ceiling.
4. **REQUIRE_HUMAN** if the action kind is not auto-permitted at the current tier
   (delegates the tier authority to :func:`tier_permits` — single source of truth).
5. **AUTO_APPROVE** only when every check above passed: a low-risk, fully-reversible,
   small-blast action whose kind the tier already auto-permits.

Security / compliance invariants upheld
---------------------------------------
* **Fail-closed default (CLAUDE.md §5.6):** the function only reaches ``AUTO_APPROVE`` by
  passing every gate; any unrecognised/ambiguous input raises or escalates — it can never
  fall through to auto.
* **No tier can override the always-gated kinds or the danger axes** — those are checked
  before the tier-permission delegation.
* **Determinism (§3.11):** a pure function of frozen values; identical inputs → identical
  decision, always.
"""

from __future__ import annotations

from autofirm.cockpit.core.approval_risk_model import (
    ApprovalDecision,
    PendingAction,
    ReversibilityClass,
    RiskLevel,
)
from autofirm.cockpit.core.autonomy_tier_model import (
    ActionKind,
    AutonomyTier,
    tier_permits,
)

__all__ = ["AUTO_APPROVE_BLAST_CEILING", "decide_approval"]

# The inclusive ceiling on affected entities for an auto-approval: an action touching
# STRICTLY MORE than this many entities always escalates to a human, even if otherwise
# benign (a large blast radius is itself a risk signal). On/just-under auto-approve;
# just-over escalates (boundary-exact).
AUTO_APPROVE_BLAST_CEILING = 5

# The kinds that are NEVER auto-approved by the dial — a human must always decide.
_ALWAYS_GATED_KINDS = frozenset({ActionKind.KILL_SWITCH, ActionKind.SPEND_COMMIT})


def decide_approval(  # noqa: PLR0911 -- each return is a distinct fail-closed security
    # gate (refuse / always-gated / 3 danger axes / out-of-tier / auto); collapsing them
    # would hide a rule and weaken the mutation surface. Intentionally one-rule-per-return.
    action: PendingAction, tier: AutonomyTier
) -> ApprovalDecision:
    """Decide whether ``action`` may proceed unattended at autonomy ``tier`` (PURE).

    Args:
        action: The fully-validated pending action and its risk attributes.
        tier: The current autonomy tier.

    Returns:
        ``AUTO_APPROVE`` only for a fully-benign, in-tier action; ``REFUSE`` for the
        categorically-unsafe combination; otherwise ``REQUIRE_HUMAN``.

    Raises:
        TypeError: If ``action`` is not a :class:`PendingAction` or ``tier`` is not an
            :class:`AutonomyTier` (fail-closed: a malformed input is refused, never scored).
    """
    # fail-closed: refuse malformed inputs up front so nothing unvalidated reaches a verdict
    if not isinstance(action, PendingAction):
        raise TypeError(f"action must be a PendingAction, not {type(action).__name__}")
    if not isinstance(tier, AutonomyTier):
        raise TypeError(f"tier must be an AutonomyTier, not {type(tier).__name__}")

    # Rule 1 — REFUSE the categorically-unsafe action (all three danger axes maxed). This
    # is checked FIRST so the most dangerous combination can never be merely "queued".
    if (
        action.risk_level == RiskLevel.CRITICAL
        and action.reversibility == ReversibilityClass.IRREVERSIBLE
        and action.requires_external_call
    ):
        return ApprovalDecision.REFUSE  # fail-closed: too dangerous to auto OR to queue

    # Rule 2 — always-gated kinds: a human decides regardless of tier or risk.
    if action.action_kind in _ALWAYS_GATED_KINDS:
        return ApprovalDecision.REQUIRE_HUMAN  # fail-closed: never auto-fire the kill switch

    # Rule 3 — any single danger axis escalates. Each is its own gate so a mutant that
    # weakens ONE comparison still leaves the action requiring a human.
    if action.risk_level > RiskLevel.LOW:  # boundary: only LOW is auto-approvable
        return ApprovalDecision.REQUIRE_HUMAN
    if action.reversibility != ReversibilityClass.REVERSIBLE:  # only fully reversible auto
        return ApprovalDecision.REQUIRE_HUMAN
    if action.estimated_blast_radius > AUTO_APPROVE_BLAST_CEILING:  # boundary-exact ceiling
        return ApprovalDecision.REQUIRE_HUMAN

    # Rule 4 — tier authority: the kind must be auto-permitted at this tier. Delegated to
    # tier_permits so the dial is the single source of truth (it also rejects the gated
    # kinds, but those are already handled above — defence in depth).
    if not tier_permits(tier, action.action_kind):
        return ApprovalDecision.REQUIRE_HUMAN  # fail-closed: out-of-tier kind escalates

    # Rule 5 — every gate passed: benign, reversible, small-blast, in-tier ⇒ auto-approve.
    return ApprovalDecision.AUTO_APPROVE
