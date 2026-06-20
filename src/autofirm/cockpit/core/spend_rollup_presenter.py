"""The three-tier spend rollup fold: entries -> run total → per-agent → per-step (EXACT).

What this does
--------------
:func:`roll_up_run_spend` is a PURE fold from a flat sequence of :class:`SpendEntry` cost
lines into a :class:`RunSpendRollup` tree: the run grand total, each agent's subtotal, and
each step's leaf, every node an exact :class:`~autofirm.foundation.money.money_amount.Money`
with a :class:`~autofirm.cockpit.core.budget_threshold_state.BudgetBand`. Summation is
pure ``Decimal`` via ``Money`` addition, so the per-step amounts sum to the per-agent
subtotals sum to the grand total — to the cent, with no penny created or lost — which is
the rollup's acceptance invariant (cockpit-research/PLAN.md §1.1; CLAUDE.md §3.11; the
~100% mutation target).

Why it exists / where it sits
-----------------------------
The cockpit shows spend at run / agent / step granularity so the operator can see exactly
where money is going. Keeping the fold pure makes the exact-reconciliation invariant
trivially property-testable and gives mutmut a small, total function to attack. Sits in
the pure core; depends on the foundation ``Money`` type, the band classifier, and the
rollup value types — never on I/O.

Security / compliance invariants upheld
---------------------------------------
* **Zero float / exact reconciliation (§3.11):** all addition is ``Money`` (Decimal); the
  whole grand total is recomputed by folding the per-step amounts, so subtotals always
  reconcile exactly.
* **Single currency by construction (research folder 09):** the run declares ONE currency;
  an entry or budget in a different currency is refused (``Money.__add__`` also refuses
  cross-currency) — a rollup never silently mixes currencies.
* **Fail-closed (§5.6):** a non-``SpendEntry`` ledger member, a currency mismatch, or a
  malformed budget is refused before any total is produced.
* **Deterministic presentation:** agents and steps are returned in stable sorted-by-id
  order, so the same ledger always yields the same tree regardless of input order.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from autofirm.cockpit.core.budget_threshold_state import classify_budget_band
from autofirm.cockpit.core.spend_rollup_model import (
    AgentSpend,
    RunSpendRollup,
    SpendEntry,
    StepSpend,
)
from autofirm.foundation.money.money_amount import Money

__all__ = ["roll_up_run_spend"]


def roll_up_run_spend(
    entries: Sequence[SpendEntry], *, budget: Money, currency: str
) -> RunSpendRollup:
    """Fold ``entries`` into the exact three-tier run → agent → step spend tree (PURE).

    Args:
        entries: The flat per-step cost lines. May be empty (⇒ a zero rollup).
        budget: The run budget ceiling, used to classify each node's band. Must be the
            same ``currency`` and strictly positive (enforced by the band classifier).
        currency: The single ISO-4217 currency the whole run is denominated in; every
            entry and the budget must match it.

    Returns:
        The :class:`RunSpendRollup` with exact totals and a band on every node, agents and
        steps in stable sorted-by-id order.

    Raises:
        TypeError: If a ledger member is not a :class:`SpendEntry` (fail-closed).
        ValueError: If any entry or the budget is not in ``currency`` (fail-closed:
            a rollup is single-currency by construction).
    """
    # fail-closed: the budget anchors the run currency; a mismatched budget is refused so
    # the band classification cannot silently compare across currencies.
    if not isinstance(budget, Money):
        raise TypeError(f"budget must be Money, not {type(budget).__name__}")
    if budget.currency != currency:
        raise ValueError(
            f"budget currency {budget.currency} does not match run currency {currency}"
        )

    zero = Money(Decimal("0.00"), currency)  # the exact additive identity for this run

    # Group per-step amounts by (agent_id -> step_id -> running Money), summing duplicates.
    # A plain dict keyed by id gives last-write-wins; we ADD so repeated (agent, step)
    # lines accumulate (a real ledger has many cost lines per step).
    by_agent: dict[str, dict[str, Money]] = {}
    for entry in entries:
        # fail-closed: refuse any non-SpendEntry so a forged/garbage ledger member cannot
        # contribute an unvalidated amount to a total.
        if not isinstance(entry, SpendEntry):
            raise TypeError(f"every ledger member must be a SpendEntry, not {type(entry).__name__}")
        # fail-closed: an entry in another currency is refused — the run is single-currency.
        if entry.amount.currency != currency:
            raise ValueError(
                f"entry currency {entry.amount.currency} does not match run currency {currency}"
            )
        steps = by_agent.setdefault(entry.agent_id, {})
        # Money.__add__ keeps this exact and re-checks the currency (defence in depth).
        steps[entry.step_id] = steps.get(entry.step_id, zero) + entry.amount

    agents: list[AgentSpend] = []
    run_total = zero
    # Sort agents by id for deterministic presentation (no reliance on dict order).
    for agent_id in sorted(by_agent):
        step_amounts = by_agent[agent_id]
        agent_total = zero
        step_nodes: list[StepSpend] = []
        # Sort steps by id; fold their amounts into the agent subtotal exactly.
        for step_id in sorted(step_amounts):
            amount = step_amounts[step_id]
            step_nodes.append(StepSpend(step_id=step_id, amount=amount))
            agent_total = agent_total + amount  # exact Decimal addition
        agents.append(
            AgentSpend(
                agent_id=agent_id,
                total=agent_total,
                band=classify_budget_band(agent_total, budget),
                steps=tuple(step_nodes),
            )
        )
        # Recompute the grand total by folding agent subtotals — so the run total is, by
        # construction, exactly the sum of the subtotals (reconciliation cannot drift).
        run_total = run_total + agent_total

    return RunSpendRollup(
        total=run_total,
        band=classify_budget_band(run_total, budget),
        agents=tuple(agents),
    )
