"""Cost-ledger value types: ``TokenUsage``, ``PriceVector``, ``UsageCostRecord``.

What this does
--------------
Defines the three frozen, fail-closed contracts of ``data-contracts.md`` §8:
:class:`TokenUsage` (provider-RETURNED token counts only), :class:`PriceVector`
(the exact per-token ``Decimal`` prices applied, a frozen snapshot), and
:class:`UsageCostRecord` (one immutable, RFC-6962 hash-chained ledger row). The
record's ``record_hash`` is validated at construction against the canonical hash of
its content chained over ``prev_hash`` — so a tampered/forged row cannot be built.

Why it exists / where it sits
-----------------------------
These are the typed shapes the rest of ``costledger`` operates on: the pure
cost computation produces a ``cost`` :class:`Money`; the append-only ledger chains
``UsageCostRecord`` rows; rollups and reconciliation read them. They sit just above
the shared :class:`~autofirm.modelgateway.model_reference.ModelRef` identity and the
:class:`~autofirm.foundation.money.Money` primitive, and reuse the audit package's
RFC-6962 ``leaf_hash`` (never re-implemented). The hashing/serialisation helpers
live in :mod:`cost_record_canonical_hashing` to keep this file single-responsibility.

Security / compliance invariants upheld
---------------------------------------
* **Provider usage is ground truth (research folder 07):** ``TokenUsage`` holds the
  provider-returned counts verbatim; non-negative, fail-closed.
* **Decimal-only prices (folder 08, §3.11):** every ``PriceVector`` rate is a
  ``Decimal``; a negative rate is refused. A ``float`` cannot reach here.
* **Single-currency by construction (folder 09):** ``cost`` is :class:`Money`, which
  carries its own currency; ``unit_prices`` names the same currency.
* **Tamper-evidence (RFC-6962, §8):** ``record_hash`` MUST equal the canonical leaf
  hash chained over ``prev_hash`` — a mismatch is refused at construction.
* **Attribution is bound, not self-declared (threat-model C9):** ``requesting_role_id``
  is carried from the authenticated invocation, recorded for per-role rollups.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from autofirm.audit.rfc6962_hashing import HASH_BYTES
from autofirm.costledger.cost_record_canonical_hashing import compute_cost_record_hash
from autofirm.foundation.money.money_amount import Money
from autofirm.modelgateway.model_reference import ModelRef, UseCaseId
from autofirm.org.org_identifiers import RoleId

__all__ = [
    "CostSource",
    "PriceVector",
    "TokenUsage",
    "UsageCostRecord",
]

# Provenance of the cost NUMBER (data-contracts.md §8 / SYNTHESIS.md §5):
# provider_reported = the provider's own cost figure (PREFERRED when available,
# e.g. OpenRouter usage.cost); price_map_computed = computed from the frozen price
# snapshot (the default per-request path for Anthropic/OpenAI/Google/Bedrock).
CostSource = Literal["provider_reported", "price_map_computed"]


class TokenUsage(BaseModel):
    """Provider-RETURNED token counts only (never a local-tokenizer estimate).

    Each bucket is non-negative; cache and reasoning counts default to 0 (§8). These
    are the counts the cost ledger trusts as ground truth (research folder 07) — the
    gateway echoes the provider's usage object here unchanged.
    """

    model_config = ConfigDict(frozen=True)

    input_tokens: int  # uncached prompt tokens the provider billed as input
    output_tokens: int  # completion/candidate tokens the provider billed as output
    cache_read_tokens: int = 0  # prompt-cache READ tokens (priced separately, §8)
    cache_write_tokens: int = 0  # prompt-cache WRITE tokens (priced separately, §8)
    reasoning_tokens: int = 0  # reasoning/thinking output tokens (priced separately, §8)

    @field_validator(
        "input_tokens",
        "output_tokens",
        "cache_read_tokens",
        "cache_write_tokens",
        "reasoning_tokens",
    )
    @classmethod
    def _non_negative(cls, value: int) -> int:
        # fail-closed: a negative token count is nonsensical usage — refuse it
        # rather than letting it net out a real bucket to a wrong (lower) cost.
        if value < 0:
            raise ValueError("token counts must be >= 0 (provider-returned usage)")
        return value


class PriceVector(BaseModel):
    """The EXACT per-token ``Decimal`` prices applied — a frozen snapshot (§8).

    Every rate is per-token (the LiteLLM catalog is per-token, folder 05) and a
    ``Decimal`` (folder 08). ``currency`` is the ISO-4217 code all five rates share;
    a float rate cannot be constructed and a negative rate is refused (fail-closed).
    The optional tier fields carry the Google >200k-prompt uplift rates (folder 03/05).
    """

    model_config = ConfigDict(frozen=True)

    currency: str  # ISO-4217; the single currency of every rate in this vector
    input_price: Decimal  # per uncached-input token
    output_price: Decimal  # per output token
    cache_read_price: Decimal  # per cache-read token (discounted)
    cache_write_price: Decimal  # per cache-write token
    reasoning_price: Decimal  # per reasoning token (billed at the output rate)
    # Tiered uplift (Google >200k-prompt boundary, folder 03/05). Both None means
    # "no tiering". When set, they REPLACE input_price/output_price for the part of
    # the request whose PROMPT exceeds `tier_threshold_tokens` (boundary-exact).
    tier_threshold_tokens: int | None = None
    input_price_above_threshold: Decimal | None = None
    output_price_above_threshold: Decimal | None = None

    @field_validator(
        "input_price",
        "output_price",
        "cache_read_price",
        "cache_write_price",
        "reasoning_price",
    )
    @classmethod
    def _price_non_negative(cls, value: Decimal) -> Decimal:
        # fail-closed: a negative per-token price would create money on a request —
        # refuse it (and pydantic refuses a non-Decimal, so float never reaches here).
        if value < 0:
            raise ValueError("per-token prices must be >= 0 (Decimal)")
        return value

    @field_validator("input_price_above_threshold", "output_price_above_threshold")
    @classmethod
    def _tier_price_non_negative(cls, value: Decimal | None) -> Decimal | None:
        # fail-closed: an above-threshold tier rate, when present, is still a price.
        if value is not None and value < 0:
            raise ValueError("tier prices must be >= 0 (Decimal)")
        return value

    @model_validator(mode="after")
    def _tier_fields_all_or_none(self) -> PriceVector:
        # fail-closed: tiered pricing is all-or-nothing. A threshold with no rates
        # (or rates with no threshold) is an ambiguous, mis-priceable half-spec —
        # refuse it so a tier can never be silently ignored (folder 03 boundary).
        tier_fields = (
            self.tier_threshold_tokens,
            self.input_price_above_threshold,
            self.output_price_above_threshold,
        )
        if any(f is not None for f in tier_fields) and any(f is None for f in tier_fields):
            raise ValueError(
                "tiered pricing requires ALL of tier_threshold_tokens, "
                "input_price_above_threshold, output_price_above_threshold (or none)"
            )
        if self.tier_threshold_tokens is not None and self.tier_threshold_tokens <= 0:
            raise ValueError("tier_threshold_tokens must be > 0 when set")
        return self


class UsageCostRecord(BaseModel):
    """One immutable, RFC-6962 hash-chained ledger row (data-contracts.md §8).

    Construction is fail-closed: ``record_hash`` MUST equal the canonical leaf hash
    of this row's content chained over ``prev_hash`` (so a forged/edited row cannot
    be built), and the ``cost`` currency MUST match the ``unit_prices`` currency
    (no cross-currency row). Hashes are 32-byte SHA-256 digests stored as bytes.
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    correlation_id: UUID  # joins the invocation + audit trail (§8); refuse if absent
    requesting_role_id: RoleId  # attribution (per-role/team/use-case/company rollups)
    use_case: UseCaseId  # the routing key this spend is attributed to
    served_by: ModelRef  # which model/provider actually answered (failover-aware)
    usage: TokenUsage  # the provider-attested counts
    unit_prices: PriceVector  # the exact prices applied (frozen snapshot)
    cost: Money  # EXACT Decimal via exact_money_arithmetic; == f(usage, unit_prices)
    cost_source: CostSource  # provenance of the cost number (provider vs computed)
    price_catalog_version: str  # SemVer of the price snapshot used (reconcilable)
    recorded_at: datetime  # injected clock (deterministic)
    prev_hash: bytes  # RFC-6962 chain link to the previous row (or genesis)
    record_hash: bytes  # H(canonical(this row)) chained over prev_hash

    @field_validator("prev_hash", "record_hash")
    @classmethod
    def _hash_width(cls, value: bytes) -> bytes:
        # fail-closed: a wrong-width hash is a malformed chain link — refuse rather
        # than chain over garbage (mirrors node_hash / the capabilities event).
        if len(value) != HASH_BYTES:
            raise ValueError(f"hash must be exactly {HASH_BYTES} bytes, got {len(value)}")
        return value

    @model_validator(mode="after")
    def _currency_and_hash_consistent(self) -> UsageCostRecord:
        # fail-closed: the cost currency must equal the price-vector currency, or the
        # row prices one currency and reports another (a silent FX bug, folder 09).
        if self.cost.currency != self.unit_prices.currency:
            raise ValueError(
                f"cost currency {self.cost.currency} != unit_prices currency "
                f"{self.unit_prices.currency} (no cross-currency row)"
            )
        # fail-closed tamper-evidence: the stored record_hash MUST equal the
        # recomputed canonical leaf hash chained over prev_hash. Any edit to any
        # committed field changes the preimage and breaks this equality (§8).
        expected = compute_cost_record_hash(self, prev_hash=self.prev_hash)
        if self.record_hash != expected:
            raise ValueError("record_hash does not match canonical content (tamper-evident)")
        return self
