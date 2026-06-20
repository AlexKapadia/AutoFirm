"""spend panel: mutation-hardening — exact title/columns/id and the total·band·ledger subtitle.

Covers all three subtitle branches: a budgeted+verified ledger, the no-budget band label, and
the tamper-evident UNVERIFIED ledger label (built explicitly since the default fixture verifies).
"""

from __future__ import annotations

from decimal import Decimal

from rich.table import Table
from textual.widgets import Static

from autofirm.cockpit.core.budget_threshold_state import BudgetBand
from autofirm.cockpit.readmodels.spend_snapshot_view import SpendSnapshotView
from autofirm.cockpit.tui.cockpit_app import CockpitApp
from autofirm.cockpit.tui.spend_snapshot_panel import SpendSnapshotPanel
from autofirm.foundation.money.money_amount import Money
from tests.cockpit.tui.synthetic_cockpit_read_model import synthetic_model

_QUIET = 1000.0


async def test_spend_panel_exact_title_columns_id_and_verified_subtitle() -> None:
    app = CockpitApp(synthetic_model(populated=True), refresh_interval=_QUIET)
    async with app.run_test() as pilot:
        await pilot.pause()
        panel = app.query_one("#spend-snapshot-panel", SpendSnapshotPanel)
        assert panel.query_one(".panel-title", Static).render().plain == "Spend — per model"
        table = getattr(panel.query_one(".panel-body", Static).render(), "_renderable", None)
        assert isinstance(table, Table)
        assert [c.header for c in table.columns] == ["Model", "Amount"]
        assert panel.subtitle == "Total 60.00 USD · band WARN_50 · ledger verified"


async def test_spend_panel_no_budget_band_label() -> None:
    app = CockpitApp(synthetic_model(populated=False), refresh_interval=_QUIET)
    async with app.run_test() as pilot:
        await pilot.pause()
        panel = app.query_one(SpendSnapshotPanel)
        assert panel.subtitle == "Total 0.00 USD · band no budget · ledger verified"


async def test_spend_panel_unverified_ledger_label() -> None:
    model = synthetic_model(populated=True)
    model.spend = SpendSnapshotView(
        grand_total=Money(Decimal("60.00"), "USD"),
        per_role={},
        per_use_case={},
        per_model={"openai/gpt-4": Money(Decimal("60.00"), "USD")},
        budget=Money(Decimal("100.00"), "USD"),
        band=BudgetBand.WARN_50,
        ledger_verified=False,
    )
    app = CockpitApp(model, refresh_interval=_QUIET)
    async with app.run_test() as pilot:
        await pilot.pause()
        panel = app.query_one(SpendSnapshotPanel)
        assert panel.subtitle == "Total 60.00 USD · band WARN_50 · ledger UNVERIFIED"
