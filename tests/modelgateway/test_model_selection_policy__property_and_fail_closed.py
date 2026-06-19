"""Property + fail-closed tests for the PURE deterministic selection policy.

The headline properties (Hypothesis, CLAUDE.md §3.6): for ANY candidate order, ANY
availability subset, and ANY cap, the plan is a subset of the selector's candidates,
contains only available + in-budget models, is deterministic, and the learned hook can
never widen the set / drop a model / beat the cap / override the kill-switch. Explicit
fail-closed cases: tripped kill-switch, empty availability, all-over-cap, unmeetable quorum.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from autofirm.modelgateway.kill_switch_epoch import KillSwitchEngaged
from autofirm.modelgateway.model_invocation_contract import ModelSelector
from autofirm.modelgateway.model_reference import ModelRef
from autofirm.modelgateway.model_selection_policy import (
    SelectionRefused,
    build_call_plan,
)
from tests.modelgateway.synthetic_gateway_fixtures import (
    CLAUDE_HAIKU,
    CLAUDE_OPUS,
    GEMINI,
    GPT,
    MODEL_POOL,
    availability_strategy,
    candidate_tuple_strategy,
    cost_cap_strategy,
    epoch,
)


def _selector_for(candidates: tuple[ModelRef, ...]) -> ModelSelector:
    """A failover selector over ``candidates`` (the most permissive shape)."""
    return ModelSelector(strategy="preferred_with_failover", candidates=candidates)


@pytest.mark.property
@given(candidates=candidate_tuple_strategy, available=availability_strategy)
def test_plan_is_always_a_subset_of_candidates_and_available(
    candidates: tuple[ModelRef, ...], available: frozenset[ModelRef]
) -> None:
    sel = _selector_for(candidates)
    expected = tuple(c for c in candidates if c in available)
    if not expected:
        with pytest.raises(SelectionRefused):
            build_call_plan(sel, available, epoch())
        return
    plan = build_call_plan(sel, available, epoch())
    # subset of candidates, all available, order preserved from the selector.
    assert set(plan) <= set(candidates)
    assert all(model in available for model in plan)
    assert plan == expected  # deterministic, candidate-ordered


@pytest.mark.property
@given(
    candidates=candidate_tuple_strategy,
    available=availability_strategy,
    cap=cost_cap_strategy,
)
def test_no_over_cap_model_is_ever_planned(
    candidates: tuple[ModelRef, ...], available: frozenset[ModelRef], cap: Decimal | None
) -> None:
    # Deterministic per-model cost: index in the pool * 1.00 (so some exceed any cap).
    costs = {model: Decimal(i) + Decimal("0.50") for i, model in enumerate(MODEL_POOL)}
    sel = _selector_for(candidates)
    try:
        plan = build_call_plan(
            sel, available, epoch(), cost_cap=cap, cost_estimator=lambda m: costs[m]
        )
    except SelectionRefused:
        return  # nothing in-budget+available — a valid fail-closed outcome
    for model in plan:
        assert model in available
        if cap is not None:
            assert costs[model] <= cap  # bounded spend: never over the cap


@pytest.mark.property
@given(candidates=candidate_tuple_strategy, available=availability_strategy)
def test_plan_is_deterministic_across_repeats(
    candidates: tuple[ModelRef, ...], available: frozenset[ModelRef]
) -> None:
    sel = _selector_for(candidates)
    try:
        first = build_call_plan(sel, available, epoch())
    except SelectionRefused:
        with pytest.raises(SelectionRefused):
            build_call_plan(sel, available, epoch())
        return
    for _ in range(5):
        assert build_call_plan(sel, available, epoch()) == first


@pytest.mark.property
@given(
    candidates=candidate_tuple_strategy,
    available=availability_strategy,
    perm_seed=st.integers(min_value=0, max_value=10_000),
)
def test_learned_hook_can_never_widen_drop_or_escape_the_allowed_set(
    candidates: tuple[ModelRef, ...],
    available: frozenset[ModelRef],
    perm_seed: int,
) -> None:
    sel = _selector_for(candidates)
    allowed = tuple(c for c in candidates if c in available)
    if not allowed:
        return  # covered by the fail-closed test below

    # A hostile hook: returns models NOT in the allowed set, duplicates, and a
    # reordering — the core must dispose of all of that and keep exactly `allowed`.
    def hostile_hook(allowed_in: tuple[ModelRef, ...]) -> tuple[ModelRef, ...]:
        injected = MODEL_POOL  # includes models possibly not allowed
        cut = perm_seed % len(allowed_in)
        rotated = allowed_in[cut:] + allowed_in[:cut]
        return injected + rotated + allowed_in  # garbage + duplicates + a rotation

    plan = build_call_plan(sel, available, epoch(), learned_router=hostile_hook)
    # The SET is exactly the allowed set — never widened, never dropped.
    assert set(plan) == set(allowed)
    assert len(plan) == len(allowed)  # no duplicates leaked through


@pytest.mark.unit
@pytest.mark.security
def test_tripped_kill_switch_refuses_before_any_planning() -> None:
    sel = _selector_for((CLAUDE_OPUS, GPT))
    with pytest.raises(KillSwitchEngaged):
        build_call_plan(sel, frozenset(MODEL_POOL), epoch(tripped=True))


@pytest.mark.unit
def test_empty_availability_refuses_fail_closed() -> None:
    sel = _selector_for((CLAUDE_OPUS, GPT))
    # anchored exact message kills a string-literal mutant on the refusal text.
    with pytest.raises(
        SelectionRefused, match=r"^no candidate is both available and within the cost cap$"
    ):
        build_call_plan(sel, frozenset(), epoch())


@pytest.mark.unit
def test_cost_cap_is_strict_greater_than_boundary_exact() -> None:
    # Boundary-exact (CLAUDE.md §3.6): a candidate whose cost EQUALS the cap is KEPT
    # (the guard is `> cap`, not `>= cap`); a candidate one unit OVER is DROPPED. This
    # kills both the comparison mutant (`>`->`>=`/`<`) and the `continue`-skip mutant.
    sel = _selector_for((CLAUDE_OPUS, GPT))
    costs = {CLAUDE_OPUS: Decimal("1.00"), GPT: Decimal("1.01")}
    plan = build_call_plan(
        sel,
        frozenset((CLAUDE_OPUS, GPT)),
        epoch(),
        cost_cap=Decimal("1.00"),
        cost_estimator=lambda m: costs[m],
    )
    # cost == cap kept; cost just-over dropped (so GPT is excluded, OPUS remains).
    assert plan == (CLAUDE_OPUS,)


@pytest.mark.unit
def test_over_cap_candidate_before_in_cap_one_is_skipped_not_break_or_pass() -> None:
    # The over-cap candidate is FIRST; the in-cap one is SECOND. With the real
    # `continue` the loop SKIPS the over-cap one and keeps the in-cap one -> plan
    # is (CLAUDE_OPUS,). A `break` mutant would stop at the over-cap candidate and
    # never reach CLAUDE_OPUS -> empty plan -> SelectionRefused (different). A `pass`
    # mutant would fall through and append the over-cap GPT -> (GPT, CLAUDE_OPUS)
    # (different). So this asserts `continue` exactly.
    sel = _selector_for((GPT, CLAUDE_OPUS))  # GPT first and over cap
    costs = {GPT: Decimal("9.99"), CLAUDE_OPUS: Decimal("0.50")}
    plan = build_call_plan(
        sel,
        frozenset((GPT, CLAUDE_OPUS)),
        epoch(),
        cost_cap=Decimal("1.00"),
        cost_estimator=lambda m: costs[m],
    )
    assert plan == (CLAUDE_OPUS,)  # GPT skipped (not break/pass), OPUS kept


@pytest.mark.unit
def test_cost_cap_keeps_all_when_all_within_cap() -> None:
    # Complements the boundary test: with a cap above every cost, the `continue` is
    # never taken and the full ordered plan is returned (kills a mutant that always
    # skips, and one that drops the `kept` accumulation).
    sel = _selector_for((CLAUDE_OPUS, GPT))
    plan = build_call_plan(
        sel,
        frozenset((CLAUDE_OPUS, GPT)),
        epoch(),
        cost_cap=Decimal("100"),
        cost_estimator=lambda _m: Decimal("0.01"),
    )
    assert plan == (CLAUDE_OPUS, GPT)


@pytest.mark.unit
def test_quorum_boundary_exact_met_vs_unmet() -> None:
    # Boundary on `len(ordered) < quorum`: exactly `quorum` survivors -> plan returned;
    # `quorum - 1` survivors -> refused. Kills the `<`->`<=`/`>` comparison mutant.
    sel = ModelSelector(
        strategy="ensemble_quorum", candidates=(CLAUDE_OPUS, GPT, GEMINI), quorum=2
    )
    # exactly 2 available == quorum -> returned
    assert set(build_call_plan(sel, frozenset((CLAUDE_OPUS, GPT)), epoch())) == {
        CLAUDE_OPUS,
        GPT,
    }
    # 1 available < quorum -> refused
    with pytest.raises(SelectionRefused, match="unmeetable"):
        build_call_plan(sel, frozenset((CLAUDE_OPUS,)), epoch())


@pytest.mark.unit
def test_all_candidates_over_cap_refuses() -> None:
    sel = _selector_for((CLAUDE_OPUS, GPT))
    with pytest.raises(SelectionRefused):
        build_call_plan(
            sel,
            frozenset((CLAUDE_OPUS, GPT)),
            epoch(),
            cost_cap=Decimal("1"),
            cost_estimator=lambda _m: Decimal("999"),
        )


@pytest.mark.unit
def test_ensemble_quorum_refuses_when_too_few_survive() -> None:
    sel = ModelSelector(
        strategy="ensemble_quorum", candidates=(CLAUDE_OPUS, GPT, GEMINI), quorum=3
    )
    # only 2 available -> quorum 3 unmeetable -> refuse (never run a weak quorum).
    # anchored exact message kills the f-string-literal mutant on the refusal text.
    with pytest.raises(
        SelectionRefused,
        match=r"^only 2 candidate\(s\) available; quorum 3 unmeetable$",
    ):
        build_call_plan(sel, frozenset((CLAUDE_OPUS, GPT)), epoch())


@pytest.mark.unit
@pytest.mark.security
def test_ensemble_quorum_with_missing_quorum_is_refused_defense_in_depth() -> None:
    # Bypass ModelSelector validation (model_construct) to forge an ensemble selector
    # whose quorum is None -> the policy's defense-in-depth guard must still refuse,
    # never run an unreachable-verdict quorum.
    forged = ModelSelector.model_construct(
        strategy="ensemble_quorum", candidates=(CLAUDE_OPUS, GPT), quorum=None
    )
    with pytest.raises(
        SelectionRefused, match=r"^ensemble_quorum selector is missing its quorum$"
    ):
        build_call_plan(forged, frozenset((CLAUDE_OPUS, GPT)), epoch())


@pytest.mark.unit
def test_ensemble_quorum_returns_all_surviving_candidates_when_met() -> None:
    sel = ModelSelector(
        strategy="ensemble_quorum", candidates=(CLAUDE_OPUS, GPT, GEMINI), quorum=2
    )
    plan = build_call_plan(sel, frozenset((CLAUDE_OPUS, GPT, GEMINI)), epoch())
    assert set(plan) == {CLAUDE_OPUS, GPT, GEMINI}


@pytest.mark.unit
def test_pinned_plan_is_the_single_model_when_available() -> None:
    sel = ModelSelector(strategy="pinned", candidates=(CLAUDE_HAIKU,))
    assert build_call_plan(sel, frozenset((CLAUDE_HAIKU,)), epoch()) == (CLAUDE_HAIKU,)


@pytest.mark.unit
def test_learned_hook_reorders_within_allowed_set() -> None:
    sel = _selector_for((CLAUDE_OPUS, GPT, GEMINI))
    available = frozenset((CLAUDE_OPUS, GPT, GEMINI))
    # hook prefers GEMINI first; core honours the WITHIN-set reorder deterministically.
    plan = build_call_plan(
        sel, available, epoch(), learned_router=lambda a: (GEMINI, *a)
    )
    assert plan[0] == GEMINI
    assert set(plan) == {CLAUDE_OPUS, GPT, GEMINI}


@pytest.mark.unit
@pytest.mark.security
def test_learned_hook_that_drops_a_candidate_cannot_remove_it_from_the_plan() -> None:
    # A learned router has no authority to SHRINK the allowed set: if it omits an
    # allowed model entirely, the core must re-append it (deterministic original
    # order) so the hook can only reorder, never drop. This exercises the
    # drop-recovery branch directly and kills any mutant that deletes it: without
    # the re-append, GPT and GEMINI would vanish from the plan below.
    sel = _selector_for((CLAUDE_OPUS, GPT, GEMINI))
    available = frozenset((CLAUDE_OPUS, GPT, GEMINI))

    # Hostile/incomplete hook: proposes ONLY GPT, dropping CLAUDE_OPUS and GEMINI.
    plan = build_call_plan(
        sel, available, epoch(), learned_router=lambda a: (GPT,)
    )

    # The dropped models survive, re-appended in deterministic selector order after
    # the hook's surviving proposal — set is intact, count is intact, order is exact.
    assert plan == (GPT, CLAUDE_OPUS, GEMINI)
    assert set(plan) == {CLAUDE_OPUS, GPT, GEMINI}
    assert len(plan) == 3


@pytest.mark.unit
def test_learned_hook_returning_empty_still_yields_the_full_allowed_set() -> None:
    # The most extreme drop: a hook that returns nothing. Every allowed model must
    # still be planned, in deterministic selector order (the re-append is the ONLY
    # source of the plan here, so a mutant on that loop is fatal).
    sel = _selector_for((CLAUDE_OPUS, GPT, GEMINI))
    available = frozenset((CLAUDE_OPUS, GPT, GEMINI))
    plan = build_call_plan(sel, available, epoch(), learned_router=lambda _a: ())
    assert plan == (CLAUDE_OPUS, GPT, GEMINI)
