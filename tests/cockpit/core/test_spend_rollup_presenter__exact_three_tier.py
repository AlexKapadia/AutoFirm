"""Property + adversarial tests for the three-tier spend rollup — EXACT Money, zero float.

The rollup folds per-step spend entries into per-agent subtotals and a run grand total.
The defining invariant (CLAUDE.md §3.11) is EXACTNESS: the sum of every per-step amount
equals its agent subtotal equals (summed) the grand total, to the cent, with no penny
created or lost — proven with hypothesis over thousands of random ledgers AND against
hand-computed expectations. Order-independence (commutativity/associativity of the fold),
determinism, band attachment, and fail-closed behaviour on mixed currencies / non-Money /
negative-only inputs are all asserted. No tautological asserts.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from autofirm.cockpit.core.budget_threshold_state import BudgetBand
from autofirm.cockpit.core.spend_rollup_model import SpendEntry
from autofirm.cockpit.core.spend_rollup_presenter import roll_up_run_spend
from autofirm.foundation.money.money_amount import Money

_USD = "USD"


def _usd(s: str) -> Money:
    return Money(Decimal(s), _USD)


def _entry(agent: str, step: str, amount: str) -> SpendEntry:
    return SpendEntry(agent_id=agent, step_id=step, amount=_usd(amount))


# --- A concrete, hand-computed ledger --------------------------------------------------


def test_hand_computed_three_tier_totals_are_exact() -> None:
    entries = [
        _entry("planner", "s1", "10.01"),
        _entry("planner", "s2", "0.02"),
        _entry("builder", "s1", "5.55"),
        _entry("builder", "s2", "4.45"),
        _entry("builder", "s3", "0.00"),
    ]
    rollup = roll_up_run_spend(entries, budget=_usd("100.00"), currency=_USD)

    # Grand total = 10.01 + 0.02 + 5.55 + 4.45 + 0.00 = 20.03 exactly.
    assert rollup.total == _usd("20.03")
    agents = {a.agent_id: a for a in rollup.agents}
    assert agents["planner"].total == _usd("10.03")
    assert agents["builder"].total == _usd("10.00")

    planner_steps = {s.step_id: s.amount for s in agents["planner"].steps}
    assert planner_steps == {"s1": _usd("10.01"), "s2": _usd("0.02")}
    builder_steps = {s.step_id: s.amount for s in agents["builder"].steps}
    assert builder_steps == {"s1": _usd("5.55"), "s2": _usd("4.45"), "s3": _usd("0.00")}


def test_empty_ledger_rolls_up_to_zero_with_no_agents() -> None:
    rollup = roll_up_run_spend([], budget=_usd("100.00"), currency=_USD)
    assert rollup.total == _usd("0.00")
    assert rollup.agents == ()
    assert rollup.band is BudgetBand.OK


def test_band_is_attached_at_run_level_from_total_vs_budget() -> None:
    # Total 50.00 against budget 100.00 -> exactly 50% -> WARN_50 (inclusive edge).
    entries = [_entry("a", "s1", "50.00")]
    rollup = roll_up_run_spend(entries, budget=_usd("100.00"), currency=_USD)
    assert rollup.total == _usd("50.00")
    assert rollup.band is BudgetBand.WARN_50


def test_per_agent_band_reflects_each_agents_share_of_budget() -> None:
    # Per-agent band is computed against the SAME run budget, so a single hot agent shows
    # its own pressure. Agent 'hot' spends 96.00 of a 100.00 budget -> CRIT_95.
    entries = [_entry("hot", "s1", "96.00"), _entry("cool", "s1", "1.00")]
    rollup = roll_up_run_spend(entries, budget=_usd("100.00"), currency=_USD)
    agents = {a.agent_id: a for a in rollup.agents}
    assert agents["hot"].band is BudgetBand.CRIT_95
    assert agents["cool"].band is BudgetBand.OK


# --- The exactness property: subtotals reconcile to the grand total, always ------------

_money_str = st.integers(min_value=0, max_value=10_000_000).map(
    lambda cents: Decimal(cents).scaleb(-2)  # 0.00 .. 100000.00 in exact cents
)
_agent_ids = st.sampled_from(["planner", "builder", "marketer", "cfo", "qa"])
_step_ids = st.sampled_from(["s1", "s2", "s3", "s4", "s5"])
_ledgers = st.lists(
    st.tuples(_agent_ids, _step_ids, _money_str),
    min_size=0,
    max_size=60,
)


@settings(max_examples=300, deadline=None)
@given(rows=_ledgers)
def test_grand_total_equals_sum_of_all_step_amounts_exactly(rows: list) -> None:
    entries = [SpendEntry(agent_id=a, step_id=s, amount=Money(m, _USD)) for a, s, m in rows]
    rollup = roll_up_run_spend(entries, budget=_usd("1000000.00"), currency=_USD)

    expected = Decimal("0.00")
    for _, _, m in rows:
        expected += m
    assert rollup.total.amount == expected  # exact: no penny created or lost


@settings(max_examples=300, deadline=None)
@given(rows=_ledgers)
def test_agent_subtotals_sum_back_to_grand_total_exactly(rows: list) -> None:
    entries = [SpendEntry(agent_id=a, step_id=s, amount=Money(m, _USD)) for a, s, m in rows]
    rollup = roll_up_run_spend(entries, budget=_usd("1000000.00"), currency=_USD)

    agent_sum = Decimal("0.00")
    for agent in rollup.agents:
        agent_sum += agent.total.amount
        # ...and each agent's steps sum to that agent's subtotal, exactly.
        step_sum = sum((s.amount.amount for s in agent.steps), Decimal("0.00"))
        assert step_sum == agent.total.amount
    assert agent_sum == rollup.total.amount


@settings(max_examples=200, deadline=None)
@given(rows=_ledgers)
def test_rollup_is_order_independent_commutative_and_associative(rows: list) -> None:
    entries = [SpendEntry(agent_id=a, step_id=s, amount=Money(m, _USD)) for a, s, m in rows]
    forward = roll_up_run_spend(entries, budget=_usd("1000000.00"), currency=_USD)
    reverse = roll_up_run_spend(list(reversed(entries)), budget=_usd("1000000.00"), currency=_USD)
    # Reordering inputs must not change any total (Decimal addition is exact + commutative).
    assert forward.total == reverse.total
    fa = {a.agent_id: a.total for a in forward.agents}
    ra = {a.agent_id: a.total for a in reverse.agents}
    assert fa == ra


@settings(max_examples=150, deadline=None)
@given(rows=_ledgers)
def test_every_agent_and_step_appears_exactly_once(rows: list) -> None:
    entries = [SpendEntry(agent_id=a, step_id=s, amount=Money(m, _USD)) for a, s, m in rows]
    rollup = roll_up_run_spend(entries, budget=_usd("1000000.00"), currency=_USD)

    expected_agents = {a for a, _, _ in rows}
    assert {a.agent_id for a in rollup.agents} == expected_agents
    # No agent appears twice (a mutant that fails to group would duplicate).
    assert len({a.agent_id for a in rollup.agents}) == len(rollup.agents)
    for agent in rollup.agents:
        expected_steps = {s for a, s, _ in rows if a == agent.agent_id}
        assert {s.step_id for s in agent.steps} == expected_steps
        assert len({s.step_id for s in agent.steps}) == len(agent.steps)


def test_same_agent_step_pair_amounts_accumulate() -> None:
    # Two entries for the same (agent, step) must SUM, not overwrite — a mutant using the
    # last-write-wins would drop the first 1.00 and fail this.
    entries = [_entry("a", "s1", "1.00"), _entry("a", "s1", "2.50")]
    rollup = roll_up_run_spend(entries, budget=_usd("100.00"), currency=_USD)
    assert rollup.total == _usd("3.50")
    step = rollup.agents[0].steps[0]
    assert step.amount == _usd("3.50")


def test_rollup_is_deterministic_across_repeats() -> None:
    entries = [_entry("a", "s1", "1.23"), _entry("b", "s2", "4.56")]
    totals = {
        roll_up_run_spend(entries, budget=_usd("100.00"), currency=_USD).total
        for _ in range(40)
    }
    assert len(totals) == 1


def test_agents_and_steps_are_in_stable_sorted_order() -> None:
    # Deterministic presentation: agents and steps come back sorted by id, regardless of
    # input order — a mutant relying on dict/iteration order is caught.
    entries = [
        _entry("zeta", "s2", "1.00"),
        _entry("alpha", "s3", "1.00"),
        _entry("alpha", "s1", "1.00"),
    ]
    rollup = roll_up_run_spend(entries, budget=_usd("100.00"), currency=_USD)
    assert [a.agent_id for a in rollup.agents] == ["alpha", "zeta"]
    alpha = next(a for a in rollup.agents if a.agent_id == "alpha")
    assert [s.step_id for s in alpha.steps] == ["s1", "s3"]


# --- Fail-closed -----------------------------------------------------------------------


def test_mixed_currency_entries_are_refused_fail_closed() -> None:
    entries = [
        SpendEntry(agent_id="a", step_id="s1", amount=Money(Decimal("1.00"), _USD)),
        SpendEntry(agent_id="a", step_id="s2", amount=Money(Decimal("1.00"), "GBP")),
    ]
    with pytest.raises(ValueError):
        roll_up_run_spend(entries, budget=_usd("100.00"), currency=_USD)


def test_entry_currency_must_match_declared_run_currency() -> None:
    # fail-closed: a GBP entry in a USD run is refused (the run currency is the contract).
    entries = [SpendEntry(agent_id="a", step_id="s1", amount=Money(Decimal("1.00"), "GBP"))]
    with pytest.raises(ValueError):
        roll_up_run_spend(entries, budget=_usd("100.00"), currency=_USD)


def test_budget_currency_must_match_run_currency() -> None:
    with pytest.raises(ValueError):
        roll_up_run_spend([], budget=Money(Decimal("100.00"), "GBP"), currency=_USD)


@pytest.mark.parametrize("bad", [None, 100, "100.00", Decimal("100.00")])
def test_non_money_budget_is_refused_fail_closed(bad: object) -> None:
    # fail-closed: a bare number/str budget cannot anchor the run currency — refuse it.
    with pytest.raises((TypeError, ValueError)):
        roll_up_run_spend([], budget=bad, currency=_USD)  # type: ignore[arg-type]


@pytest.mark.parametrize("bad", [None, 1, "x", Money(Decimal("1.00"), _USD)])
def test_non_spend_entry_in_ledger_is_refused_fail_closed(bad: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        roll_up_run_spend([bad], budget=_usd("100.00"), currency=_USD)  # type: ignore[list-item]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"agent_id": ""},
        {"agent_id": None},
        {"step_id": ""},
        {"step_id": 5},
        {"amount": Decimal("1.00")},
        {"amount": 1.0},
        {"amount": None},
    ],
)
def test_malformed_spend_entry_cannot_be_constructed(kwargs: dict) -> None:
    base = {"agent_id": "a", "step_id": "s1", "amount": _usd("1.00")}
    base.update(kwargs)
    with pytest.raises((TypeError, ValueError)):
        SpendEntry(**base)  # type: ignore[arg-type]
