"""Exact-equality assertions on every fail-closed message in the value-type models.

Why this file exists (CLAUDE.md §3.6)
-------------------------------------
The sibling ``test_core_value_types__mutation_hardening.py`` asserts these diagnostics with
``pytest.raises(match=...)`` -- but ``match`` is a **regex SUBSTRING search**, so mutmut's
string-wrap mutant (``"msg"`` -> ``"XXmsgXX"``) still matches and SURVIVES. These tests pin
the FULL message text with ``==``, which a wrapped/garbled string cannot satisfy, so the
message mutant is killed. Covers :mod:`approval_risk_model` and :mod:`spend_rollup_model`.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from autofirm.cockpit.core.approval_risk_model import (
    PendingAction,
    ReversibilityClass,
    RiskLevel,
)
from autofirm.cockpit.core.autonomy_tier_model import ActionKind
from autofirm.cockpit.core.spend_rollup_model import SpendEntry
from autofirm.foundation.money.money_amount import Money

_USD = "USD"


def _usd(value: str) -> Money:
    return Money(Decimal(value), _USD)


# --- PendingAction: the six fail-closed construction messages, pinned EXACTLY -----------


def test_pending_action_action_kind_message_is_exact() -> None:
    with pytest.raises(TypeError) as ei:
        PendingAction("read", RiskLevel.LOW, ReversibilityClass.REVERSIBLE, False, 0)  # type: ignore[arg-type]
    assert str(ei.value) == "action_kind must be an ActionKind"


def test_pending_action_risk_level_message_is_exact() -> None:
    with pytest.raises(TypeError) as ei:
        PendingAction(ActionKind.READ, 0, ReversibilityClass.REVERSIBLE, False, 0)  # type: ignore[arg-type]
    assert str(ei.value) == "risk_level must be a RiskLevel"


def test_pending_action_reversibility_message_is_exact() -> None:
    with pytest.raises(TypeError) as ei:
        PendingAction(ActionKind.READ, RiskLevel.LOW, "reversible", False, 0)  # type: ignore[arg-type]
    assert str(ei.value) == "reversibility must be a ReversibilityClass"


def test_pending_action_requires_external_call_message_is_exact() -> None:
    with pytest.raises(TypeError) as ei:
        PendingAction(ActionKind.READ, RiskLevel.LOW, ReversibilityClass.REVERSIBLE, 1, 0)  # type: ignore[arg-type]
    assert str(ei.value) == "requires_external_call must be a bool"


def test_pending_action_negative_blast_radius_message_is_exact() -> None:
    with pytest.raises(ValueError) as ei:
        PendingAction(ActionKind.READ, RiskLevel.LOW, ReversibilityClass.REVERSIBLE, False, -1)
    assert str(ei.value) == "estimated_blast_radius must be >= 0"


def test_pending_action_non_int_blast_radius_message_is_exact() -> None:
    with pytest.raises(TypeError) as ei:
        PendingAction(ActionKind.READ, RiskLevel.LOW, ReversibilityClass.REVERSIBLE, False, 1.5)  # type: ignore[arg-type]
    assert str(ei.value) == "estimated_blast_radius must be an int"


# --- SpendEntry: the five fail-closed construction messages, pinned EXACTLY -------------


def test_spend_entry_agent_id_type_message_is_exact() -> None:
    with pytest.raises(TypeError) as ei:
        SpendEntry(5, "s1", _usd("1.00"))  # type: ignore[arg-type]
    assert str(ei.value) == "agent_id must be a str"


def test_spend_entry_step_id_type_message_is_exact() -> None:
    with pytest.raises(TypeError) as ei:
        SpendEntry("a", 5, _usd("1.00"))  # type: ignore[arg-type]
    assert str(ei.value) == "step_id must be a str"


def test_spend_entry_blank_agent_id_message_is_exact() -> None:
    with pytest.raises(ValueError) as ei:
        SpendEntry("   ", "s1", _usd("1.00"))
    assert str(ei.value) == "agent_id must be a non-empty identifier"


def test_spend_entry_blank_step_id_message_is_exact() -> None:
    with pytest.raises(ValueError) as ei:
        SpendEntry("a", "", _usd("1.00"))
    assert str(ei.value) == "step_id must be a non-empty identifier"


def test_spend_entry_non_money_amount_message_is_exact() -> None:
    with pytest.raises(TypeError) as ei:
        SpendEntry("a", "s1", Decimal("1.00"))  # type: ignore[arg-type]
    assert str(ei.value) == "amount must be a Money (Decimal-backed), not a float/Decimal"
