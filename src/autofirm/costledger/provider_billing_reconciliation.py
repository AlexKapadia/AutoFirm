"""PURE provider-billing reconciliation — Layer B zero-drift, gross-vs-gross.

What this does
--------------
Compares the ledger's per-provider GROSS total (summed from the append-only cost
rows) against a provider's own billing export for a CLOSED period, and emits a
labelled :class:`ReconciliationReport`: the gross drift per provider, the itemised
credits/promos (which legitimately make NET differ from GROSS — never silently
absorbed), and the net figure. On a faithful export the gross drift is exactly zero
(the M2 acceptance metric, accuracy-bar-and-golden-set.md §4).

Why it exists / where it sits
-----------------------------
``SYNTHESIS.md`` §6 / accuracy-bar §1 Layer B: providers do not return a per-request
cost (except OpenRouter), so our per-request cost is a reconstruction; it matches the
provider's reported total IFF we priced every bucket at the provider's rates with the
provider's usage. This module is the acceptance signal for that — and it is PURE (no
IO, no clock), so it is a deterministic function of (ledger rows, export). It reads
the per-provider rollup and compares gross-vs-gross.

Security / compliance invariants upheld
---------------------------------------
* **Gross-vs-gross, credits itemised (§1 Layer B):** the drift is computed on GROSS
  cost; credits/promos are a SEPARATE itemised ledger, reported as net — never folded
  silently into the drift (which would hide a real discrepancy).
* **Exact Decimal comparison (§3.11):** drift is a ``Decimal`` subtraction at the
  currency minor unit; "zero drift" means exact zero, not "close".
* **Single-currency per provider (folder 09):** a provider's ledger total and export
  must share a currency; a mismatch is a refusal (no cross-currency drift).
* **Closed periods only (§5 scope boundary):** the caller supplies a closed-period
  export; this module reconciles what it is given and labels the result.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator

from autofirm.costledger.spend_rollup_views import rollup_by_provider
from autofirm.costledger.usage_cost_record import UsageCostRecord
from autofirm.foundation.money.money_amount import Money

__all__ = [
    "ProviderBillingExport",
    "ProviderReconciliation",
    "ReconciliationReport",
    "reconcile_against_export",
]


class ProviderBillingExport(BaseModel):
    """One provider's own reported total for a CLOSED period, plus itemised credits.

    ``gross_total`` is the provider's pre-credit charge; ``credits`` is the itemised
    promotional/free-tier amount the invoice nets out (folder, §1 Layer B). NET =
    gross - credits. Both are :class:`Money` so the currency is carried, not assumed.
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    provider: str  # the provider identity this export covers (e.g. "anthropic")
    gross_total: Money  # the provider's pre-credit reported total for the period
    credits: Money  # itemised credits/promos the invoice nets out (>= 0 magnitude)

    @field_validator("provider")
    @classmethod
    def _provider_non_empty(cls, value: str) -> str:
        # fail-closed: an export with no provider cannot be matched to a ledger total.
        if not value.strip():
            raise ValueError("export provider must be non-empty")
        return value


class ProviderReconciliation(BaseModel):
    """The labelled reconciliation outcome for ONE provider (gross-vs-gross).

    ``gross_drift`` = ledger gross - provider gross (zero on a faithful export).
    ``is_zero_drift`` is the boolean the M2 metric asserts. ``net_after_credits`` is
    the provider gross minus itemised credits — reported, never used to mask drift.
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    provider: str
    ledger_gross: Money  # our gross total from the ledger rollup
    provider_gross: Money  # the provider's reported gross total
    gross_drift: Money  # ledger_gross - provider_gross (target: exactly zero)
    credits: Money  # itemised credits (the legitimate net-vs-gross difference)
    net_after_credits: Money  # provider_gross - credits (reported for transparency)

    @property
    def is_zero_drift(self) -> bool:
        """True iff the gross drift is EXACTLY zero (the M2 zero-drift target)."""
        return self.gross_drift.amount == Decimal(0)


class ReconciliationReport(BaseModel):
    """The whole multi-provider reconciliation result for a closed period.

    ``per_provider`` is one :class:`ProviderReconciliation` per provider reconciled;
    ``all_zero_drift`` is the headline M2 signal (every provider reconciled to exactly
    zero gross drift).
    """

    model_config = ConfigDict(frozen=True)

    per_provider: tuple[ProviderReconciliation, ...]

    @property
    def all_zero_drift(self) -> bool:
        """True iff EVERY provider reconciled to exactly zero gross drift (M2)."""
        return all(p.is_zero_drift for p in self.per_provider)


def reconcile_against_export(
    records: Iterable[UsageCostRecord],
    exports: Mapping[str, ProviderBillingExport],
    *,
    currency: str,
) -> ReconciliationReport:
    """Reconcile the ledger's per-provider gross totals against provider exports.

    For each provider present in EITHER the ledger or the exports, compute the gross
    drift (ledger gross - provider gross), itemise the credits, and report the net.
    A provider with rows but no export (or vice-versa) is still reported (its missing
    side totals to zero) so a gap is visible, never silently dropped.

    Args:
        records: The append-only cost rows for the closed period.
        exports: Per-provider billing exports, keyed by provider identity.
        currency: The single currency the period is reconciled in.

    Returns:
        A :class:`ReconciliationReport`; ``all_zero_drift`` is the M2 signal.

    Raises:
        ValueError: If any export's currency does not match ``currency`` (fail-closed:
            no cross-currency drift, folder 09).
    """
    ledger_totals = rollup_by_provider(records, currency=currency)
    zero = Money(Decimal(0), currency)

    providers = sorted(set(ledger_totals) | set(exports))  # deterministic order
    per_provider: list[ProviderReconciliation] = []
    for provider in providers:
        ledger_gross = ledger_totals.get(provider, zero)
        export = exports.get(provider)
        if export is None:
            # A provider we spent on but have no export for: report the full ledger
            # total as drift so the missing export is visible, not silently zero.
            provider_gross = zero
            credits = zero
        else:
            if export.gross_total.currency != currency or export.credits.currency != currency:
                # fail-closed: a cross-currency export cannot be reconciled here.
                raise ValueError(
                    f"export for {provider} is not in {currency} (no cross-currency drift)"
                )
            provider_gross = export.gross_total
            credits = export.credits
        per_provider.append(
            ProviderReconciliation(
                provider=provider,
                ledger_gross=ledger_gross,
                provider_gross=provider_gross,
                gross_drift=ledger_gross - provider_gross,  # exact Decimal (folder 08)
                credits=credits,
                net_after_credits=provider_gross - credits,
            )
        )
    return ReconciliationReport(per_provider=tuple(per_provider))
