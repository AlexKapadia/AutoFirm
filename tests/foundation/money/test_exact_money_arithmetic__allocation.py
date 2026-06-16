"""Adversarial + property-based tests for cent-conserving money allocation.

Proves the seed primitive has teeth (CLAUDE.md §3.6): boundary-exact unit
asserts AND a Hypothesis property test for the load-bearing invariant — the
parts of an allocation always sum to *exactly* the input, with no cent created
or lost — across a wide generated input space. These are designed to KILL
injected mutants on ``exact_money_arithmetic`` (the mutation gate, ADR-001 §2).
"""

from decimal import Decimal

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from autofirm.foundation.money.exact_money_arithmetic import (
    allocate,
    from_minor_units,
    minor_units,
)

# --------------------------------------------------------------------------- #
# Boundary-exact unit asserts (on / just-over / just-under, degenerate cases). #
# --------------------------------------------------------------------------- #


def test_allocate_even_split_no_remainder() -> None:
    # 1.00 over 4 equal weights -> exactly 0.25 each, sums to 1.00.
    parts = allocate(Decimal("1.00"), [1, 1, 1, 1])
    assert parts == [Decimal("0.25")] * 4
    assert sum(parts) == Decimal("1.00")


def test_allocate_indivisible_cent_goes_to_largest_remainder() -> None:
    # 0.10 over 3 -> 4/3/3 cents. Equal weights => largest remainders are the
    # first parts (tie broken by lowest index), so the extra cent lands first.
    parts = allocate(Decimal("0.10"), [1, 1, 1])
    assert parts == [Decimal("0.04"), Decimal("0.03"), Decimal("0.03")]
    assert sum(parts) == Decimal("0.10")


def test_allocate_weighted_split_is_exact() -> None:
    # 1.00 over weights 1:2:1 -> 25/50/25 cents exactly.
    parts = allocate(Decimal("1.00"), [1, 2, 1])
    assert parts == [Decimal("0.25"), Decimal("0.50"), Decimal("0.25")]
    assert sum(parts) == Decimal("1.00")


def test_allocate_classic_three_way_penny_problem() -> None:
    # The canonical "split $0.01 three ways" — the single cent must not vanish
    # nor be duplicated; exactly one part gets it.
    parts = allocate(Decimal("0.01"), [1, 1, 1])
    assert sorted(parts) == [Decimal("0.00"), Decimal("0.00"), Decimal("0.01")]
    assert sum(parts) == Decimal("0.01")


def test_allocate_single_weight_returns_whole_amount() -> None:
    assert allocate(Decimal("123.45"), [7]) == [Decimal("123.45")]


def test_allocate_zero_amount_yields_all_zero() -> None:
    parts = allocate(Decimal("0.00"), [3, 5, 2])
    assert parts == [Decimal("0.00")] * 3
    assert sum(parts) == Decimal("0.00")


def test_allocate_negative_amount_conserves_and_keeps_sign() -> None:
    # A refund / negative posting must conserve cents and stay negative.
    parts = allocate(Decimal("-0.10"), [1, 1, 1])
    assert sum(parts) == Decimal("-0.10")
    assert all(p <= 0 for p in parts)
    assert parts == [Decimal("-0.04"), Decimal("-0.03"), Decimal("-0.03")]


def test_allocate_unequal_weights_assigns_leftover_by_remainder() -> None:
    # 1.00 over 1:1:1 -> 34/33/33; the extra cent goes to the first (largest
    # remainder, tie -> lowest index), proving the remainder ranking is used.
    parts = allocate(Decimal("1.00"), [1, 1, 1])
    assert parts == [Decimal("0.34"), Decimal("0.33"), Decimal("0.33")]


def test_minor_units_round_trip_exact() -> None:
    assert minor_units(Decimal("10.00")) == 1000
    assert from_minor_units(1000) == Decimal("10.00")


# --------------------------------------------------------------------------- #
# Fail-closed validation (CLAUDE.md §5.6) — refuse, never coerce.             #
# --------------------------------------------------------------------------- #


def test_allocate_rejects_empty_weights() -> None:
    with pytest.raises(ValueError, match="at least one"):
        allocate(Decimal("1.00"), [])


@pytest.mark.parametrize("bad", [[0, 1], [1, -3], [-1]])
def test_allocate_rejects_non_positive_weights(bad: list[int]) -> None:
    with pytest.raises(ValueError, match="strictly positive"):
        allocate(Decimal("1.00"), bad)


def test_allocate_rejects_sub_cent_amount() -> None:
    with pytest.raises(ValueError, match="not exactly representable"):
        allocate(Decimal("1.005"), [1, 1])


def test_minor_units_rejects_negative_exponent() -> None:
    with pytest.raises(ValueError, match="exponent must be >= 0"):
        minor_units(Decimal("1.00"), exponent=-1)


def test_from_minor_units_rejects_negative_exponent() -> None:
    with pytest.raises(ValueError, match="exponent must be >= 0"):
        from_minor_units(100, exponent=-1)


# --------------------------------------------------------------------------- #
# Property-based invariants (PBT mandatory — CLAUDE.md §3.6).                  #
# The core invariant: an allocation conserves every minor unit, always.       #
# --------------------------------------------------------------------------- #

_amounts = st.decimals(
    min_value=Decimal("-100000.00"),
    max_value=Decimal("100000.00"),
    places=2,
    allow_nan=False,
    allow_infinity=False,
)
_weights = st.lists(st.integers(min_value=1, max_value=10_000), min_size=1, max_size=25)


