"""Exact-summation rollup tests (M3): subtotals sum to the grand total, no drift.

Proves the per-role / use-case / model / provider rollups each sum EXACTLY to the
grand total across thousands of synthetic rows (no penny created or lost), that
reversing entries net naturally, and that cross-currency rollups fail closed.
"""

from decimal import Decimal

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from autofirm.costledger.append_only_cost_ledger import AppendOnlyCostLedger
from autofirm.costledger.exact_cost_computation import compute_exact_cost
from autofirm.costledger.spend_rollup_views import (
    grand_total,
    rollup_by_model,
    rollup_by_provider,
    rollup_by_role,
    rollup_by_use_case,
)
from autofirm.foundation.money.money_amount import Money
from autofirm.modelgateway.model_reference import ModelProvider, ModelRef
from tests.costledger.synthetic_cost_fixtures import (
    FIXED_INSTANT,
    corr,
    make_prices,
    make_usage,
    role,
    use_case,
)

_PROVIDERS = list(ModelProvider)


def _ledger_of(specs: list[tuple[int, int, int]]) -> AppendOnlyCostLedger:
    """Build a ledger; each spec is (role_idx, provider_idx, input_tokens)."""
    ledger = AppendOnlyCostLedger()
    prices = make_prices()
    for i, (role_idx, prov_idx, toks) in enumerate(specs):
        usage = make_usage(input_tokens=toks, output_tokens=0)
        cost = compute_exact_cost(usage, prices)
        model = ModelRef(provider=_PROVIDERS[prov_idx % len(_PROVIDERS)], model_name=f"m{prov_idx}")
        rec = ledger.seal_new(
            correlation_id=corr(i),
            requesting_role_id=role(f"r{role_idx}"),
            use_case=use_case(f"uc{role_idx % 3}"),
            served_by=model,
            usage=usage,
            unit_prices=prices,
            cost=cost,
            cost_source="price_map_computed",
            price_catalog_version="1.0.0",
            recorded_at=FIXED_INSTANT,
        )
        ledger = ledger.append(rec)
    return ledger


def _sum(rollup) -> Money:
    total = Money(Decimal(0), "USD")
    for v in rollup.values():
        total = total + v
    return total


def test_known_rollup_by_role() -> None:
    ledger = _ledger_of([(0, 0, 1_000_000), (1, 0, 2_000_000), (0, 1, 1_000_000)])
    # role0: 1M+1M tokens @3e-6 = 3.00+3.00=6.00 ; role1: 2M = 6.00
    by_role = rollup_by_role(ledger.records(), currency="USD")
    assert by_role["r0"] == Money(Decimal("6.00"), "USD")
    assert by_role["r1"] == Money(Decimal("6.00"), "USD")


@settings(max_examples=60)
@given(
    specs=st.lists(
        st.tuples(
            st.integers(min_value=0, max_value=9),  # role
            st.integers(min_value=0, max_value=4),  # provider
            st.integers(min_value=0, max_value=5_000_000),  # tokens
        ),
        min_size=1,
        max_size=400,
    )
)
def test_all_rollups_sum_to_grand_total_exactly(specs) -> None:
    ledger = _ledger_of(specs)
    records = ledger.records()
    gt = grand_total(records, currency="USD")
    assert _sum(rollup_by_role(records, currency="USD")) == gt
    assert _sum(rollup_by_use_case(records, currency="USD")) == gt
    assert _sum(rollup_by_model(records, currency="USD")) == gt
    assert _sum(rollup_by_provider(records, currency="USD")) == gt


def test_thousands_of_rows_sum_exactly() -> None:
    # Rollups operate on the row sequence directly (no per-append re-verification
    # needed here), so build the records list once and total it — exact across 3000.
    ledger = AppendOnlyCostLedger()
    prices = make_prices()
    records = []
    for i in range(3000):
        usage = make_usage(input_tokens=(i % 7) * 100_003, output_tokens=0)
        rec = ledger.seal_new(
            correlation_id=corr(i), requesting_role_id=role(f"r{i % 10}"),
            use_case=use_case(f"uc{i % 3}"),
            served_by=ModelRef(provider=_PROVIDERS[i % 5], model_name=f"m{i % 5}"),
            usage=usage, unit_prices=prices, cost=compute_exact_cost(usage, prices),
            cost_source="price_map_computed", price_catalog_version="1.0.0",
            recorded_at=FIXED_INSTANT,
        )
        ledger = ledger.append(rec)
        records.append(rec)
    gt = grand_total(records, currency="USD")
    assert _sum(rollup_by_role(records, currency="USD")) == gt
    assert _sum(rollup_by_model(records, currency="USD")) == gt


def test_reversing_entry_reduces_rollup_and_total() -> None:
    ledger = _ledger_of([(0, 0, 1_000_000)])  # role r0, 3.00
    rec = ledger.records()[0]
    ledger = ledger.append(ledger.seal_reversal(original=rec))
    gt = grand_total(ledger.records(), currency="USD")
    assert gt == Money(Decimal("0.00"), "USD")
    assert rollup_by_role(ledger.records(), currency="USD")["r0"] == Money(Decimal("0.00"), "USD")


def test_rollup_cross_currency_fails_closed() -> None:
    ledger = _ledger_of([(0, 0, 1_000_000)])
    with pytest.raises(ValueError, match="cannot combine"):
        rollup_by_role(ledger.records(), currency="EUR")
