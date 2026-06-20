"""The spend-snapshot panel: per-model rollup table + a total / band / ledger-verify summary.

What this does
--------------
Defines :class:`SpendSnapshotPanel`, which maps a
:class:`~autofirm.cockpit.readmodels.spend_snapshot_view.SpendSnapshotView` into a per-model
rollup table (model key → exact amount) and a one-line subtitle carrying the grand total, the
budget band (or "no budget"), and the tamper-evident ledger-verify result. A ledger with no
spend rows renders the empty-state message while the subtitle still shows the zero total.

Why it exists / where it sits
-----------------------------
The operator's spend view. Sits in the tui layer; depends only on the base panel and the spend
read-model DTO (which carries the foundation ``Money`` and the pure band enum — no on-main
import).
"""

from __future__ import annotations

from autofirm.cockpit.readmodels.spend_snapshot_view import SpendSnapshotView
from autofirm.cockpit.tui.cockpit_table_panel import CockpitTablePanel

__all__ = ["SpendSnapshotPanel"]


class SpendSnapshotPanel(CockpitTablePanel):
    """A panel that renders the per-model spend rollup plus a total/band/verify summary."""

    def __init__(self) -> None:
        """Build the spend panel with its columns and empty-state message."""
        super().__init__(
            title="Spend — per model",
            columns=("Model", "Amount"),
            empty_message="No spend recorded yet.",
            panel_id="spend-snapshot-panel",
        )

    def show(self, view: SpendSnapshotView) -> None:
        """Render the per-model rollup and a total / band / ledger-verify summary line."""
        total = f"{view.grand_total.amount} {view.grand_total.currency}"
        band = "no budget" if view.band is None else view.band.name
        ledger = "verified" if view.ledger_verified else "UNVERIFIED"
        self.set_subtitle(f"Total {total} · band {band} · ledger {ledger}")
        rows = tuple(
            (model, f"{amount.amount} {amount.currency}")
            for model, amount in sorted(view.per_model.items())
        )
        self.display_rows(rows)
