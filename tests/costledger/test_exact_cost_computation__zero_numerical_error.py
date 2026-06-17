"""Zero-numerical-error property + boundary tests for the exact cost function (M1/M4/M7).

The §3.11 headline: the computed Decimal cost equals the mathematically correct value
EXACTLY, to the currency minor unit, on every input. These tests carry an INDEPENDENT
reference oracle (a different, by-hand summation) so they are not tautological (§3.6),
hunt the tier/unit/currency boundaries on/just-over/just-under, and are designed to
KILL mutants: a dropped bucket, a wrong rounding mode, an off-by-1000 unit divisor, a
reasoning-token added on top, or a `>` flipped to `>=` at the tier boundary all FAIL.
"""

from decimal import ROUND_DOWN, ROUND_HALF_EVEN, Decimal, localcontext

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from autofirm.costledger.exact_cost_computation import compute_exact_cost
from autofirm.foundation.money.money_amount import Money, minor_unit_exponent
from tests.costledger.synthetic_cost_fixtures import (
    make_prices,
    make_usage,
    price_vector_strategy,
    usage_strategy,
)


def _reference_cost(usage, prices, *, unit_divisor: int) -> Money:
    """An INDEPENDENT, by-hand oracle: full-precision sum, then ONE banker's quantize.

    Deliberately written differently from the production code (explicit wide context,
    list-sum) so agreement is evidence, not a copy. Honours tiering the same way the
    spec requires (prompt strictly above threshold -> uplift rate).
    """
    if prices.tier_threshold_tokens is not None and (
        usage.input_tokens + usage.cache_read_tokens
    ) > prices.tier_threshold_tokens:
        in_rate = prices.input_price_above_threshold
        out_rate = prices.output_price_above_threshold
    else:
        in_rate = prices.input_price
        out_rate = prices.output_price
    with localcontext() as ctx:
        ctx.prec = 80
        products = [
            Decimal(usage.input_tokens) * in_rate,
            Decimal(usage.output_tokens) * out_rate,
            Decimal(usage.cache_read_tokens) * prices.cache_read_price,
            Decimal(usage.cache_write_tokens) * prices.cache_write_price,
            Decimal(usage.reasoning_tokens) * prices.reasoning_price,
        ]
        total = sum(products, Decimal(0)) / Decimal(unit_divisor)
    exponent = minor_unit_exponent(prices.currency)
    quantum = Decimal(1).scaleb(-exponent)
    return Money(total.quantize(quantum, rounding=ROUND_HALF_EVEN), prices.currency)


# ----------------------- known-answer (hand-computed) ----------------------- #


def test_base_input_output_known_answer_to_the_cent() -> None:
    # 1000 in @ 3e-6 = 0.003 ; 500 out @ 15e-6 = 0.0075 ; sum 0.0105 -> USD 2dp 0.01
    cost = compute_exact_cost(make_usage(input_tokens=1000, output_tokens=500), make_prices())
    assert cost == Money(Decimal("0.01"), "USD")


def test_every_bucket_priced_independently_known_answer() -> None:
    # Distinct prices per bucket so a DROPPED or SWAPPED bucket changes the answer.
    usage = make_usage(
        input_tokens=100,
        output_tokens=200,
        cache_read_tokens=300,
        cache_write_tokens=400,
        reasoning_tokens=500,
    )
    prices = make_prices(
        input_price="0.001",
        output_price="0.002",
        cache_read_price="0.003",
        cache_write_price="0.004",
        reasoning_price="0.005",
    )
    # 100*.001 + 200*.002 + 300*.003 + 400*.004 + 500*.005
    # = .1 + .4 + .9 + 1.6 + 2.5 = 5.5
    assert compute_exact_cost(usage, prices) == Money(Decimal("5.50"), "USD")


def test_reasoning_tokens_priced_but_not_added_on_top_of_output() -> None:
    # reasoning is its OWN bucket at its own rate; it must NOT also be added to output.
    # If a mutant adds reasoning into output, this fails.
    usage = make_usage(input_tokens=0, output_tokens=10, reasoning_tokens=10)
    prices = make_prices(output_price="0.01", reasoning_price="0.02", input_price="0")
    # 10*0.01 + 10*0.02 = 0.10 + 0.20 = 0.30  (NOT 20*0.01 and NOT 20*0.02)
    assert compute_exact_cost(usage, prices) == Money(Decimal("0.30"), "USD")


# ----------------------------- banker's rounding ---------------------------- #


def test_rounding_is_banker_half_even_not_half_up() -> None:
    # Construct a total of exactly 0.005 and 0.015 so HALF_EVEN vs HALF_UP DIVERGE:
    # 0.005 -> 0.00 (even) under HALF_EVEN, 0.01 under HALF_UP.
    # 1 input token @ 0.005 = 0.005 -> 0.00 ; @ 0.015 = 0.015 -> 0.02 (even).
    half_to_even_down = compute_exact_cost(
        make_usage(input_tokens=1, output_tokens=0),
        make_prices(input_price="0.005", output_price="0", cache_read_price="0",
                    cache_write_price="0", reasoning_price="0"),
    )
    assert half_to_even_down == Money(Decimal("0.00"), "USD")
    half_to_even_up = compute_exact_cost(
        make_usage(input_tokens=1, output_tokens=0),
        make_prices(input_price="0.015", output_price="0", cache_read_price="0",
                    cache_write_price="0", reasoning_price="0"),
    )
    assert half_to_even_up == Money(Decimal("0.02"), "USD")


