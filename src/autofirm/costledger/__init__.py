"""AutoFirm cost ledger — 100%-accurate cross-model spend/cost accounting (W5).

Exact ``Decimal`` cost = f(provider-returned usage, versioned frozen price snapshot),
recorded as append-only, RFC-6962 hash-chained rows, reconciled to zero drift against
each provider's billing export. Implements the honest three-layer accuracy bar
(``docs/research/B5-exact-cost-accounting/accuracy-bar-and-golden-set.md``):
Layer A exact-to-the-cent computation, Layer B zero-drift reconciliation on closed
periods (gross-vs-gross, credits itemised), Layer C provider usage trusted as ground
truth.

Layering (low -> high):
* :mod:`~autofirm.costledger.usage_cost_record` — ``TokenUsage`` / ``PriceVector`` /
  ``UsageCostRecord`` (frozen, fail-closed, hash-validated).
* :mod:`~autofirm.costledger.cost_record_canonical_hashing` — the one canonical
  serialisation + RFC-6962 leaf hash for a row (reuses ``audit.rfc6962_hashing``).
* :mod:`~autofirm.costledger.price_catalog_contract` — the SemVer-versioned, SHA-pinned
  frozen price snapshot with explicit ``unit_divisor`` (fail-closed lookup).
* :mod:`~autofirm.costledger.provider_usage_adapters` — per-provider usage parsers
  encoding the INVERTED cache-subset / reasoning / field-name quirks.
* :mod:`~autofirm.costledger.exact_cost_computation` — the PURE
  ``(TokenUsage, PriceVector) -> Money`` exact cost (Layer A; mutation-critical).
* :mod:`~autofirm.costledger.append_only_cost_ledger` — the append-only, hash-chained
  ledger; corrections are reversing entries (mutation-critical).
* :mod:`~autofirm.costledger.spend_rollup_views` — pure exact rollups (per role / use
  case / model / provider / company).
* :mod:`~autofirm.costledger.provider_billing_reconciliation` — Layer B zero-drift,
  gross-vs-gross reconciliation against a provider export (mutation-critical).
"""

from __future__ import annotations

from autofirm.costledger.append_only_cost_ledger import (
    GENESIS_PREV_HASH,
    AppendOnlyCostLedger,
    CostLedgerError,
)
from autofirm.costledger.exact_cost_computation import compute_exact_cost
from autofirm.costledger.price_catalog_contract import (
    PriceCatalog,
    PriceCatalogEntry,
    PriceCatalogLookupError,
)
from autofirm.costledger.provider_billing_reconciliation import (
    ProviderBillingExport,
    ProviderReconciliation,
    ReconciliationReport,
    reconcile_against_export,
)
from autofirm.costledger.provider_usage_adapters import (
    UsageParseError,
    parse_anthropic_usage,
    parse_bedrock_usage,
    parse_google_usage,
    parse_openai_usage,
)
from autofirm.costledger.spend_rollup_views import (
    grand_total,
    rollup_by_model,
    rollup_by_provider,
    rollup_by_role,
    rollup_by_use_case,
)
from autofirm.costledger.usage_cost_record import (
    CostSource,
    PriceVector,
    TokenUsage,
    UsageCostRecord,
)

__all__ = [
    "GENESIS_PREV_HASH",
    "AppendOnlyCostLedger",
    "CostLedgerError",
    "CostSource",
    "PriceCatalog",
    "PriceCatalogEntry",
    "PriceCatalogLookupError",
    "PriceVector",
    "ProviderBillingExport",
    "ProviderReconciliation",
    "ReconciliationReport",
    "TokenUsage",
    "UsageCostRecord",
    "UsageParseError",
    "compute_exact_cost",
    "grand_total",
    "parse_anthropic_usage",
    "parse_bedrock_usage",
    "parse_google_usage",
    "parse_openai_usage",
    "reconcile_against_export",
    "rollup_by_model",
    "rollup_by_provider",
    "rollup_by_role",
    "rollup_by_use_case",
]
