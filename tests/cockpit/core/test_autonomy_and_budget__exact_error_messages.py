"""Exact-equality assertions on every fail-closed message in the dial and band classifier.

Why this file exists (CLAUDE.md §3.6)
-------------------------------------
``pytest.raises(match=...)`` is a regex SUBSTRING search, so the string-wrap mutant
(``"msg"`` -> ``"XXmsgXX"``) survives a ``match`` assertion. These tests pin each
fail-closed message with ``==`` on the resolved text. For the f-string messages
(``f"... not {type(x).__name__}"``) a known wrong type (``int``) is passed and the
resolved string (``"... not int"``) is asserted in full. Covers :mod:`autonomy_tier_model`
and :mod:`budget_threshold_state`.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from autofirm.cockpit.core.autonomy_tier_model import (
    ActionKind,
    AutonomyTier,
    is_legal_transition,
    legal_next_tiers,
    tier_permits,
)
from autofirm.cockpit.core.budget_threshold_state import classify_budget_band
from autofirm.foundation.money.money_amount import Money


def _usd(value: str) -> Money:
    return Money(Decimal(value), "USD")


# --- autonomy dial: f-string type messages resolved against a known wrong type (int) ----


def test_tier_permits_tier_message_is_exact() -> None:
    with pytest.raises(TypeError) as ei:
        tier_permits(123, ActionKind.READ)  # type: ignore[arg-type]
    assert str(ei.value) == "tier must be an AutonomyTier, not int"


def test_tier_permits_action_message_is_exact() -> None:
    with pytest.raises(TypeError) as ei:
        tier_permits(AutonomyTier.FULL, 123)  # type: ignore[arg-type]
    assert str(ei.value) == "action must be an ActionKind, not int"


def test_is_legal_transition_frm_message_is_exact() -> None:
    with pytest.raises(TypeError) as ei:
        is_legal_transition(123, AutonomyTier.FULL)  # type: ignore[arg-type]
    assert str(ei.value) == "frm must be an AutonomyTier, not int"


def test_is_legal_transition_to_message_is_exact() -> None:
    with pytest.raises(TypeError) as ei:
        is_legal_transition(AutonomyTier.FULL, 123)  # type: ignore[arg-type]
    assert str(ei.value) == "to must be an AutonomyTier, not int"


def test_legal_next_tiers_frm_message_is_exact() -> None:
    with pytest.raises(TypeError) as ei:
        legal_next_tiers(123)  # type: ignore[arg-type]
    assert str(ei.value) == "frm must be an AutonomyTier, not int"


# --- budget classifier: the five fail-closed messages, pinned EXACTLY -------------------


def test_classify_spent_type_message_is_exact() -> None:
    with pytest.raises(TypeError) as ei:
        classify_budget_band("1.00", _usd("100.00"))  # type: ignore[arg-type]
    assert str(ei.value) == "spent must be Money, not str"


def test_classify_budget_type_message_is_exact() -> None:
    with pytest.raises(TypeError) as ei:
        classify_budget_band(_usd("1.00"), "100.00")  # type: ignore[arg-type]
    assert str(ei.value) == "budget must be Money, not str"


def test_classify_cross_currency_message_is_exact() -> None:
    # f-string resolves both currencies; assert the full sentence, not a substring.
    with pytest.raises(ValueError) as ei:
        classify_budget_band(_usd("1.00"), Money(Decimal("100.00"), "GBP"))
    assert str(ei.value) == "cannot compare USD spend against GBP budget"


def test_classify_non_positive_budget_message_is_exact() -> None:
    with pytest.raises(ValueError) as ei:
        classify_budget_band(_usd("1.00"), _usd("0.00"))
    assert str(ei.value) == "budget must be strictly positive to classify a band"


def test_classify_negative_spent_message_is_exact() -> None:
    with pytest.raises(ValueError) as ei:
        classify_budget_band(_usd("-1.00"), _usd("100.00"))
    assert str(ei.value) == "spent must be non-negative to classify a band"
