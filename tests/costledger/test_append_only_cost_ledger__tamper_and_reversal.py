"""Hash-chain tamper + append-only + reversing-entry tests for the cost ledger (M5).

Proves the RFC-6962 chain detects reorder / insert / delete / modify (fail-closed),
that the ledger is append-only (no update/delete path), that corrections are reversing
entries that preserve the chain, and that totals (with corrections) are exact. Designed
to kill mutants on the chain-link comparison, the verify loop, and the genesis anchor.
"""

from decimal import Decimal

import pytest

from autofirm.costledger.append_only_cost_ledger import (
    GENESIS_PREV_HASH,
    AppendOnlyCostLedger,
    CostLedgerError,
)
from autofirm.costledger.exact_cost_computation import compute_exact_cost
from autofirm.foundation.money.money_amount import Money
from tests.costledger.synthetic_cost_fixtures import (
    FIXED_INSTANT,
    corr,
    make_model,
    make_prices,
    make_usage,
    role,
    use_case,
)


def _seed(n: int) -> AppendOnlyCostLedger:
    """Build a ledger with ``n`` sealed rows (each a distinct, valid cost)."""
    ledger = AppendOnlyCostLedger()
    prices = make_prices()
    for i in range(n):
        usage = make_usage(input_tokens=1000 * (i + 1), output_tokens=0)
        cost = compute_exact_cost(usage, prices)
        rec = ledger.seal_new(
            correlation_id=corr(i),
            requesting_role_id=role(f"r{i}"),
            use_case=use_case("uc"),
            served_by=make_model(),
            usage=usage,
            unit_prices=prices,
            cost=cost,
            cost_source="price_map_computed",
            price_catalog_version="1.0.0",
            recorded_at=FIXED_INSTANT,
        )
        ledger = ledger.append(rec)
    return ledger


def test_seal_append_chain_verifies() -> None:
    ledger = _seed(5)
    assert ledger.verify() is True
    assert len(ledger.records()) == 5


def test_genesis_prev_hash_is_all_zero_32_bytes() -> None:
    assert GENESIS_PREV_HASH == b"\x00" * 32
    assert _seed(1).records()[0].prev_hash == GENESIS_PREV_HASH


def test_modify_detected_construction_fails_closed() -> None:
    # A row whose stored hash does not match its content cannot even be built — and a
    # ledger wrapping such a tuple cannot be constructed (fail-closed).
    ledger = _seed(3)
    records = list(ledger.records())
    # Forge a row by copying a valid one but with a different cost and the OLD hash.
    forged = records[1].model_copy(update={"cost": Money(Decimal("9.99"), "USD")})
    with pytest.raises(CostLedgerError, match="tamper detected"):
        AppendOnlyCostLedger((records[0], forged, records[2]))


def test_reorder_detected_fail_closed() -> None:
    ledger = _seed(3)
    r = ledger.records()
    # Swapping two rows breaks each one's prev_hash chain link.
    with pytest.raises(CostLedgerError, match="tamper detected"):
        AppendOnlyCostLedger((r[0], r[2], r[1]))


def test_delete_middle_detected_fail_closed() -> None:
    ledger = _seed(3)
    r = ledger.records()
    # Dropping the middle row leaves r[2].prev_hash pointing at the deleted r[1].
    with pytest.raises(CostLedgerError, match="tamper detected"):
        AppendOnlyCostLedger((r[0], r[2]))


def test_insert_foreign_row_detected_fail_closed() -> None:
    a = _seed(2).records()
    b = _seed(3).records()  # a different chain
    # Splicing a foreign row in breaks the chain link.
    with pytest.raises(CostLedgerError, match="tamper detected"):
        AppendOnlyCostLedger((a[0], b[1], a[1]))


def test_append_with_wrong_prev_hash_refused() -> None:
    # A row chained over GENESIS cannot be appended to a non-empty ledger whose tip
    # is no longer genesis — its prev_hash does not match the current tip.
    ledger = _seed(2)
    genesis_anchored = _seed(1).records()[0]  # prev_hash == GENESIS, != ledger.tip
    assert genesis_anchored.prev_hash == GENESIS_PREV_HASH
    assert ledger.tip_hash != GENESIS_PREV_HASH
    with pytest.raises(CostLedgerError, match="broken chain"):
        ledger.append(genesis_anchored)


def test_append_returns_new_ledger_original_unchanged() -> None:
    # Append-only / immutable: appending does not mutate the original ledger.
    ledger = _seed(2)
    before = len(ledger.records())
    new_rec = ledger.seal_new(
        correlation_id=corr(99),
        requesting_role_id=role("rX"),
        use_case=use_case("uc"),
        served_by=make_model(),
        usage=make_usage(),
        unit_prices=make_prices(),
        cost=compute_exact_cost(make_usage(), make_prices()),
        cost_source="price_map_computed",
        price_catalog_version="1.0.0",
        recorded_at=FIXED_INSTANT,
    )
    grown = ledger.append(new_rec)
    assert len(ledger.records()) == before  # original untouched
    assert len(grown.records()) == before + 1


def test_reversing_entry_preserves_chain_and_nets_total() -> None:
    ledger = _seed(0)
    prices = make_prices()
    usage = make_usage(input_tokens=1000, output_tokens=0)  # cost 0.003 -> 0.00? use bigger
    usage = make_usage(input_tokens=1_000_000, output_tokens=0)  # 1e6*3e-6 = 3.00
    cost = compute_exact_cost(usage, prices)
    rec = ledger.seal_new(
        correlation_id=corr(1), requesting_role_id=role("r1"), use_case=use_case("uc"),
        served_by=make_model(), usage=usage, unit_prices=prices, cost=cost,
        cost_source="price_map_computed", price_catalog_version="1.0.0",
        recorded_at=FIXED_INSTANT,
    )
    ledger = ledger.append(rec)
    assert ledger.total("USD") == Money(Decimal("3.00"), "USD")
    # Correct via a reversing entry (exact negative), not an edit.
    reversal = ledger.seal_reversal(original=rec)
    ledger = ledger.append(reversal)
    assert ledger.verify() is True
    assert ledger.total("USD") == Money(Decimal("0.00"), "USD")  # netted to zero
    assert len(ledger.records()) == 2  # BOTH rows retained (audit trail)
    assert reversal.cost.amount == -cost.amount


def test_total_cross_currency_fails_closed() -> None:
    ledger = _seed(1)
    with pytest.raises(ValueError, match="cannot combine"):
        ledger.total("EUR")  # rows are USD


def test_empty_ledger_verifies_and_totals_zero() -> None:
    ledger = AppendOnlyCostLedger()
    assert ledger.verify() is True
    assert ledger.total("USD") == Money(Decimal("0"), "USD")
    assert ledger.tip_hash == GENESIS_PREV_HASH


def test_determinism_same_content_same_hash() -> None:
    # Two independently-sealed ledgers from identical content have identical hashes.
    a = _seed(3).records()
    b = _seed(3).records()
    assert [r.record_hash for r in a] == [r.record_hash for r in b]
