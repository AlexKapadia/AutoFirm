"""``frozen=True`` + ``slots=True`` immutability proofs for every core value type.

These kill the dataclass-decorator flag mutants (CLAUDE.md §3.6):
* ``frozen=True`` -> ``frozen=False`` -- a flipped flag would let a "frozen" record be
  mutated between scoring and audit. Caught by asserting that assigning a field raises
  :class:`dataclasses.FrozenInstanceError` (which only a frozen dataclass does).
* ``slots=True`` -> ``slots=False`` -- a flipped flag would grow a ``__dict__`` and silently
  absorb typo'd/forged attributes. Caught by asserting the instance has NO ``__dict__``
  (only a slotted instance lacks one).
"""

from __future__ import annotations

import dataclasses
from decimal import Decimal

import pytest

from autofirm.cockpit.core.approval_risk_model import (
    PendingAction,
    ReversibilityClass,
    RiskLevel,
)
from autofirm.cockpit.core.autonomy_tier_model import ActionKind
from autofirm.cockpit.core.budget_threshold_state import BudgetBand
from autofirm.cockpit.core.spend_rollup_model import (
    AgentSpend,
    RunSpendRollup,
    SpendEntry,
    StepSpend,
)
from autofirm.foundation.money.money_amount import Money


def _usd(value: str) -> Money:
    return Money(Decimal(value), "USD")


def _pending() -> PendingAction:
    return PendingAction(
        action_kind=ActionKind.READ,
        risk_level=RiskLevel.LOW,
        reversibility=ReversibilityClass.REVERSIBLE,
        requires_external_call=False,
        estimated_blast_radius=0,
    )


def test_pending_action_is_frozen_and_slotted() -> None:
    obj = _pending()
    with pytest.raises(dataclasses.FrozenInstanceError):
        obj.risk_level = RiskLevel.CRITICAL  # type: ignore[misc]
    assert not hasattr(obj, "__dict__")  # slots=True -> no instance __dict__


def test_spend_entry_is_frozen_and_slotted() -> None:
    obj = SpendEntry("a", "s1", _usd("1.00"))
    with pytest.raises(dataclasses.FrozenInstanceError):
        obj.amount = _usd("9.99")  # type: ignore[misc]
    assert not hasattr(obj, "__dict__")


def test_step_spend_is_frozen_and_slotted() -> None:
    obj = StepSpend("s1", _usd("1.00"))
    with pytest.raises(dataclasses.FrozenInstanceError):
        obj.amount = _usd("9.99")  # type: ignore[misc]
    assert not hasattr(obj, "__dict__")


def test_agent_spend_is_frozen_and_slotted() -> None:
    obj = AgentSpend("a", _usd("1.00"), BudgetBand.OK, ())
    with pytest.raises(dataclasses.FrozenInstanceError):
        obj.total = _usd("9.99")  # type: ignore[misc]
    assert not hasattr(obj, "__dict__")


def test_run_spend_rollup_is_frozen_and_slotted() -> None:
    obj = RunSpendRollup(_usd("1.00"), BudgetBand.OK, ())
    with pytest.raises(dataclasses.FrozenInstanceError):
        obj.total = _usd("9.99")  # type: ignore[misc]
    assert not hasattr(obj, "__dict__")
