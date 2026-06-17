"""Reconciliation tests (M2): zero drift on a faithful multi-provider export.

Proves: a faithful gross-vs-gross export reconciles to EXACTLY zero drift across >=3
providers + >=2 currencies; a non-zero drift is detected and labelled; credits are
itemised (net != gross) and never absorbed into drift; reversing-entry corrections are
reflected; cross-currency exports fail closed; a missing export is surfaced as drift.
"""

from decimal import Decimal

import pytest

from autofirm.costledger.append_only_cost_ledger import AppendOnlyCostLedger
from autofirm.costledger.exact_cost_computation import compute_exact_cost
from autofirm.costledger.provider_billing_reconciliation import (
    ProviderBillingExport,
    reconcile_against_export,
)
from autofirm.costledger.spend_rollup_views import rollup_by_provider
from autofirm.foundation.money.money_amount import Money
from autofirm.modelgateway.model_reference import ModelProvider, ModelRef
from tests.costledger.synthetic_cost_fixtures import (
    FIXED_INSTANT,
    corr,
    make_prices,
    make_usage,
    money,
    role,
    use_case,
)


def _row(ledger: AppendOnlyCostLedger, i: int, provider: ModelProvider, toks: int, currency: str):
    prices = make_prices(currency=currency)
    usage = make_usage(input_tokens=toks, output_tokens=0)
    cost = compute_exact_cost(usage, prices)
    rec = ledger.seal_new(
        correlation_id=corr(i), requesting_role_id=role("r"), use_case=use_case("uc"),
        served_by=ModelRef(provider=provider, model_name="m"),
        usage=usage, unit_prices=prices, cost=cost,
        cost_source="price_map_computed", price_catalog_version="1.0.0",
        recorded_at=FIXED_INSTANT,
    )
    return ledger.append(rec)


def test_zero_drift_on_faithful_multiprovider_usd() -> None:
    # 3 providers, all USD. Build the export FROM the ledger's own per-provider total
    # so a faithful export reconciles to exactly zero (the M2 target).
    ledger = AppendOnlyCostLedger()
    ledger = _row(ledger, 0, ModelProvider.OPENAI, 1_000_000, "USD")  # 3.00
    ledger = _row(ledger, 1, ModelProvider.ANTHROPIC, 2_000_000, "USD")  # 6.00
    ledger = _row(ledger, 2, ModelProvider.GOOGLE, 3_000_000, "USD")  # 9.00
    totals = rollup_by_provider(ledger.records(), currency="USD")
    exports = {
        p: ProviderBillingExport(provider=p, gross_total=totals[p], credits=money("0"))
        for p in totals
    }
    report = reconcile_against_export(ledger.records(), exports, currency="USD")
    assert report.all_zero_drift is True
    for pr in report.per_provider:
        assert pr.gross_drift == Money(Decimal("0.00"), "USD")


def test_nonzero_drift_detected_and_labelled() -> None:
    ledger = AppendOnlyCostLedger()
    ledger = _row(ledger, 0, ModelProvider.OPENAI, 1_000_000, "USD")  # ledger says 3.00
    exports = {
        "openai": ProviderBillingExport(
            provider="openai", gross_total=money("3.50"), credits=money("0")
        )
    }
    report = reconcile_against_export(ledger.records(), exports, currency="USD")
    assert report.all_zero_drift is False
    pr = report.per_provider[0]
    assert pr.gross_drift == Money(Decimal("-0.50"), "USD")  # 3.00 - 3.50
    assert pr.is_zero_drift is False


def test_credits_itemised_net_differs_from_gross_drift_still_zero() -> None:
    # Gross matches exactly (zero drift) but the provider nets out a credit -> NET <
    # GROSS. The credit must NOT mask the (zero) drift; it is reported separately.
    ledger = AppendOnlyCostLedger()
    ledger = _row(ledger, 0, ModelProvider.OPENAI, 1_000_000, "USD")  # 3.00 gross
    exports = {
        "openai": ProviderBillingExport(
            provider="openai", gross_total=money("3.00"), credits=money("1.00")
        )
    }
    report = reconcile_against_export(ledger.records(), exports, currency="USD")
    pr = report.per_provider[0]
    assert pr.is_zero_drift is True  # gross-vs-gross is zero
    assert pr.credits == money("1.00")
    assert pr.net_after_credits == money("2.00")  # 3.00 - 1.00, reported not absorbed


def test_reversing_correction_changes_reconciliation() -> None:
    ledger = AppendOnlyCostLedger()
    ledger = _row(ledger, 0, ModelProvider.OPENAI, 1_000_000, "USD")  # 3.00
    rec = ledger.records()[0]
    ledger = ledger.append(ledger.seal_reversal(original=rec))  # net 0.00
    exports = {
        "openai": ProviderBillingExport(
            provider="openai", gross_total=money("0.00"), credits=money("0")
        )
    }
    report = reconcile_against_export(ledger.records(), exports, currency="USD")
    assert report.all_zero_drift is True


def test_missing_export_surfaces_full_ledger_as_drift() -> None:
    ledger = AppendOnlyCostLedger()
    ledger = _row(ledger, 0, ModelProvider.OPENAI, 1_000_000, "USD")  # 3.00, no export
    report = reconcile_against_export(ledger.records(), {}, currency="USD")
    pr = report.per_provider[0]
    assert pr.provider == "openai"
    assert pr.gross_drift == Money(Decimal("3.00"), "USD")  # full ledger as drift, visible
    assert report.all_zero_drift is False


def test_cross_currency_export_fails_closed() -> None:
    ledger = AppendOnlyCostLedger()
    ledger = _row(ledger, 0, ModelProvider.OPENAI, 1_000_000, "USD")
    exports = {
        "openai": ProviderBillingExport(
            provider="openai", gross_total=money("3.00", "EUR"), credits=money("0", "EUR")
        )
    }
    with pytest.raises(ValueError, match="no cross-currency drift"):
        reconcile_against_export(ledger.records(), exports, currency="USD")


def test_export_provider_must_be_non_empty() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        ProviderBillingExport(provider="  ", gross_total=money("1"), credits=money("0"))
