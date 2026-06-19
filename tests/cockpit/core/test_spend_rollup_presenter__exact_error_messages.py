"""Exact-equality assertions on every fail-closed message in the spend rollup fold.

Why this file exists (CLAUDE.md §3.6)
-------------------------------------
``pytest.raises(match=...)`` is a regex SUBSTRING search, so the string-wrap mutant
(``"msg"`` -> ``"XXmsgXX"``) survives. These tests pin the resolved message text with
``==``. The two currency-mismatch diagnostics are f-strings interpolating both currencies;
they are triggered with mismatched currencies so the EXACT resolved sentence is asserted.
Covers :mod:`spend_rollup_presenter`.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from autofirm.cockpit.core.spend_rollup_model import SpendEntry
from autofirm.cockpit.core.spend_rollup_presenter import roll_up_run_spend
from autofirm.foundation.money.money_amount import Money

_USD = "USD"


def _usd(value: str) -> Money:
    return Money(Decimal(value), _USD)


def _gbp(value: str) -> Money:
    return Money(Decimal(value), "GBP")


def test_roll_up_budget_type_message_is_exact() -> None:
    with pytest.raises(TypeError) as ei:
        roll_up_run_spend([], budget="100.00", currency=_USD)  # type: ignore[arg-type]
    assert str(ei.value) == "budget must be Money, not str"


def test_roll_up_budget_currency_mismatch_message_is_exact() -> None:
    # Mismatched budget currency -> resolved f-string asserted in full.
    with pytest.raises(ValueError) as ei:
        roll_up_run_spend([], budget=_gbp("100.00"), currency=_USD)
    assert str(ei.value) == "budget currency GBP does not match run currency USD"


def test_roll_up_non_entry_member_message_is_exact() -> None:
    with pytest.raises(TypeError) as ei:
        roll_up_run_spend([1], budget=_usd("100.00"), currency=_USD)  # type: ignore[list-item]
    assert str(ei.value) == "every ledger member must be a SpendEntry, not int"


def test_roll_up_entry_currency_mismatch_message_is_exact() -> None:
    # A GBP entry in a USD run -> resolved f-string asserted in full.
    with pytest.raises(ValueError) as ei:
        roll_up_run_spend(
            [SpendEntry("a", "s1", _gbp("1.00"))],
            budget=_usd("100.00"),
            currency=_USD,
        )
    assert str(ei.value) == "entry currency GBP does not match run currency USD"
