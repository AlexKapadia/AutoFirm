"""spend_adapter: rollups, optional band at exact boundaries, verify propagation, currency."""

from __future__ import annotations

from decimal import Decimal

import pytest

from autofirm.cockpit.adapters.spend_adapter import build_spend_snapshot_view
from autofirm.cockpit.core.budget_threshold_state import BudgetBand
from autofirm.costledger.append_only_cost_ledger import AppendOnlyCostLedger
from autofirm.foundation.money.money_amount import Money
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


def _ledger(rows: list[tuple[str, str, str, str]]) -> AppendOnlyCostLedger:
    """Build a ledger; each row is (role, use_case, model_name, cost_amount) in USD."""
    from autofirm.modelgateway.model_reference import ModelProvider

    ledger = AppendOnlyCostLedger()
    for i, (r, uc, model_name, amount) in enumerate(rows):
        rec = ledger.seal_new(
            correlation_id=corr(i),
            requesting_role_id=role(r),
            use_case=use_case(uc),
            served_by=make_model(ModelProvider.OPENAI, model_name),
            usage=make_usage(),
            unit_prices=make_prices(),
            cost=money(amount),
            cost_source="price_map_computed",
            price_catalog_version="1.0.0",
            recorded_at=FIXED_INSTANT,
        )
        ledger = ledger.append(rec)
    return ledger


# --------------------------- empty + verify --------------------------- #


def test_empty_ledger_is_zero_total_empty_rollups_verified() -> None:
    view = build_spend_snapshot_view(AppendOnlyCostLedger(), currency="USD")
    assert view.grand_total == money("0")
    assert dict(view.per_role) == {}
    assert dict(view.per_use_case) == {}
    assert dict(view.per_model) == {}
    assert view.ledger_verified is True
    assert view.band is None
    assert view.budget is None


def test_broken_chain_propagates_to_ledger_verified_false() -> None:
    valid = _ledger([("r0", "uc0", "m0", "5.00")]).records()[0]
    tampered = valid.model_copy(update={"cost": money("999.00")})  # hash no longer matches
    ledger = AppendOnlyCostLedger((tampered,), _trusted=True)  # bypass construct-time verify
    view = build_spend_snapshot_view(ledger, currency="USD")
    assert view.ledger_verified is False  # the broken chain is surfaced, not hidden


# --------------------------- rollups --------------------------- #


def test_rollups_map_keys_to_exact_subtotals() -> None:
    view = build_spend_snapshot_view(
        _ledger(
            [
                ("r0", "uc0", "m0", "6.00"),
                ("r1", "uc0", "m1", "4.00"),
                ("r0", "uc1", "m0", "1.00"),
            ]
        ),
        currency="USD",
    )
    assert view.grand_total == money("11.00")
    assert dict(view.per_role) == {"r0": money("7.00"), "r1": money("4.00")}
    assert dict(view.per_use_case) == {"uc0": money("10.00"), "uc1": money("1.00")}
    assert dict(view.per_model) == {
        "openai/m0": money("7.00"),
        "openai/m1": money("4.00"),
    }


# --------------------------- band at exact boundaries --------------------------- #


@pytest.mark.parametrize(
    ("total", "budget", "expected"),
    [
        ("10.00", "100.00", BudgetBand.OK),  # 10%
        ("50.00", "100.00", BudgetBand.WARN_50),  # exactly 50%
        ("80.00", "100.00", BudgetBand.WARN_80),  # exactly 80%
        ("95.00", "100.00", BudgetBand.CRIT_95),  # exactly 95%
        ("49.99", "100.00", BudgetBand.OK),  # just under 50%
    ],
)
def test_band_classified_at_boundaries_when_budget_positive(
    total: str, budget: str, expected: BudgetBand
) -> None:
    view = build_spend_snapshot_view(
        _ledger([("r0", "uc0", "m0", total)]), currency="USD", budget=money(budget)
    )
    assert view.band is expected
    assert view.budget == money(budget)


def test_band_none_when_budget_is_none() -> None:
    view = build_spend_snapshot_view(_ledger([("r0", "uc0", "m0", "5.00")]), currency="USD")
    assert view.band is None


def test_band_none_when_budget_is_zero() -> None:
    view = build_spend_snapshot_view(
        _ledger([("r0", "uc0", "m0", "5.00")]), currency="USD", budget=money("0.00")
    )
    assert view.band is None  # non-positive budget -> no band (classifier not invoked)


def test_band_none_when_budget_is_negative() -> None:
    view = build_spend_snapshot_view(
        _ledger([("r0", "uc0", "m0", "5.00")]), currency="USD", budget=money("-5.00")
    )
    assert view.band is None


# --------------------------- currency threading --------------------------- #


def test_currency_is_threaded_through_totals_and_band() -> None:
    ledger = AppendOnlyCostLedger()
    rec = ledger.seal_new(
        correlation_id=corr(0),
        requesting_role_id=role("r0"),
        use_case=use_case("uc0"),
        served_by=make_model(),
        usage=make_usage(),
        unit_prices=make_prices(currency="JPY"),
        cost=Money(Decimal("500"), "JPY"),
        cost_source="price_map_computed",
        price_catalog_version="1.0.0",
        recorded_at=FIXED_INSTANT,
    )
    ledger = ledger.append(rec)
    view = build_spend_snapshot_view(
        ledger, currency="JPY", budget=Money(Decimal("1000"), "JPY")
    )
    assert view.grand_total == Money(Decimal("500"), "JPY")
    assert view.per_role["r0"] == Money(Decimal("500"), "JPY")
    assert view.band is BudgetBand.WARN_50  # 500/1000 == exactly 50%, in JPY
