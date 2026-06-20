"""Boundary-exact kill for the spend adapter's positive-budget guard (CLAUDE.md §3.6).

Why this file exists
--------------------
``_classify_band`` guards on ``budget.amount <= 0`` (no band unless the budget is STRICTLY
positive). The behavioural suite tests budgets of 0, a negative, and amounts >= 10, none of
which distinguish ``<= 0`` from mutmut's ``<= 1`` mutant. This pins the exact boundary at
``amount == 1``: a budget of exactly 1 is strictly positive, so a band MUST be classified --
the ``<= 1`` mutant would wrongly suppress it.
"""

from __future__ import annotations

from decimal import Decimal

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


def _usd(amount: str) -> Money:
    return Money(Decimal(amount), "USD")


def _ledger_with_cost(amount: str) -> AppendOnlyCostLedger:
    from autofirm.modelgateway.model_reference import ModelProvider

    ledger = AppendOnlyCostLedger()
    rec = ledger.seal_new(
        correlation_id=corr(0),
        requesting_role_id=role("r0"),
        use_case=use_case("uc0"),
        served_by=make_model(ModelProvider.OPENAI, "m0"),
        usage=make_usage(),
        unit_prices=make_prices(),
        cost=money(amount),
        cost_source="price_map_computed",
        price_catalog_version="1.0.0",
        recorded_at=FIXED_INSTANT,
    )
    return ledger.append(rec)


def test_band_classified_when_budget_amount_is_exactly_one() -> None:
    # amount == 1 is strictly positive (> 0) -> a band MUST be produced. The `<= 1` mutant
    # would treat 1 as non-positive and return None, so a non-None band kills it.
    view = build_spend_snapshot_view(
        _ledger_with_cost("1.00"), currency="USD", budget=_usd("1.00")
    )
    assert view.band is BudgetBand.CRIT_95  # 1.00 / 1.00 == 100% -> CRIT_95


def test_band_ok_at_fractional_positive_budget_below_one() -> None:
    # 0 < amount < 1 is still strictly positive; original classifies, `<= 1` mutant returns None.
    view = build_spend_snapshot_view(
        _ledger_with_cost("0.01"), currency="USD", budget=_usd("0.50")
    )
    assert view.band is BudgetBand.OK  # 0.01 / 0.50 == 2% -> OK (and crucially NOT None)
