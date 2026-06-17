"""PURE, deterministic spend rollups that sum EXACTLY (no float drift).

What this does
--------------
Aggregates a sequence of :class:`~autofirm.costledger.usage_cost_record.UsageCostRecord`
rows into exact per-dimension totals — per requesting role, per use-case, per model,
per provider, and the whole-company grand total — each a :class:`~autofirm.foundation
.money.Money`. Every rollup is a pure ``Decimal`` fold; the per-dimension subtotals
sum back to EXACTLY the grand total (no penny created or lost), which is the M3
acceptance metric (accuracy-bar-and-golden-set.md §4).

Why it exists / where it sits
-----------------------------
``data-contracts.md`` §8 attributes spend per role/team/use-case/model/company; this
is the read-side view over the append-only ledger. It is pure (no clock, no IO) so a
rollup is a deterministic function of the rows, trivially property-testable for the
"subtotals == grand total, exactly" invariant. It sits above the record contract and
reads what the ledger holds.

Security / compliance invariants upheld
---------------------------------------
* **Exact summation (§3.11):** all addition is via :class:`Money` (``Decimal``);
  there is no float path, so thousands of rows sum with zero drift.
* **Single-currency by construction (folder 09):** a rollup is computed within ONE
  currency; mixing currencies in one rollup is a refusal (convert via FX first).
* **Reversing entries net naturally:** a negative-cost correction reduces its
  dimension's subtotal AND the grand total identically, so corrections stay consistent.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from decimal import Decimal

from autofirm.costledger.usage_cost_record import UsageCostRecord
from autofirm.foundation.money.money_amount import Money

__all__ = [
    "grand_total",
    "rollup_by_model",
    "rollup_by_provider",
    "rollup_by_role",
    "rollup_by_use_case",
]


def grand_total(records: Iterable[UsageCostRecord], *, currency: str) -> Money:
    """Sum every row's cost in ``currency`` EXACTLY (the whole-company total).

    Args:
        records: The cost rows to total.
        currency: The single currency every row must be denominated in.

    Returns:
        The exact ``Money`` grand total (reversing entries net out).

    Raises:
        ValueError: If any row is a different currency (fail-closed, folder 09).
    """
    running = Money(Decimal(0), currency)
    for record in records:
        running = running + record.cost  # fail-closed on a currency mismatch
    return running


def rollup_by_role(records: Iterable[UsageCostRecord], *, currency: str) -> Mapping[str, Money]:
    """Total spend per ``requesting_role_id`` (exact; subtotals sum to grand total)."""
    return _rollup(records, currency=currency, key=lambda r: str(r.requesting_role_id))


def rollup_by_use_case(
    records: Iterable[UsageCostRecord], *, currency: str
) -> Mapping[str, Money]:
    """Total spend per ``use_case`` (exact; subtotals sum to grand total)."""
    return _rollup(records, currency=currency, key=lambda r: str(r.use_case))


def rollup_by_model(records: Iterable[UsageCostRecord], *, currency: str) -> Mapping[str, Money]:
    """Total spend per ``(provider, model_name)`` (exact; subtotals sum to grand total).

    The key is ``"<provider>/<model_name>"`` so two providers serving the same model
    name never collapse into one bucket (surface-aware attribution, folder 07).
    """
    return _rollup(
        records,
        currency=currency,
        key=lambda r: f"{r.served_by.provider.value}/{r.served_by.model_name}",
    )


def rollup_by_provider(
    records: Iterable[UsageCostRecord], *, currency: str
) -> Mapping[str, Money]:
    """Total spend per provider (exact; the per-provider total reconciliation uses)."""
    return _rollup(records, currency=currency, key=lambda r: r.served_by.provider.value)


def _rollup(
    records: Iterable[UsageCostRecord],
    *,
    currency: str,
    key: Callable[[UsageCostRecord], str],
) -> Mapping[str, Money]:
    """Fold rows into exact per-``key`` ``Money`` subtotals (the shared rollup core).

    Each subtotal starts at zero in ``currency`` and accumulates via :class:`Money`
    addition (Decimal, fail-closed on a currency mismatch), so the union of all
    subtotals equals the grand total exactly — no float, no lost penny (M3).
    """
    totals: dict[str, Money] = {}
    for record in records:
        bucket = key(record)
        current = totals.get(bucket, Money(Decimal(0), currency))
        totals[bucket] = current + record.cost  # fail-closed on a currency mismatch
    return totals
