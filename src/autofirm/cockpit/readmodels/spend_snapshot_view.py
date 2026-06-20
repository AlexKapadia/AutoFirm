"""The spend-snapshot read-model: grand total + rollups + budget band + chain-verified flag.

What this does
--------------
Defines :class:`SpendSnapshotView`, the cockpit-facing projection of the on-main cost ledger:
the exact :class:`~autofirm.foundation.money.money_amount.Money` grand total, the per-role /
per-use-case / per-model rollup mappings (each an exact ``Money``), the optional budget and
its derived :class:`~autofirm.cockpit.core.budget_threshold_state.BudgetBand` (both ``None``
when no positive budget is supplied), and ``ledger_verified`` — the result of re-walking the
RFC-6962 hash chain. Built by :mod:`~autofirm.cockpit.adapters.spend_adapter`.

Why it exists / where it sits
-----------------------------
The operator's spend panel renders this view. Keeping band/budget optional lets the cockpit
show raw spend even when no budget is configured. Sits in the read-model layer; depends only
on the foundation ``Money`` type and the pure cockpit-core band enum (no on-main import).

Security / compliance invariants upheld
---------------------------------------
* **Immutable, read-only mappings (CLAUDE.md §3.2):** the rollup mappings are wrapped in a
  read-only :class:`~types.MappingProxyType` at construction, so a presented snapshot can
  never be mutated after the fact.
* **Tamper-evidence surfaced, never hidden:** ``ledger_verified`` carries the ledger's own
  ``verify()`` result verbatim — a broken chain is shown as ``False``, not swallowed.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from autofirm.cockpit.core.budget_threshold_state import BudgetBand
from autofirm.foundation.money.money_amount import Money

__all__ = ["SpendSnapshotView"]


@dataclass(frozen=True, slots=True)
class SpendSnapshotView:
    """An immutable snapshot of company spend: total, rollups, optional budget band, verify.

    Attributes:
        grand_total: The exact ``Money`` total across every ledger row.
        per_role: Exact spend per requesting-role id (read-only mapping).
        per_use_case: Exact spend per use-case id (read-only mapping).
        per_model: Exact spend per ``"<provider>/<model>"`` key (read-only mapping).
        budget: The configured budget ceiling, or ``None`` when none was supplied.
        band: The derived budget band, or ``None`` when no strictly-positive budget exists.
        ledger_verified: The ledger's RFC-6962 chain verification result.
    """

    grand_total: Money
    per_role: Mapping[str, Money]
    per_use_case: Mapping[str, Money]
    per_model: Mapping[str, Money]
    budget: Money | None
    band: BudgetBand | None
    ledger_verified: bool

    def __post_init__(self) -> None:
        """Freeze the rollup mappings into read-only proxies (immutability invariant).

        ``frozen=True`` only blocks attribute reassignment; the underlying dicts would still
        be mutable. Wrapping each in a :class:`~types.MappingProxyType` (via
        ``object.__setattr__``, the standard frozen-dataclass escape hatch) makes the
        presented rollups genuinely read-only.
        """
        object.__setattr__(self, "per_role", MappingProxyType(dict(self.per_role)))
        object.__setattr__(self, "per_use_case", MappingProxyType(dict(self.per_use_case)))
        object.__setattr__(self, "per_model", MappingProxyType(dict(self.per_model)))
