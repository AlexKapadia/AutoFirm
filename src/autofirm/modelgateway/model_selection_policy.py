"""PURE deterministic selection: (selector, availability, cap, kill-switch) -> call plan.

What this does
--------------
Turns a :class:`ModelSelector` policy into an ordered **call plan** — the exact
sequence of candidate models the gateway should attempt — under four fail-closed
constraints: only AVAILABLE models may be planned, an optional per-call COST CAP
must hold, the KILL-SWITCH epoch must be untripped, and every planned model MUST be
one of the selector's own candidates. This is the deterministic core of ADR-003 §3
(`pinned` / `preferred_with_failover` / `ensemble_quorum`): given the same inputs it
returns the same plan every time, with no I/O.

The optional LEARNED-ROUTER hook may only *propose* a reordering **within** the
already-allowed candidate set; the deterministic core then DISPOSES — it intersects
the proposal back to the allowed set and can never let the learned layer add a model,
drop a required quorum member, exceed the cap, or override the kill-switch. The
learned layer is strictly optional and strictly bounded (CLAUDE.md §3.5).

Why it exists / where it sits
-----------------------------
``data-contracts.md`` §7 / ADR-003: the selector names a policy, never a model
string. This module is where the policy becomes an executable plan, kept pure so it
is property-tested exhaustively (CLAUDE.md §3.6) and carries no network.

Security / compliance invariants upheld (CLAUDE.md §5.6)
-------------------------------------------------------
* **Kill-switch fail-closed (C7):** a tripped epoch yields NO plan (raises) — every
  call path is halted before any candidate is planned.
* **Bounded spend:** a candidate whose estimated worst-case cost exceeds the cap is
  excluded; if that empties the plan, the call is refused (never an over-cap call).
* **Closed candidate set:** the plan is a subset of ``selector.candidates`` in every
  branch; the learned hook is intersected back, so it can never widen the set.
* **Quorum satisfiability:** ``ensemble_quorum`` refuses if fewer than ``quorum``
  candidates survive availability + cap — a quorum that cannot be met is never run.
"""

from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal

from autofirm.modelgateway.kill_switch_epoch import KillSwitchEpoch
from autofirm.modelgateway.model_invocation_contract import ModelSelector
from autofirm.modelgateway.model_reference import ModelRef

__all__ = [
    "CostEstimator",
    "LearnedRouterHook",
    "SelectionRefused",
    "build_call_plan",
]

# A pure, injected estimate of a candidate's worst-case cost for THIS call, as a
# Decimal (§3.11 — never float). Used only to enforce the cap; it never picks a
# model by itself. Returning a value <= cap keeps the candidate; > cap drops it.
CostEstimator = Callable[[ModelRef], Decimal]  # pragma: no mutate -- annotation-only alias

# A pure, OPTIONAL learned reordering of the allowed candidates. It receives the
# already-allowed list and returns a proposed order; the core intersects the result
# back to the allowed set (so an out-of-set or dropped model is silently ignored)
# and never trusts it to add/cap/halt. None => use the deterministic order as-is.
LearnedRouterHook = Callable[[tuple[ModelRef, ...]], tuple[ModelRef, ...]]  # pragma: no mutate  # noqa: E501


class SelectionRefused(RuntimeError):
    """Raised when no in-policy, in-budget, kill-switch-clear plan exists (fail-closed).

    The deterministic core refuses rather than degrade: an empty availability set, an
    over-cap-only candidate list, an unmeetable quorum, or a tripped kill-switch all
    produce a refusal, never a silently-weakened call.
    """


def _allowed_candidates(
    selector: ModelSelector,
    available: frozenset[ModelRef],
    cost_estimator: CostEstimator | None,
    cost_cap: Decimal | None,
) -> tuple[ModelRef, ...]:
    """Return the selector candidates that are available AND within the cost cap.

    Order is preserved from ``selector.candidates`` (deterministic). A candidate is
    kept iff it is in ``available`` and (when a cap is set) its estimated cost does
    not exceed the cap. The result is always a subset of the selector's candidates.
    """
    kept: list[ModelRef] = []
    for candidate in selector.candidates:
        # closed set + availability: only a listed, currently-available model is kept.
        if candidate not in available:
            continue
        # bounded spend: drop any candidate whose worst-case cost exceeds the cap so
        # an over-cap model can never enter the plan (fail-closed on spend).
        if (
            cost_cap is not None
            and cost_estimator is not None
            and cost_estimator(candidate) > cost_cap
        ):
            continue
        kept.append(candidate)
    return tuple(kept)


