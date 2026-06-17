"""Edge/branch hardening: exercises the remaining fail-closed branches with teeth.

Covers (and mutation-hardens) the corners the main suites leave: the ``seal`` reseal
path, the tier half-spec runtime guard, the optional-int malformed/negative branches in
the provider adapters, and the negative-tier-price validator. Each asserts the EXACT
fail-closed behaviour so a mutant on these guards is killed.
"""

from datetime import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from autofirm.costledger.append_only_cost_ledger import AppendOnlyCostLedger
from autofirm.costledger.exact_cost_computation import _effective_input_output_rates
from autofirm.costledger.provider_usage_adapters import UsageParseError, parse_openai_usage
from autofirm.costledger.usage_cost_record import PriceVector, TokenUsage
from tests.costledger.synthetic_cost_fixtures import (
    FIXED_INSTANT,
    corr,
    make_model,
    make_prices,
    make_usage,
    money,
    role,
    use_case,
)


def test_seal_reseals_content_over_current_tip() -> None:
    # The `seal` path (distinct from seal_new) re-stamps an existing content record's
    # prev_hash to the ledger tip and recomputes its hash, so it chains correctly.
    ledger = AppendOnlyCostLedger()
    first = ledger.seal_new(
        correlation_id=corr(1), requesting_role_id=role("r"), use_case=use_case("uc"),
        served_by=make_model(), usage=make_usage(), unit_prices=make_prices(),
        cost=money("0.01"), cost_source="price_map_computed",
        price_catalog_version="1.0.0", recorded_at=FIXED_INSTANT,
    )
    ledger = ledger.append(first)
    # Re-seal the SAME content over the new tip -> a valid, appendable second row.
    resealed = ledger.seal(content=first)
    assert resealed.prev_hash == ledger.tip_hash
    grown = ledger.append(resealed)
    assert grown.verify() is True
    assert len(grown.records()) == 2


def test_tier_half_spec_guard_raises_at_runtime() -> None:
    # The PriceVector validator normally blocks a half-spec, but the computation has a
    # belt-and-braces runtime guard. Force it via model_construct (bypasses validation)
    # to prove the guard fires fail-closed rather than pricing at a wrong rate.
    half = PriceVector.model_construct(
        currency="USD",
        input_price=Decimal("0.001"),
        output_price=Decimal("0.002"),
        cache_read_price=Decimal("0"),
        cache_write_price=Decimal("0"),
        reasoning_price=Decimal("0"),
        tier_threshold_tokens=100,  # threshold set...
        input_price_above_threshold=None,  # ...but rates missing (half-spec)
        output_price_above_threshold=None,
    )
    with pytest.raises(ValueError, match="missing an above-threshold rate"):
        _effective_input_output_rates(make_usage(input_tokens=200), half)


def test_optional_int_negative_value_fails_closed() -> None:
    # A PRESENT cache field with a negative value is refused (not silently 0).
    with pytest.raises(UsageParseError, match="must be >= 0"):
        parse_openai_usage(
            {
                "prompt_tokens": 100,
                "completion_tokens": 0,
                "prompt_tokens_details": {"cached_tokens": -5},
            }
        )


def test_optional_int_non_int_value_fails_closed() -> None:
    with pytest.raises(UsageParseError, match="must be an int"):
        parse_openai_usage(
            {
                "prompt_tokens": 100,
                "completion_tokens": 0,
                "prompt_tokens_details": {"cached_tokens": "oops"},
            }
        )


def test_negative_above_threshold_tier_price_refused() -> None:
    with pytest.raises(ValidationError, match="tier prices must be >= 0"):
        make_prices(
            tier_threshold_tokens=200_000,
            input_price_above_threshold="-0.001",
            output_price_above_threshold="0.002",
        )


def test_zero_token_call_costs_zero_exactly() -> None:
    # Degenerate: an all-zero usage object costs exactly 0 (no crash, exact).
    from autofirm.costledger.exact_cost_computation import compute_exact_cost

    cost = compute_exact_cost(
        TokenUsage(input_tokens=0, output_tokens=0), make_prices()
    )
    assert cost == money("0.00")


def test_naive_recorded_at_accepted_and_normalised() -> None:
    # A naive datetime is treated as UTC by the canonical encoder; the row builds.
    ledger = AppendOnlyCostLedger()
    rec = ledger.seal_new(
        correlation_id=corr(1), requesting_role_id=role("r"), use_case=use_case("uc"),
        served_by=make_model(), usage=make_usage(), unit_prices=make_prices(),
        cost=money("0.01"), cost_source="price_map_computed",
        price_catalog_version="1.0.0",
        recorded_at=datetime(2026, 1, 1, 12, 0),
    )
    assert ledger.append(rec).verify() is True
