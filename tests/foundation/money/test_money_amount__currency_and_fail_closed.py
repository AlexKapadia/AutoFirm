"""Adversarial tests for the currency-aware ``Money`` value type (fail-closed, exact).

Proves teeth: float money is refused, cross-currency arithmetic is refused, the minor
unit is currency-DEPENDENT (USD 2 / JPY 0 / BHD 3) and unknown currencies fail closed,
and quantisation is banker's. Designed to kill mutants on the type guard, the currency
check, the minor-unit table, and the rounding mode.
"""

from decimal import ROUND_HALF_EVEN, Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from autofirm.foundation.money.money_amount import (
    ISO4217_MINOR_UNIT_EXPONENT,
    LEDGER_ROUNDING,
    Money,
    minor_unit_exponent,
)


def test_float_amount_is_refused() -> None:
    # The single most common money bug: a float amount must be refused, not rounded.
    with pytest.raises(TypeError, match="must be a Decimal"):
        Money(0.1, "USD")  # type: ignore[arg-type]


def test_int_amount_is_refused() -> None:
    with pytest.raises(TypeError, match="must be a Decimal"):
        Money(5, "USD")  # type: ignore[arg-type]


def test_non_finite_amount_is_refused() -> None:
    with pytest.raises(ValueError, match="must be finite"):
        Money(Decimal("NaN"), "USD")
    with pytest.raises(ValueError, match="must be finite"):
        Money(Decimal("Infinity"), "USD")


def test_unknown_currency_is_refused() -> None:
    with pytest.raises(ValueError, match="unknown ISO-4217 currency"):
        Money(Decimal("1.00"), "ZZZ")


def test_cross_currency_add_is_refused() -> None:
    with pytest.raises(ValueError, match="cannot combine USD with EUR"):
        Money(Decimal("1.00"), "USD") + Money(Decimal("1.00"), "EUR")


def test_cross_currency_sub_is_refused() -> None:
    with pytest.raises(ValueError, match="cannot combine"):
        Money(Decimal("1.00"), "USD") - Money(Decimal("1.00"), "JPY")


def test_same_currency_add_is_exact() -> None:
    total = Money(Decimal("0.1"), "USD") + Money(Decimal("0.2"), "USD")
    # Decimal 0.1+0.2 == 0.3 EXACTLY (a float would give 0.30000000000000004).
    assert total == Money(Decimal("0.3"), "USD")
    assert total.amount == Decimal("0.3")


@pytest.mark.parametrize(("currency", "exponent"), [("USD", 2), ("JPY", 0), ("BHD", 3)])
def test_minor_unit_exponent_is_currency_dependent(currency: str, exponent: int) -> None:
    assert minor_unit_exponent(currency) == exponent


def test_minor_unit_unknown_currency_fails_closed() -> None:
    with pytest.raises(ValueError, match="refusing to guess a minor unit"):
        minor_unit_exponent("XYZ")


def test_quantize_usd_two_decimals_banker() -> None:
    # 0.005 -> 0.00 (even) ; 0.015 -> 0.02 (even) under HALF_EVEN.
    assert Money(Decimal("0.005"), "USD").quantize() == Money(Decimal("0.00"), "USD")
    assert Money(Decimal("0.015"), "USD").quantize() == Money(Decimal("0.02"), "USD")


def test_quantize_jpy_zero_decimals() -> None:
    assert Money(Decimal("4.4"), "JPY").quantize().amount == Decimal("4")
    assert Money(Decimal("4.5"), "JPY").quantize().amount == Decimal("4")  # even


def test_quantize_bhd_three_decimals() -> None:
    assert Money(Decimal("0.0005"), "BHD").quantize().amount == Decimal("0.000")  # even
    assert Money(Decimal("0.0015"), "BHD").quantize().amount == Decimal("0.002")  # even


def test_equality_requires_both_currency_and_amount() -> None:
    assert Money(Decimal("1.00"), "USD") == Money(Decimal("1.00"), "USD")
    assert Money(Decimal("1.00"), "USD") != Money(Decimal("1.00"), "EUR")
    assert Money(Decimal("1.00"), "USD") != Money(Decimal("1.01"), "USD")
    assert Money(Decimal("1.00"), "USD") != "not money"


def test_hash_consistent_with_equality() -> None:
    a = Money(Decimal("1.00"), "USD")
    b = Money(Decimal("1.00"), "USD")
    assert hash(a) == hash(b)
    assert len({a, b}) == 1


def test_ledger_rounding_is_half_even() -> None:
    assert LEDGER_ROUNDING == ROUND_HALF_EVEN


def test_minor_unit_table_has_zero_two_and_three_dp_currencies() -> None:
    # Guards against a regression collapsing the table to a single 2dp default.
    assert ISO4217_MINOR_UNIT_EXPONENT["JPY"] == 0
    assert ISO4217_MINOR_UNIT_EXPONENT["USD"] == 2
    assert ISO4217_MINOR_UNIT_EXPONENT["BHD"] == 3


@given(
    a=st.integers(min_value=-10_000, max_value=10_000),
    b=st.integers(min_value=-10_000, max_value=10_000),
)
def test_add_then_sub_roundtrips_exactly(a: int, b: int) -> None:
    # (x + y) - y == x exactly, for any same-currency amounts (no float drift).
    x = Money(Decimal(a).scaleb(-2), "USD")
    y = Money(Decimal(b).scaleb(-2), "USD")
    assert (x + y) - y == x