def test_rounding_deferred_to_boundary_not_per_token() -> None:
    # Three tokens each costing 0.004 -> per-token-rounded would be 0.00*3 = 0.00;
    # deferred-sum = 0.012 -> 0.01. The correct (deferred) answer is 0.01.
    cost = compute_exact_cost(
        make_usage(input_tokens=3, output_tokens=0),
        make_prices(input_price="0.004", output_price="0", cache_read_price="0",
                    cache_write_price="0", reasoning_price="0"),
    )
    assert cost == Money(Decimal("0.01"), "USD")


# ----------------------- unit divisor (per-1K/per-1M trap) ------------------ #


@pytest.mark.parametrize(
    ("divisor", "rate", "expected"),
    [
        (1, "0.000003", "0.01"),  # per-token: 1000*3e-6 = 0.003 -> ... need output too
    ],
)
def test_unit_divisor_scales_exactly(divisor: int, rate: str, expected: str) -> None:
    # per-1M row: rate 3.0 per 1e6 tokens, 1000 tokens -> 1000*3/1e6 = 0.003.
    cost = compute_exact_cost(
        make_usage(input_tokens=1000, output_tokens=0),
        make_prices(input_price="3.0", output_price="0", cache_read_price="0",
                    cache_write_price="0", reasoning_price="0"),
        unit_divisor=1_000_000,
    )
    assert cost == Money(Decimal("0.00"), "USD")  # 0.003 -> 0.00 at 2dp


def test_per_1k_vs_per_1m_no_1000x_error() -> None:
    # Same logical price (3 per-1M == 0.003 per-1K) must give the SAME cost when the
    # divisor matches the rate's scale — a 1000x divisor bug would diverge wildly.
    per_million = compute_exact_cost(
        make_usage(input_tokens=1_000_000, output_tokens=0),
        make_prices(input_price="3.0", output_price="0", cache_read_price="0",
                    cache_write_price="0", reasoning_price="0"),
        unit_divisor=1_000_000,
    )
    per_thousand = compute_exact_cost(
        make_usage(input_tokens=1_000_000, output_tokens=0),
        make_prices(input_price="0.003", output_price="0", cache_read_price="0",
                    cache_write_price="0", reasoning_price="0"),
        unit_divisor=1_000,
    )
    assert per_million == per_thousand == Money(Decimal("3.00"), "USD")


def test_unit_divisor_zero_or_negative_fails_closed() -> None:
    # Assert the EXACT, full message (start-to-end anchored) so a string mutant that
    # prepends/appends to the error text is killed, not merely substring-matched.
    expected = "unit_divisor must be > 0 (tokens per quoted rate)"
    with pytest.raises(ValueError) as exc0:
        compute_exact_cost(make_usage(), make_prices(), unit_divisor=0)
    assert str(exc0.value) == expected
    with pytest.raises(ValueError) as excneg:
        compute_exact_cost(make_usage(), make_prices(), unit_divisor=-1)
    assert str(excneg.value) == expected


# ----------------------- tiered pricing (Gemini 200k) ----------------------- #

_TIER = 200_000


def _tiered_prices() -> object:
    return make_prices(
        input_price="0.00000125",
        output_price="0.00001",
        input_price_above_threshold="0.0000025",
        output_price_above_threshold="0.000015",
        tier_threshold_tokens=_TIER,
        cache_read_price="0",
        cache_write_price="0",
        reasoning_price="0",
    )


@pytest.mark.parametrize(
    ("prompt", "uses_uplift"),
    [
        (_TIER - 1, False),  # just-under: base rate
        (_TIER, False),  # exactly AT: base rate (strict >)
        (_TIER + 1, True),  # just-over: uplift rate
    ],
)
def test_tier_boundary_is_strict_above(prompt: int, uses_uplift: bool) -> None:
    prices = _tiered_prices()
    usage = make_usage(input_tokens=prompt, output_tokens=0)
    cost = compute_exact_cost(usage, prices)
    base = Money(
        (Decimal(prompt) * Decimal("0.00000125")).quantize(Decimal("0.01"), ROUND_HALF_EVEN),
        "USD",
    )
    uplift = Money(
        (Decimal(prompt) * Decimal("0.0000025")).quantize(Decimal("0.01"), ROUND_HALF_EVEN),
        "USD",
    )
    assert cost == (uplift if uses_uplift else base)