@settings(max_examples=600)
@given(amount=_amounts, weights=_weights)
def test_property_allocation_sum_equals_input_exactly(
    amount: Decimal, weights: list[int]
) -> None:
    # THE invariant: no cent is ever created or lost, for any amount/weights.
    parts = allocate(amount, weights)
    assert sum(parts) == amount


@settings(max_examples=600)
@given(amount=_amounts, weights=_weights)
def test_property_part_count_matches_weight_count(
    amount: Decimal, weights: list[int]
) -> None:
    assert len(allocate(amount, weights)) == len(weights)


@settings(max_examples=600)
@given(amount=_amounts, weights=_weights)
def test_property_each_part_is_quantised_to_the_cent(
    amount: Decimal, weights: list[int]
) -> None:
    # Every returned part must itself be an exact whole number of cents.
    for part in allocate(amount, weights):
        assert part == part.quantize(Decimal("0.01"))


@settings(max_examples=400)
@given(
    amount=st.decimals(
        min_value=Decimal("0.00"), max_value=Decimal("100000.00"), places=2,
        allow_nan=False, allow_infinity=False,
    ),
    weights=_weights,
)
def test_property_each_part_within_one_cent_of_fair_share(
    amount: Decimal, weights: list[int]
) -> None:
    # Largest-remainder fairness: every part is within one minor unit of its
    # exact proportional share — kills mutants that misroute leftover cents.
    parts = allocate(amount, weights)
    total_w = sum(weights)
    total_units = minor_units(amount)
    for w, part in zip(weights, parts, strict=True):
        fair = Decimal(total_units * w) / Decimal(total_w)
        got = Decimal(minor_units(part))
        assert abs(got - fair) < 1


@settings(max_examples=300)
@given(amount=_amounts, weights=_weights)
def test_property_allocation_is_deterministic(
    amount: Decimal, weights: list[int]
) -> None:
    # Identical inputs must yield identical outputs across repeats (determinism).
    assert allocate(amount, weights) == allocate(amount, weights)


# --------------------------------------------------------------------------- #
# Mutation-killer tests (ADR-001 §2). Each targets a surviving mutant on       #
# exact_money_arithmetic so the mutation score is 100% killed. Behaviour-only  #
# survivors (the sign branch at total_units==0, and the wide intermediate      #
# precision floor of 50) are documented below as equivalent mutants.          #
# --------------------------------------------------------------------------- #


def test_exponent_zero_is_accepted_whole_units_only() -> None:
    # Kills the `< 0` -> `<= 0` / `< 1` boundary mutants on the exponent guard:
    # exponent 0 (whole units, no fractional minor unit) MUST be accepted, not
    # refused. A mutant that rejects 0 would raise here instead of allocating.
    assert minor_units(Decimal("5"), 0) == 5
    assert from_minor_units(5, 0) == Decimal("5")
    assert allocate(Decimal("10"), [1, 1, 1], 0) == [
        Decimal("4"),
        Decimal("3"),
        Decimal("3"),
    ]


def test_minor_units_negative_exponent_message_is_exact() -> None:
    # Kills the string mutant on the message: assert the FULL text, not a
    # substring, so an `XX...XX`-wrapped mutated message fails the assert.
    with pytest.raises(ValueError) as exc:
        minor_units(Decimal("1.00"), exponent=-1)
    assert str(exc.value) == "exponent must be >= 0, got -1"


def test_from_minor_units_negative_exponent_message_is_exact() -> None:
    with pytest.raises(ValueError) as exc:
        from_minor_units(100, exponent=-1)
    assert str(exc.value) == "exponent must be >= 0, got -1"


def test_minor_units_sub_cent_message_is_exact() -> None:
    with pytest.raises(ValueError) as exc:
        minor_units(Decimal("1.005"))
    assert (
        str(exc.value)
        == "amount Decimal('1.005') is not exactly representable at 2 decimal places"
    )


def test_allocate_empty_weights_message_is_exact() -> None:
    with pytest.raises(ValueError) as exc:
        allocate(Decimal("1.00"), [])
    assert str(exc.value) == "weights must contain at least one entry"


def test_allocate_non_positive_weights_message_is_exact() -> None:
    with pytest.raises(ValueError) as exc:
        allocate(Decimal("1.00"), [0, 1])
    assert str(exc.value) == "all weights must be strictly positive, got [0, 1]"


def test_allocate_leftover_uses_minus_remainder_not_plus() -> None:
    # Kills the `exact_share - floor` -> `exact_share + floor` mutant. With `+`
    # the remainder ranking is corrupted, so the leftover cent is misrouted.
    # The true largest-remainder result for 2.76 over 2:5:2:8 is pinned exactly.
    parts = allocate(Decimal("2.76"), [2, 5, 2, 8])
    assert parts == [Decimal("0.33"), Decimal("0.81"), Decimal("0.32"), Decimal("1.30")]
    assert sum(parts) == Decimal("2.76")


def test_allocate_uses_high_intermediate_precision_for_exact_remainders() -> None:
    # Kills the `ctx.prec = 50` -> `51` mutant: at the configured precision the
    # largest-remainder routing for 291.44 over 105:660:715 is exact and pinned;
    # bumping the precision shifts a cent between the first two parts. Both still
    # sum correctly, so only an exact-distribution assert catches the drift.
    parts = allocate(Decimal("291.44"), [105, 660, 715])
    assert parts == [Decimal("20.68"), Decimal("129.96"), Decimal("140.80")]
    assert sum(parts) == Decimal("291.44")
