# B5 — SYNTHESIS: the unified exact-cost model and the provider-quirk matrix

> Cross-source reconciliation of folders 01–10. Owned by the orchestrator (CRO research org).
> Drives the W5 design. Date: 2026-06-17.

## 1. The one invariant that survives every source

**Provider-returned usage is the source of truth for billing; local token estimates are never.**
(folders 02, 03, 07). No mainstream per-request inference API returns a cost number — only
**OpenRouter** does (folder 06), and OpenAI/AWS/Google expose cost only at the **aggregated, delayed,
org/account level** (Costs API, Cost & Usage Report, Cloud Billing). Therefore the per-request cost is
**computed by us** from `(usage, frozen price snapshot)` and labelled `price_map_computed`; the
aggregated provider figure is `provider_reported` and is what we **reconcile against**.

## 2. The unified cost formula (per request, per `(model, surface)`)

All five providers reduce to the same shape, but with **provider-specific token decomposition** that
must NOT be shared code (folders 01–04):

```
cost = Σ_bucket  ( tokens[bucket]  ×  rate[bucket, model, surface, snapshot] )      # all Decimal

buckets (superset; a given provider populates a subset):
  base_input        — uncached prompt tokens
  cache_write_5m    — Anthropic 1.25× base input
  cache_write_1h    — Anthropic 2.00× base input
  cache_write       — Bedrock / generic single write rate
  cache_read        — discounted (Anthropic 0.10×; OpenAI/Gemini per-model cached column)
  base_output       — completion / candidate tokens
  reasoning_output  — billed at OUTPUT rate, see decomposition quirk below
  tiered_uplift     — Gemini: a HIGHER rate above the 200k-prompt boundary
```

**Provider decomposition quirks the formula MUST encode (these are the load-bearing accuracy facts):**

| Provider | Cache tokens vs prompt | Reasoning tokens | Tiering | Unit |
|----------|------------------------|------------------|---------|------|
| Anthropic | `cache_read`/`cache_creation_input_tokens` are **separate** from `input_tokens`; 5m vs 1h split in `cache_creation.{ephemeral_5m,ephemeral_1h}` at **1.25× / 2×**, read **0.1×** | `output_tokens_details.thinking_tokens` (billed as output) | none | per-MTok |
| OpenAI | `prompt_tokens_details.cached_tokens` is a **SUBSET of `prompt_tokens`** → must subtract before pricing base input at a lower cached rate | `completion_tokens_details.reasoning_tokens` is a **SUBSET of `completion_tokens`** (already billed as output — itemize, never add) | none | per-1M |
| Google | `promptTokenCount` **INCLUDES** `cachedContentTokenCount` → subtract or double-charge; output base = `candidatesTokenCount + thoughtsTokenCount` | `thoughtsTokenCount` (billed as output) | **rate steps up above 200k-token prompt** (Pro: in $1.25→$2.50, out $10→$15) | per-1M |
| AWS Bedrock | `inputTokens` **EXCLUDES** cache-read (`cacheReadInputTokens` separate) | (inherits hosted model's behavior) | none | **per-1K historically / per-1M now — store unit explicitly** |
| OpenRouter | native split fields; returns **actual cost** | `native_tokens_reasoning` | (passthrough) | provider-native |

> **The cache-token relationship is inverted between providers** (OpenAI/Google: cached ⊂ prompt;
> Anthropic/Bedrock: cache separate). A single shared "subtract cached from input" rule is WRONG.
> Each provider gets its own decomposition adapter; the *pricing* core is shared, the *parsing* is not.

## 3. Money representation (folders 08, 09)

- **`Decimal` only**, never `float`. Construct from **strings** (`Decimal("0.000003")`), never from a
  float literal (which re-imports the binary error). Per-token rates are tiny (`input_cost_per_token`
  ~ `3e-6`) so precision is mandatory.
- **Default rounding = `ROUND_HALF_EVEN`** (banker's, Python default). Any deviation is explicit and recorded.
- **Defer rounding.** Sum the full-precision per-bucket products, then `.quantize()` to the currency
  minor unit **once** at the ledger boundary — rounding each token-product first loses pennies.
- **Currency minor unit is currency-dependent** (ISO 4217 exponent: USD 2, JPY 0, BHD/KWD 3). Quantize
  to the per-currency exponent; unknown currency **fails closed**.
- **FX:** store `(original_amount, original_currency, fx_rate, fx_rate_source, fx_rate_timestamp,
  converted_amount)` — never the converted figure alone. Allocations use largest-remainder so splits
  sum **exactly** to the total.

## 4. The append-only, tamper-evident ledger (folder 10)

`UsageCostRecord` is appended to an **RFC-6962-style hash-chained log**. Reproduce the formulae EXACTLY
(the `0x00`/`0x01` domain-separation prefixes are mandatory for second-preimage resistance):

```
leaf_hash      = SHA-256( 0x00 || canonical_serialization(record) )
interior_hash  = SHA-256( 0x01 || left_subtree_hash || right_subtree_hash )
```

A simpler linear hash-chain variant (each record stores `prev_hash`, and `this_hash =
SHA-256(prev_hash || canonical(record))`) is the minimum; the RFC-6962 Merkle tree gives efficient
inclusion/consistency proofs. **Corrections are never edits** — a wrong record is superseded by a new
**reversing entry + correct entry** (preserves both audit trail and chain integrity).

The record stores the **raw provider usage object verbatim** plus the **price-snapshot id**
(`model, surface, accessed_date, catalog_sha`), so cost is **independently re-derivable** and any
reconciliation discrepancy can be traced to either a usage-parse bug or a stale price.

## 5. Provenance model (`cost_source`)

```
cost_source = provider_reported   # cost taken from provider (OpenRouter per-request; OpenAI Costs API,
                                  #   AWS CUR, GCP Billing at the aggregated/reconciliation layer)
            | price_map_computed   # cost we computed from usage × frozen price snapshot (default path
                                  #   for Anthropic / OpenAI / Google / Bedrock per-request)

token_source = provider_reported  # from the response usage object (REQUIRED for billing)
             | local_estimate      # tiktoken/heuristic — pre-call budgeting ONLY, flagged estimate_only,
                                   #   NEVER written to a billable UsageCostRecord
```

## 6. Reconciliation loop (the acceptance signal)

```
for each (provider, period):
    ledger_total   = Σ price_map_computed cost over UsageCostRecords in period   # ours
    provider_total = provider_reported export (Costs API / CUR / Billing / OpenRouter)
    drift          = ledger_total − provider_total
    assert drift == 0   (to the currency minor unit)      # zero-drift target
    # nonzero drift => open an investigation entry; resolve via reversing entries, never silent fixes
```

Tolerance may auto-clear sub-cent rounding-artifact differences **only with a logged explanation**; the
**target is exact zero drift** at item and grand-total level.
