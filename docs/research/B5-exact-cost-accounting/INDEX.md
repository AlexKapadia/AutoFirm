# B5 — Exact Cross-Model Cost Accounting (Workstream 5): Research Index

> Research org / CRO deliverable. **Research gates building** (CLAUDE.md §2 CRO, §3.3, §4.6).
> Bar: institution-grade, **zero numerical errors on deterministic money paths** (§3.11).
> Date assembled: **2026-06-17**. PRIMARY-source-first (provider docs + open price catalog) —
> this is an accuracy/engineering problem, not an academic one.

## What W5 must deliver
A cost-accounting subsystem where:
- **Exact `Decimal` cost = f(provider-returned usage, versioned frozen price snapshot)** — never float, never local-tokenizer estimates.
- Every cost row is an **append-only, RFC-6962 hash-chained `UsageCostRecord`** (tamper-evident).
- Each record carries **`cost_source` provenance = `provider_reported | price_map_computed`**.
- The ledger **reconciles to zero drift** against each provider's billing/usage export.

## Sources (one folder per source — §4.6)

| # | Folder | Source (PRIMARY) | One-line takeaway |
|---|--------|------------------|-------------------|
| 01 | `01-anthropic-pricing-and-usage-api` | Anthropic / platform.claude.com docs | Returns **tokens only, no cost**; cache split lives in `cache_creation.{ephemeral_5m,ephemeral_1h}` at 1.25x/2x, read 0.1x; `count_tokens` is a free **estimate**, never bill from it. |
| 02 | `02-openai-pricing-and-usage-api` | OpenAI / developers.openai.com docs | **Reasoning tokens hidden inside `completion_tokens`**; `cached_tokens ⊂ prompt_tokens` at a lower rate; Chat vs Responses field names differ; org **Costs API returns decimal dollars** (reconciliation source). |
| 03 | `03-google-vertex-gemini-pricing-and-usage` | Google / ai.google.dev + cloud.google.com | **Tiered at the 200k-prompt boundary** (Pro input $1.25→$2.50); `promptTokenCount` **includes** `cachedContentTokenCount`; thinking tokens billed as output; no cost returned. |
| 04 | `04-aws-bedrock-pricing-and-usage` | AWS / aws.amazon.com/bedrock + docs.aws | **Per-1K vs per-1M unit trap** (1000x risk); **Provisioned Throughput is time-based not token-based**; `inputTokens` **excludes** cache-read; rates ≠ native; reconcile via CUR. |
| 05 | `05-litellm-price-catalog-and-cost-calc` | LiteLLM `model_prices_and_context_window.json` + docs | Open per-token catalog (2,784 entries) with cache/reasoning/threshold fields; **NO versioning** → must **pin a commit SHA**; per-token not per-1K. |
| 06 | `06-openrouter-usage-accounting` | OpenRouter docs (usage object, `/generation`) | **Returns ACTUAL cost** (`usage.cost`, `/generation.total_cost`) from **native** tokenizer counts → a `provider_reported` source; stores native + normalized counts. |
| 07 | `07-tokenizer-vs-provider-usage-accuracy` | tiktoken repo + Anthropic count_tokens docs | Local tokenizers count raw text only — miss chat/tool/image/reasoning tokens (1 tool: 14→403 tok); **provider usage MUST be source of truth**, local = estimate-only. |
| 08 | `08-decimal-vs-float-for-money` | Python `decimal` docs + General Decimal Arithmetic / IEEE 754 | Float drifts silently (`0.1+0.2≠0.3`); use `Decimal`, default **`ROUND_HALF_EVEN`**, `.quantize` to currency minor unit; pass strings not floats into `Decimal`. |
| 09 | `09-multi-currency-and-money-representation` | ISO 4217 + Fowler Money pattern | Minor-unit precision is **currency-dependent** (USD 2, JPY 0, BHD 3); amount+currency inseparable; FX → store amount+currency+rate+timestamp, largest-remainder allocation. |
| 10 | `10-billing-reconciliation-and-audit-ledger` | RFC 6962 §2.1 + accounting reconciliation practice | Reproduces exact Merkle leaf `SHA-256(0x00‖entry)` / node `SHA-256(0x01‖L‖R)`; reconciliation targets **zero drift**; corrections = **reversing entries, never edits**. |

## Orchestrator-owned synthesis
- **`SYNTHESIS.md`** — cross-source reconciliation: the unified cost formula, the provider-quirk matrix, the provenance model.
- **`accuracy-bar-and-golden-set.md`** — the honest answer to *"is 100% accuracy achievable?"*, the W5 golden-set + metric proposal, and the enumerated provider quirks the design MUST handle.

## GRADE posture
Provider docs and language/standards docs are **PRIMARY/High** for *mechanics and field names*. All **prices are volatile/Moderate** — they are snapshot-and-frozen by `(model, surface, accessed_date)`, never trusted live. The LiteLLM catalog is community-maintained (High schema / Moderate price + staleness) and MUST be SHA-pinned.
