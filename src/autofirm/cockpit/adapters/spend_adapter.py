"""The spend adapter: project the cost ledger into a cockpit spend read-model.

What this does
--------------
Defines :func:`build_spend_snapshot_view`, which reads an on-main
:class:`~autofirm.costledger.append_only_cost_ledger.AppendOnlyCostLedger` and produces a
:class:`~autofirm.cockpit.readmodels.spend_snapshot_view.SpendSnapshotView`: the exact grand
total and the per-role / per-use-case / per-model rollups (via the pure
:mod:`~autofirm.costledger.spend_rollup_views` functions), the ledger's RFC-6962
``verify()`` result, and — only when a strictly-positive budget is supplied — the derived
:class:`~autofirm.cockpit.core.budget_threshold_state.BudgetBand`. Read-only.

Why it exists / where it sits
-----------------------------
This is the seam that turns the live cost ledger into the cockpit's spend panel data. The
budget is INJECTED by C3 composition (the cockpit does not own a budget source); when none is
given (or a non-positive one is), the band is ``None`` and raw spend is still shown. Sits in
the adapters layer (the only cockpit layer allowed to import on-main domain types).

Security / compliance invariants upheld
---------------------------------------
* **Read-only projection (CLAUDE.md §3.2):** the adapter only reads ``records()`` / ``verify()``
  and folds them with pure functions — it never appends to or mutates the ledger.
* **Exact money, single currency (§3.11 / folder 09):** all totals are ``Money`` (Decimal);
  ``currency`` is threaded through every rollup, and a cross-currency row fails closed upstream.
* **Tamper-evidence surfaced (§5.6):** ``verify()`` is carried into ``ledger_verified`` verbatim
  — a broken chain shows as ``False``, never hidden.
"""

from __future__ import annotations

from autofirm.cockpit.core.budget_threshold_state import BudgetBand, classify_budget_band
from autofirm.cockpit.readmodels.spend_snapshot_view import SpendSnapshotView
from autofirm.costledger.append_only_cost_ledger import AppendOnlyCostLedger
from autofirm.costledger.spend_rollup_views import (
    grand_total,
    rollup_by_model,
    rollup_by_role,
    rollup_by_use_case,
)
from autofirm.foundation.money.money_amount import Money

__all__ = ["build_spend_snapshot_view"]


def build_spend_snapshot_view(
    ledger: AppendOnlyCostLedger,
    *,
    currency: str,
    budget: Money | None = None,
) -> SpendSnapshotView:
    """Project a cost ledger into an immutable :class:`SpendSnapshotView` (read-only).

    Args:
        ledger: The append-only cost ledger to read.
        currency: The single ISO-4217 currency every row is denominated in (threaded through
            every rollup).
        budget: An optional budget ceiling. A band is classified ONLY when ``budget`` is not
            ``None`` and its amount is strictly positive; otherwise ``band`` is ``None``.

    Returns:
        A :class:`SpendSnapshotView` carrying the exact total, the three rollups, the optional
        budget + band, and the ledger's chain-verification result.
    """
    records = ledger.records()
    total = grand_total(records, currency=currency)
    band = _classify_band(total, budget)
    return SpendSnapshotView(
        grand_total=total,
        per_role=rollup_by_role(records, currency=currency),
        per_use_case=rollup_by_use_case(records, currency=currency),
        per_model=rollup_by_model(records, currency=currency),
        budget=budget,
        band=band,
        ledger_verified=ledger.verify(),
    )


def _classify_band(total: Money, budget: Money | None) -> BudgetBand | None:
    """Classify the band, or return ``None`` when no strictly-positive budget is supplied.

    Guarding on ``budget.amount > 0`` here keeps the classifier's fail-closed contract intact:
    :func:`classify_budget_band` refuses a non-positive budget, so the cockpit treats "no
    positive budget configured" as simply "no band to show" rather than an error.
    """
    if budget is None or budget.amount <= 0:
        return None
    return classify_budget_band(total, budget)
