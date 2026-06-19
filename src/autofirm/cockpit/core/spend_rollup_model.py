"""Frozen value types for the three-tier spend rollup (no logic, no I/O).

What this does
--------------
Defines the immutable inputs and outputs of the spend rollup: :class:`SpendEntry` (one
per-step cost line), and the read-side view types :class:`StepSpend`, :class:`AgentSpend`,
and :class:`RunSpendRollup` (the run total → per-agent → per-step tree, each node carrying
an exact :class:`~autofirm.foundation.money.money_amount.Money` and a
:class:`~autofirm.cockpit.core.budget_threshold_state.BudgetBand`). All decision/fold logic
lives in :mod:`spend_rollup_presenter` (cockpit-research/PLAN.md §1.1).

Why it exists / where it sits
-----------------------------
Separating the data from the fold keeps each file single-responsibility and lets the
presenter be one pure function over these frozen records — the mutation target. Sits in
the pure core; depends only on the foundation ``Money`` type and the band enum.

Security / compliance invariants upheld
---------------------------------------
* **Fail-closed construction (CLAUDE.md §5.6):** :class:`SpendEntry` refuses an empty/non-
  string id or a non-``Money`` amount, so a malformed cost line cannot exist and reach the
  fold.
* **Immutability + exact money:** every type is frozen and every amount is ``Money``
  (Decimal-backed), so a rollup is a deterministic, drift-free function of its inputs.
"""

from __future__ import annotations

from dataclasses import dataclass

from autofirm.cockpit.core.budget_threshold_state import BudgetBand
from autofirm.foundation.money.money_amount import Money

__all__ = ["AgentSpend", "RunSpendRollup", "SpendEntry", "StepSpend"]


@dataclass(frozen=True, slots=True)
class SpendEntry:
    """One per-step spend line: which agent, which step, how much (exact ``Money``).

    Attributes:
        agent_id: Non-empty identifier of the agent that incurred the cost.
        step_id: Non-empty identifier of the step within that agent's run.
        amount: The exact ``Money`` cost of the line.
    """

    agent_id: str
    step_id: str
    amount: Money

    def __post_init__(self) -> None:
        """Validate fail-closed: non-empty string ids and a real ``Money`` amount.

        Raises:
            TypeError: If an id is not a ``str`` or ``amount`` is not ``Money``.
            ValueError: If an id is empty/blank (an unlabelled cost line cannot be rolled
                up to a node — fail-closed rather than bucket it under "").
        """
        # fail-closed: ids must be real non-blank strings so every cost maps to a node
        if not isinstance(self.agent_id, str):
            raise TypeError("agent_id must be a str")
        if not isinstance(self.step_id, str):
            raise TypeError("step_id must be a str")
        if not self.agent_id.strip():
            raise ValueError("agent_id must be a non-empty identifier")
        if not self.step_id.strip():
            raise ValueError("step_id must be a non-empty identifier")
        # fail-closed: a non-Money amount (e.g. bare Decimal/float) is refused — exact
        # money is the whole point; a float here would re-import drift.
        if not isinstance(self.amount, Money):
            raise TypeError("amount must be a Money (Decimal-backed), not a float/Decimal")


@dataclass(frozen=True, slots=True)
class StepSpend:
    """A leaf node: the total exact spend attributed to one step of one agent."""

    step_id: str
    amount: Money


@dataclass(frozen=True, slots=True)
class AgentSpend:
    """A mid node: one agent's exact subtotal, its band, and its per-step breakdown.

    Attributes:
        agent_id: The agent this subtotal belongs to.
        total: The exact ``Money`` sum of every step under this agent.
        band: This agent's budget band (its subtotal vs the run budget).
        steps: The per-step leaves, in stable sorted-by-``step_id`` order.
    """

    agent_id: str
    total: Money
    band: BudgetBand
    steps: tuple[StepSpend, ...]


@dataclass(frozen=True, slots=True)
class RunSpendRollup:
    """The root: the run grand total, its band, and the per-agent breakdown.

    Attributes:
        total: The exact ``Money`` grand total across every agent and step.
        band: The run's budget band (grand total vs the run budget).
        agents: The per-agent subtotals, in stable sorted-by-``agent_id`` order.
    """

    total: Money
    band: BudgetBand
    agents: tuple[AgentSpend, ...]