def test_tier_keyed_on_prompt_includes_cache_read() -> None:
    # The prompt size that triggers tiering = input + cache_read (folder 03). With
    # input just under and cache_read pushing it over, the uplift must apply.
    prices = _tiered_prices()
    usage = make_usage(input_tokens=_TIER - 10, output_tokens=0, cache_read_tokens=20)
    cost = compute_exact_cost(usage, prices)
    # prompt = 199_990 + 20 = 200_010 > 200_000 -> uplift on the INPUT bucket.
    expected_input = Decimal(_TIER - 10) * Decimal("0.0000025")
    expected = (expected_input).quantize(Decimal("0.01"), ROUND_HALF_EVEN)
    assert cost == Money(expected, "USD")


# ----------------------------- currency minor unit -------------------------- #


def test_jpy_quantizes_to_zero_decimals() -> None:
    # JPY has 0 minor digits — a 2dp default would invent precision.
    cost = compute_exact_cost(
        make_usage(input_tokens=10, output_tokens=0),
        make_prices(currency="JPY", input_price="0.4", output_price="0",
                    cache_read_price="0", cache_write_price="0", reasoning_price="0"),
    )
    # 10*0.4 = 4.0 -> JPY 0dp -> 4
    assert cost == Money(Decimal("4"), "JPY")
    assert cost.amount == Decimal("4")


def test_bhd_quantizes_to_three_decimals() -> None:
    # BHD has 3 minor digits — a 2dp default would LOSE a unit.
    cost = compute_exact_cost(
        make_usage(input_tokens=1, output_tokens=0),
        make_prices(currency="BHD", input_price="0.0005", output_price="0",
                    cache_read_price="0", cache_write_price="0", reasoning_price="0"),
    )
    # 1*0.0005 = 0.0005 -> 3dp HALF_EVEN -> 0.000 (even)
    assert cost == Money(Decimal("0.000"), "BHD")
    # And 0.0015 -> 0.002 (even)
    cost2 = compute_exact_cost(
        make_usage(input_tokens=3, output_tokens=0),
        make_prices(currency="BHD", input_price="0.0005", output_price="0",
                    cache_read_price="0", cache_write_price="0", reasoning_price="0"),
    )
    assert cost2 == Money(Decimal("0.002"), "BHD")  # 0.0015 -> 0.002


def test_unknown_currency_fails_closed() -> None:
    with pytest.raises(ValueError, match="unknown ISO-4217 currency"):
        compute_exact_cost(
            make_usage(),
            make_prices(currency="ZZZ"),
        )


# --------------------------- property: exact vs oracle ---------------------- #


@settings(max_examples=400)
@given(usage=usage_strategy(), prices=price_vector_strategy())
def test_matches_independent_reference_oracle_exactly(usage, prices) -> None:
    # The general anti-overfit guarantee: for ANY valid usage+prices, the production
    # cost equals the independent by-hand oracle EXACTLY (Decimal equality).
    assert compute_exact_cost(usage, prices, unit_divisor=1) == _reference_cost(
        usage, prices, unit_divisor=1
    )


@settings(max_examples=200)
@given(
    usage=usage_strategy(),
    prices=price_vector_strategy(),
    divisor=st.sampled_from([1, 1_000, 1_000_000]),
)
def test_matches_oracle_across_unit_divisors(usage, prices, divisor) -> None:
    assert compute_exact_cost(usage, prices, unit_divisor=divisor) == _reference_cost(
        usage, prices, unit_divisor=divisor
    )


@settings(max_examples=200)
@given(usage=usage_strategy(), prices=price_vector_strategy())
def test_determinism_identical_inputs_identical_output(usage, prices) -> None:
    # M4: identical (usage, snapshot) -> byte-identical Decimal cost, every run.
    first = compute_exact_cost(usage, prices)
    for _ in range(5):
        again = compute_exact_cost(usage, prices)
        assert again == first
        assert again.amount == first.amount  # exact Decimal identity, not just ==


@settings(max_examples=200)
@given(usage=usage_strategy(), prices=price_vector_strategy())
def test_never_uses_round_down_a_different_mode_diverges(usage, prices) -> None:
    # Prove the mode MATTERS: where ROUND_DOWN would differ from HALF_EVEN, the
    # production answer follows HALF_EVEN (kills a rounding-mode mutant).
    exponent = minor_unit_exponent(prices.currency)
    quantum = Decimal(1).scaleb(-exponent)
    with localcontext() as ctx:
        ctx.prec = 80
        raw = (
            Decimal(usage.input_tokens) * prices.input_price
            + Decimal(usage.output_tokens) * prices.output_price
            + Decimal(usage.cache_read_tokens) * prices.cache_read_price
            + Decimal(usage.cache_write_tokens) * prices.cache_write_price
            + Decimal(usage.reasoning_tokens) * prices.reasoning_price
        )
    half_even = raw.quantize(quantum, rounding=ROUND_HALF_EVEN)
    round_down = raw.quantize(quantum, rounding=ROUND_DOWN)
    produced = compute_exact_cost(usage, prices).amount
    assert produced == half_even
    if half_even != round_down:
        assert produced != round_down