def _apply_learned_hook(
    allowed: tuple[ModelRef, ...], learned_router: LearnedRouterHook | None
) -> tuple[ModelRef, ...]:
    """Let the learned hook reorder WITHIN ``allowed``; the core disposes (intersect).

    The proposal is intersected back to ``allowed`` (preserving the proposal's order
    for members that are in the allowed set), then any allowed model the proposal
    omitted is appended in deterministic order. So the hook can re-rank but can never
    add a model, drop one, or change the allowed SET — only its order.
    """
    if learned_router is None:
        return allowed
    proposed = learned_router(allowed)
    allowed_set = set(allowed)
    seen: set[ModelRef] = set()
    reordered: list[ModelRef] = []
    # Take the hook's order, but ONLY for models that are genuinely allowed — an
    # out-of-set or duplicated proposal entry is ignored (the core disposes).
    for candidate in proposed:
        if candidate in allowed_set and candidate not in seen:
            reordered.append(candidate)
            seen.add(candidate)
    # Re-append any allowed model the hook omitted, in deterministic original order,
    # so the hook can never DROP a candidate from the plan — only reorder it.
    for candidate in allowed:
        if candidate not in seen:
            reordered.append(candidate)
            seen.add(candidate)
    return tuple(reordered)


def build_call_plan(  # noqa: PLR0913 -- the selection inputs are intrinsically wide:
    # policy, availability, kill-switch, and the optional (cap, estimator, learned hook)
    # are all independent inputs to one pure decision; collapsing them would hide them.
    selector: ModelSelector,
    available: frozenset[ModelRef],
    kill_switch: KillSwitchEpoch,
    cost_cap: Decimal | None = None,
    cost_estimator: CostEstimator | None = None,
    learned_router: LearnedRouterHook | None = None,
) -> tuple[ModelRef, ...]:
    """Return the deterministic, in-policy ordered call plan, or raise SelectionRefused.

    Args:
        selector: the validated selection policy (its candidates are the ONLY allowed set).
        available: the set of models the gateway can currently reach.
        kill_switch: the egress epoch; a tripped epoch refuses the whole plan (C7).
        cost_cap: optional per-call worst-case cost ceiling (Decimal; None => no cap).
        cost_estimator: required when ``cost_cap`` is set; estimates a candidate's cost.
        learned_router: optional hook that may reorder WITHIN the allowed set only.

    Returns:
        For ``pinned`` / ``preferred_with_failover``: the allowed candidates in plan
        order (the gateway tries them in turn). For ``ensemble_quorum``: the allowed
        candidates to call in parallel (at least ``quorum`` of them).

    Raises:
        SelectionRefused: tripped kill-switch, no available candidate, all over cap,
            or an unmeetable quorum — every fail-closed refusal of a non-runnable call.
    """
    # fail-closed FIRST (C7): a tripped kill-switch halts egress before any planning,
    # so no availability/cap branch can ever produce a plan while egress is halted.
    kill_switch.require_egress_permitted()

    allowed = _allowed_candidates(selector, available, cost_estimator, cost_cap)
    if not allowed:
        # fail-closed: nothing available + in-budget to call — refuse, never default.
        raise SelectionRefused(
            "no candidate is both available and within the cost cap"
        )

    ordered = _apply_learned_hook(allowed, learned_router)

    if selector.strategy == "ensemble_quorum":
        # quorum satisfiability: a quorum larger than the surviving candidate count
        # can never be met — refuse rather than run a quorum that cannot reach a verdict.
        # defense-in-depth (fail-closed): ModelSelector validation already guarantees a
        # quorum for this strategy, but refuse rather than trust the invariant blindly —
        # a missing quorum here would be an unreachable-verdict request.
        quorum = selector.quorum
        if quorum is None:
            raise SelectionRefused("ensemble_quorum selector is missing its quorum")
        if len(ordered) < quorum:
            raise SelectionRefused(
                f"only {len(ordered)} candidate(s) available; quorum {quorum} unmeetable"
            )
        return ordered

    # pinned / preferred_with_failover: the gateway attempts the plan in order. For
    # pinned the selector already guarantees exactly one candidate, so the plan is
    # that one model iff it survived availability + cap (else SelectionRefused above).
    return ordered
