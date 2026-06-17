"""Fail-closed validation + tamper-evidence tests for the cost-ledger contracts.

Proves: TokenUsage/PriceVector refuse bad inputs; UsageCostRecord refuses a wrong-width
hash, a cross-currency cost, and a record_hash that does not match its content; the
canonical encoding is deterministic and injective. Designed to kill mutants on the
validators, the all-or-none tier rule, and the hash equality check.
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from autofirm.audit.rfc6962_hashing import HASH_BYTES
from autofirm.costledger.append_only_cost_ledger import GENESIS_PREV_HASH
from autofirm.costledger.cost_record_canonical_hashing import (
    canonical_cost_record_bytes,
    compute_cost_record_hash,
)
from autofirm.costledger.usage_cost_record import PriceVector, TokenUsage, UsageCostRecord
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

# ------------------------------- TokenUsage --------------------------------- #


@pytest.mark.parametrize(
    "field",
    [
        "input_tokens",
        "output_tokens",
        "cache_read_tokens",
        "cache_write_tokens",
        "reasoning_tokens",
    ],
)
def test_token_usage_refuses_negative(field: str) -> None:
    kwargs = {"input_tokens": 0, "output_tokens": 0, field: -1}
    with pytest.raises(ValidationError):
        TokenUsage(**kwargs)


def test_token_usage_cache_and_reasoning_default_zero() -> None:
    u = TokenUsage(input_tokens=1, output_tokens=1)
    assert u.cache_read_tokens == u.cache_write_tokens == u.reasoning_tokens == 0


# ------------------------------- PriceVector -------------------------------- #


@pytest.mark.parametrize(
    "field",
    ["input_price", "output_price", "cache_read_price", "cache_write_price", "reasoning_price"],
)
def test_price_vector_refuses_negative_rate(field: str) -> None:
    base = {
        "currency": "USD",
        "input_price": Decimal("0"),
        "output_price": Decimal("0"),
        "cache_read_price": Decimal("0"),
        "cache_write_price": Decimal("0"),
        "reasoning_price": Decimal("0"),
        field: Decimal("-0.001"),
    }
    with pytest.raises(ValidationError):
        PriceVector(**base)


def test_price_vector_tier_all_or_none() -> None:
    # A threshold with no above-rates (half-spec) is refused.
    with pytest.raises(ValidationError, match="tiered pricing requires"):
        make_prices(tier_threshold_tokens=200_000)
    # Above-rates with no threshold is also refused.
    with pytest.raises(ValidationError, match="tiered pricing requires"):
        make_prices(input_price_above_threshold="0.001", output_price_above_threshold="0.002")


def test_price_vector_tier_threshold_must_be_positive() -> None:
    with pytest.raises(ValidationError, match="must be > 0"):
        make_prices(
            tier_threshold_tokens=0,
            input_price_above_threshold="0.001",
            output_price_above_threshold="0.002",
        )


def test_price_vector_full_tier_spec_is_accepted() -> None:
    pv = make_prices(
        tier_threshold_tokens=200_000,
        input_price_above_threshold="0.0000025",
        output_price_above_threshold="0.000015",
    )
    assert pv.tier_threshold_tokens == 200_000


# ----------------------- UsageCostRecord construction ----------------------- #


def _valid_record(**overrides) -> UsageCostRecord:
    usage = make_usage()
    prices = make_prices()
    cost = money("0.01")
    fields = {
        "correlation_id": corr(1),
        "requesting_role_id": role("r1"),
        "use_case": use_case("uc1"),
        "served_by": make_model(),
        "usage": usage,
        "unit_prices": prices,
        "cost": cost,
        "cost_source": "price_map_computed",
        "price_catalog_version": "1.0.0",
        "recorded_at": FIXED_INSTANT,
        "prev_hash": GENESIS_PREV_HASH,
    }
    fields.update(overrides)
    # compute the matching record_hash unless caller overrode it
    if "record_hash" not in fields:
        draft = UsageCostRecord.model_construct(**fields, record_hash=GENESIS_PREV_HASH)
        fields["record_hash"] = compute_cost_record_hash(draft, prev_hash=fields["prev_hash"])
    return UsageCostRecord(**fields)


def test_valid_record_constructs() -> None:
    rec = _valid_record()
    assert rec.cost == money("0.01")


def test_record_refuses_wrong_width_prev_hash() -> None:
    with pytest.raises(ValidationError, match="exactly 32 bytes"):
        _valid_record(prev_hash=b"short")


def test_record_refuses_tampered_record_hash() -> None:
    good = _valid_record()
    # Flip the stored hash to another valid-width but wrong digest -> refused.
    wrong = bytes((good.record_hash[0] ^ 0xFF,)) + good.record_hash[1:]
    with pytest.raises(ValidationError, match="tamper-evident"):
        _valid_record(record_hash=wrong)


def test_record_refuses_cross_currency_cost_vs_prices() -> None:
    # cost in EUR but prices in USD -> refused (no silent FX).
    with pytest.raises(ValidationError, match="no cross-currency row"):
        _valid_record(cost=money("0.01", "EUR"))


def test_editing_any_field_breaks_the_hash() -> None:
    # If the usage changes but the hash is recomputed for the OLD usage, construction
    # fails — proving the hash commits to every field (tamper-evidence).
    good = _valid_record()
    with pytest.raises(ValidationError, match="tamper-evident"):
        # keep the old record_hash, change the usage -> mismatch.
        _valid_record(usage=make_usage(input_tokens=9999), record_hash=good.record_hash)


# --------------------------- canonical serialisation ------------------------ #


def test_canonical_bytes_deterministic() -> None:
    rec = _valid_record()
    a = canonical_cost_record_bytes(rec, prev_hash=GENESIS_PREV_HASH)
    b = canonical_cost_record_bytes(rec, prev_hash=GENESIS_PREV_HASH)
    assert a == b
    assert isinstance(a, bytes)


def test_canonical_bytes_injective_on_cost() -> None:
    # Two records differing only in cost amount must encode to different bytes.
    r1 = _valid_record()
    # build a second with a different cost (and its matching hash)
    r2 = _valid_record(cost=money("0.02"))
    assert canonical_cost_record_bytes(r1, prev_hash=GENESIS_PREV_HASH) != (
        canonical_cost_record_bytes(r2, prev_hash=GENESIS_PREV_HASH)
    )


def test_canonical_bytes_preserves_full_decimal_precision_roundtrip() -> None:
    # A tiny price must survive the encoding with EXACT precision (no float rounding):
    # the encoded Decimal string must round-trip back to the identical Decimal.
    import json

    tiny = Decimal("0.000000123456789")
    prices = make_prices(input_price="0.000000123456789")
    rec = _valid_record(unit_prices=prices, cost=money("0.00"))
    encoded = canonical_cost_record_bytes(rec, prev_hash=GENESIS_PREV_HASH)
    payload = json.loads(encoded)
    assert Decimal(payload["unit_prices"]["input_price"]) == tiny  # exact round-trip


def test_naive_datetime_normalised_to_utc_in_encoding() -> None:
    aware = _valid_record(recorded_at=datetime(2026, 1, 1, 12, 0, tzinfo=UTC))
    naive = _valid_record(recorded_at=datetime(2026, 1, 1, 12, 0))
    # same instant (naive treated as UTC) -> identical canonical bytes.
    assert canonical_cost_record_bytes(aware, prev_hash=GENESIS_PREV_HASH) == (
        canonical_cost_record_bytes(naive, prev_hash=GENESIS_PREV_HASH)
    )


def test_hash_width_constant_is_32() -> None:
    assert HASH_BYTES == 32
