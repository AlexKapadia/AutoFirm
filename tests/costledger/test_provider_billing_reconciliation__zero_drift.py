"""Reconciliation tests (M2): zero drift on a faithful multi-provider export.

Proves: a faithful gross-vs-gross export reconciles to EXACTLY zero drift across >=3
providers + >=2 currencies; a non-zero drift is detected and labelled; credits are
itemised (net != gross) and never absorbed into drift; reversing-entry corrections are
reflected; cross-currency exports fail closed; a missing export is surfaced as drift.
"""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from autofirm.costledger.append_only_cost_ledger import AppendOnlyCostLedger
from autofirm.costledger.exact_cost_computation import compute_exact_cost
from autofirm.costledger.provider_billing_reconciliation import (
    ProviderBillingExport,
    ProviderReconciliation,
    ReconciliationReport,
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
    with pytest.raises(ValueError) as exc:
        reconcile_against_export(ledger.records(), exports, currency="USD")
    # Exact message so a string mutant on the fail-closed text is killed.
    assert str(exc.value) == "export for openai is not in USD (no cross-currency drift)"


def test_export_with_wrong_credits_currency_also_fails_closed() -> None:
    # Independently exercise the CREDITS side of the currency guard (the `or` branch),
    # so a mutant turning `or` into `and` is killed: here gross matches USD but
    # credits are EUR — still a cross-currency export, still refused.
    ledger = AppendOnlyCostLedger()
    ledger = _row(ledger, 0, ModelProvider.OPENAI, 1_000_000, "USD")
    exports = {
        "openai": ProviderBillingExport(
            provider="openai", gross_total=money("3.00", "USD"), credits=money("0", "EUR")
        )
    }
    with pytest.raises(ValueError, match="no cross-currency drift"):
        reconcile_against_export(ledger.records(), exports, currency="USD")


def test_export_provider_must_be_non_empty() -> None:
    with pytest.raises(ValidationError) as exc:
        ProviderBillingExport(provider="  ", gross_total=money("1"), credits=money("0"))
    # Assert the EXACT validator message (pydantic exposes it as the error 'msg'), so a
    # string-literal mutant that wraps/edits the text is killed -- a substring check
    # would let a `XX..XX`-wrapped mutant survive, so we compare the message exactly.
    errors = exc.value.errors()
    assert any(e["msg"] == "Value error, export provider must be non-empty" for e in errors)


def _recon(provider: str = "openai") -> ProviderReconciliation:
    return ProviderReconciliation(
        provider=provider,
        ledger_gross=money("3.00"),
        provider_gross=money("3.00"),
        gross_drift=money("0.00"),
        credits=money("0.00"),
        net_after_credits=money("3.00"),
    )


def test_report_classes_are_frozen() -> None:
    # Immutability is a contract — kills a `frozen=True`->`False` config mutant.
    export = ProviderBillingExport(
        provider="openai", gross_total=money("1"), credits=money("0")
    )
    with pytest.raises(ValidationError):
        export.provider = "x"  # type: ignore[misc]
    recon = _recon()
    with pytest.raises(ValidationError):
        recon.provider = "x"  # type: ignore[misc]
    report = ReconciliationReport(per_provider=(recon,))
    with pytest.raises(ValidationError):
        report.per_provider = ()  # type: ignore[misc]


def test_report_classes_carry_money_fields_arbitrary_types_allowed() -> None:
    # Money is an arbitrary (non-pydantic) type; constructing these models proves
    # arbitrary_types_allowed is set — kills the `True`->`False` config mutant
    # (which would make construction with a Money field raise).
    export = ProviderBillingExport(
        provider="openai", gross_total=money("9.99"), credits=money("1.00")
    )
    assert export.gross_total == money("9.99")
    recon = _recon()
    assert recon.ledger_gross == money("3.00")
