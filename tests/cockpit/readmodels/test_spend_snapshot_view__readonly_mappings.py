"""SpendSnapshotView: read-only rollup mappings + optional budget/band carriage."""

from __future__ import annotations

from decimal import Decimal

import pytest

from autofirm.cockpit.core.budget_threshold_state import BudgetBand
from autofirm.cockpit.readmodels.spend_snapshot_view import SpendSnapshotView
from autofirm.foundation.money.money_amount import Money


def _money(amount: str) -> Money:
    return Money(Decimal(amount), "USD")


def _view(*, budget: Money | None = None, band: BudgetBand | None = None) -> SpendSnapshotView:
    return SpendSnapshotView(
        grand_total=_money("10.00"),
        per_role={"r-0": _money("6.00"), "r-1": _money("4.00")},
        per_use_case={"uc-0": _money("10.00")},
        per_model={"openai/gpt-x": _money("10.00")},
        budget=budget,
        band=band,
        ledger_verified=True,
    )


def test_carries_total_rollups_and_verify_flag() -> None:
    view = _view()
    assert view.grand_total == _money("10.00")
    assert view.per_role["r-0"] == _money("6.00")
    assert view.per_use_case["uc-0"] == _money("10.00")
    assert view.per_model["openai/gpt-x"] == _money("10.00")
    assert view.ledger_verified is True


def test_rollup_mappings_are_read_only() -> None:
    view = _view()
    # MappingProxyType refuses item assignment -> a presented snapshot cannot be mutated.
    with pytest.raises(TypeError):
        view.per_role["r-2"] = _money("1.00")  # type: ignore[index]
    with pytest.raises(TypeError):
        view.per_use_case["x"] = _money("1.00")  # type: ignore[index]
    with pytest.raises(TypeError):
        view.per_model["y"] = _money("1.00")  # type: ignore[index]


def test_mutating_source_dict_after_construction_does_not_leak_in() -> None:
    source = {"r-0": _money("6.00")}
    view = SpendSnapshotView(
        grand_total=_money("6.00"),
        per_role=source,
        per_use_case={},
        per_model={},
        budget=None,
        band=None,
        ledger_verified=True,
    )
    source["r-9"] = _money("99.00")  # mutate the original after construction
    assert "r-9" not in view.per_role  # the view copied; it is not aliased to source


def test_optional_budget_and_band_default_to_none() -> None:
    view = _view()
    assert view.budget is None
    assert view.band is None


def test_budget_and_band_carried_when_supplied() -> None:
    view = _view(budget=_money("12.00"), band=BudgetBand.WARN_80)
    assert view.budget == _money("12.00")
    assert view.band is BudgetBand.WARN_80


def test_view_is_frozen() -> None:
    view = _view()
    with pytest.raises(AttributeError):
        view.ledger_verified = False  # type: ignore[misc]
