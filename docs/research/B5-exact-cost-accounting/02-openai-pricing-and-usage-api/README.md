# B5 / W5 Research — OpenAI API: Pricing + Usage Reporting

> Workstream 5 (W5): 100%-accurate cross-model spend/cost accounting.
> This folder captures the PRIMARY OpenAI documentation needed to compute exact cost
> from provider-returned usage. Prices are volatile — this is a **frozen snapshot**.

---

## 1. Full Citation

| Field | Value |
| --- | --- |
| Page title | "Pricing" — OpenAI API |
| Publisher | OpenAI |
| Year | 2026 |
| URL | `https://developers.openai.com/api/docs/pricing` |
| Mirror | `https://openai.com/api/pricing/` (returned HTTP 403 to the fetcher; not relied upon) |
| Date accessed | 2026-06-17 |

| Field | Value |
| --- | --- |
| Page title | "Chat Completions — object" (usage object) — OpenAI API Reference |
| Publisher | OpenAI |
| Year | 2026 |
| URL | `https://developers.openai.com/api/docs/api-reference/chat/object` |
| Note | `https://platform.openai.com/docs/api-reference/chat/object` returned HTTP 403 to the fetcher; the developers.openai.com mirror was used. |
| Date accessed | 2026-06-17 |

| Field | Value |
| --- | --- |
| Page title | "Reasoning models" — OpenAI API |
| Publisher | OpenAI |
| Year | 2026 |
| URL | `https://developers.openai.com/api/docs/guides/reasoning` |
| Date accessed | 2026-06-17 |

| Field | Value |
| --- | --- |
| Page title | "Costs" — OpenAI API Reference (Admin → Organization → Costs) |
| Publisher | OpenAI |
| Year | 2026 |
| URL | `https://developers.openai.com/api/reference/resources/admin/subresources/organization/subresources/usage/methods/costs` |
| Date accessed | 2026-06-17 |

---

## 2. Faithful Structured Summary (reproduced EXACTLY)

### 2.1 Model pricing (verbatim, USD, per 1M tokens)

> IMPORTANT STALENESS FLAG: As of 2026-06-17 the live OpenAI pricing page's **Flagship**
> tier lists `gpt-5.x` models — NOT `gpt-4o` / `o1` / `o3` / `o4-mini`. The legacy
> gpt-4o / o-series names requested in the brief were NOT present in the flagship table on
> the access date (they may exist only on a legacy/expanded page). Figures below are what
> the live page showed. Treat any gpt-4o/o-series number as **unverified / superseded**.

Flagship — Standard pricing:
```
Model           Input        Cached Input   Output
-------------   ----------   ------------   ----------
gpt-5.5         $5.00        $0.50          $30.00
gpt-5.5-pro     $30.00       —              $180.00
gpt-5.4         $2.50        $0.25          $15.00
gpt-5.4-mini    $0.75        $0.075         $4.50
gpt-5.4-nano    $0.20        $0.02          $1.25
gpt-5.4-pro     $30.00       —              $180.00
```

Batch tier (50% discount — see 2.3):
```
Model           Input        Cached Input   Output
-------------   ----------   ------------   ----------
gpt-5.5         $2.50        $0.25          $15.00
gpt-5.4         $1.25        $0.13          $7.50
gpt-5.4-mini    $0.375       $0.0375        $2.25
gpt-5.4-nano    $0.10        $0.01          $0.625
```

Specialized models (as listed):
```
o3-deep-research        $5.00 input    $20.00 output
o4-mini-deep-research   $1.00 input    $4.00  output
computer-use-preview    $1.50 input    $6.00  output
gpt-5.3-codex (Batch)   $1.75 input    $14.00 output
```

Regional-processing uplift (verbatim): *"Regional processing (data residency) endpoints are
charged a 10% uplift for models released on or after March 5, 2026."*

### 2.2 Cached input pricing (confirmed)

Cached prompt tokens are billed at a steep discount, listed as a **separate "Cached Input"
column** per model (not a fixed global multiplier). On the access-date table the cached rate
is **~0.1x of the standard input rate** for the gpt-5.4/5.5 family
(e.g. gpt-5.4: input $2.50 → cached $0.25; gpt-5.5: $5.00 → $0.50; gpt-5.4-mini: $0.75 →
$0.075). The exact cached price MUST be read per-model from the price snapshot — do not assume
a constant multiplier across models or versions.

### 2.3 Batch API discount (verbatim)

The pricing page exposes a **Batch** processing tier; standard rates are halved
(**50% discount**), confirmed by cross-checking the batch rows against standard rows
(e.g. gpt-5.5 standard input $5.00 → batch $2.50; output $30.00 → $15.00).

### 2.4 `usage` object field names — Chat Completions response (verbatim)

The response returns ONLY token counts. **No cost/dollar figure is returned per request.**
Docs label it: *"Usage statistics for the completion request"* with no pricing data in the
response schema.

Primary fields (verbatim):
```
prompt_tokens                 (number)
completion_tokens             (number)
total_tokens                  (number)
```

`prompt_tokens_details` (object) sub-fields (verbatim):
```
cached_tokens                 (number)   -- cached portion of prompt_tokens (discounted)
audio_tokens                  (number)
```

`completion_tokens_details` (object) sub-fields (verbatim):
```
reasoning_tokens              (number)
accepted_prediction_tokens    (number)
rejected_prediction_tokens    (number)
audio_tokens                  (number)
```

> API-SURFACE NOTE (critical for a cross-model accountant): the **Chat Completions** API uses
> `prompt_tokens` / `completion_tokens` and `completion_tokens_details.reasoning_tokens`. The
> newer **Responses** API uses `input_tokens` / `output_tokens` and
> `output_tokens_details.reasoning_tokens`. W5 must normalize BOTH shapes.

### 2.5 Reasoning-token billing (verbatim)

From the Reasoning models guide:
*"While reasoning tokens are not visible via the API, they still occupy space in the model's
context window and are **billed as output tokens**."*

Reporting: *"the exact number of reasoning tokens used is visible in the usage object... under
`output_tokens_details`: reasoning_tokens"* (Responses API). On Chat Completions the same count
appears under `completion_tokens_details.reasoning_tokens`.

**Confirmed:** reasoning tokens are billed at the OUTPUT rate and are ALREADY INCLUDED in the
`completion_tokens` (Chat) / `output_tokens` (Responses) total — they are itemized, not added
on top. Do NOT double-count.

### 2.6 Usage API / Costs API (verbatim)

- A **Usage API** and a **Costs API** exist at the **organization/admin** level (dashboard-grade,
  daily granularity) — NOT per-request.
- **Costs API** `GET /v1/organization/costs` returns buckets; each result bucket
  (`"object": "organization.costs.result"`) contains an `amount` object:
  ```json
  { "amount": { "value": 0.06, "currency": "usd" } }
  ```
  Field docstring (verbatim): *"The numeric value of the cost."* `currency` is a lowercase
  ISO-4217 code. Optional grouping: `line_item`, `project_id`, `api_key_id`, `quantity`.
- **The Costs API returns a DECIMAL DOLLAR value (the currency's standard unit), NOT cents.**
  (Earlier internal assumption "cost in cents" is INCORRECT per the live reference — it is a
  decimal `value` + `currency`, e.g. `0.13080438340307526 USD` precision is possible.)
- This org-level cost is authoritative for reconciliation but is aggregated/delayed and cannot
  attribute cost to an individual request in real time.

### 2.7 Per-request response: cost figure?

**NO.** The per-request Chat Completions / Responses `usage` object returns ONLY token counts.
A dollar cost is available only via the separate org-level **Costs API** (delayed, aggregated).

---

## 3. GRADE Tier

| Aspect | Confidence | Rationale |
| --- | --- | --- |
| `usage` field names & mechanics | **HIGH** | Primary vendor reference, reproduced verbatim. |
| Reasoning billed as output, included in completion/output tokens | **HIGH** | Stated verbatim in the Reasoning guide. |
| Cached-input discount exists, per-model | **HIGH** | Separate "Cached Input" column per model on the price page. |
| Batch 50% discount | **HIGH** | Stated tier + cross-checked against published rows. |
| Costs API returns decimal `{value,currency}` | **HIGH** | Quoted from the API reference. |
| Exact per-1M prices | **MODERATE — snapshot & freeze** | Volatile; flagship list shifted to gpt-5.x. Freeze `accessed=2026-06-17`. |
| gpt-4o / o-series specific prices | **UNVERIFIED** | Not present in the flagship table on the access date; treat as superseded. |

---

## 4. "Best parts to take" — mapped to W5 design

**Does OpenAI return a cost number per request?** NO — per-request `usage` is tokens only.
A dollar cost exists ONLY at the org level via the **Costs API** (`amount.value` decimal +
`currency`), which is delayed/aggregated. Therefore:
- Per-request: `cost_source = "price_map_computed"`.
- Org-level reconciliation: `cost_source = "provider_reported"` (Costs API `amount.value`),
  used to RECONCILE the summed computed ledger against the authoritative bill.

**Exact cost formula** (Decimal, never float), prices from a versioned frozen snapshot keyed
by `(model, accessed_date)`, normalizing Chat vs Responses field names:

```
# Normalize: prompt=prompt_tokens|input_tokens ; completion=completion_tokens|output_tokens
# cached    = prompt_tokens_details.cached_tokens  (Chat) | input_tokens_details.cached_tokens (Resp)
# reasoning = completion_tokens_details.reasoning_tokens | output_tokens_details.reasoning_tokens

in_price     = price[model].input          # $/1M
cached_price = price[model].cached_input   # $/1M  (per-model, ~0.1x but read exactly)
out_price    = price[model].output         # $/1M

uncached_prompt = prompt - cached          # cached billed at cached rate, remainder at input rate

cost = ( uncached_prompt * in_price
       + cached          * cached_price
       + completion      * out_price        # reasoning_tokens ALREADY inside `completion`
       ) / 1_000_000
# Batch: use frozen batch rows (≈0.5x). Regional/data-residency: +10% uplift for models
# released on/after 2026-03-05 — gate by model release date in the snapshot.
```

CRITICAL field-to-price mapping:
- `cached_tokens` is a SUBSET of `prompt_tokens` → split prompt into (uncached @ input rate)
  + (cached @ cached rate). Pricing all of `prompt_tokens` at the input rate OVERCHARGES.
- `reasoning_tokens` is a SUBSET of `completion_tokens`/`output_tokens` → it is ALREADY in the
  output total at the output rate. Do NOT add it again.
- `accepted_prediction_tokens` / `rejected_prediction_tokens` (Predicted Outputs) — REJECTED
  predicted tokens are still billed as output tokens; they too are inside the completion total.
- `audio_tokens` (in both detail objects) priced at separate audio rates if audio models used.

> RED FLAG — reasoning tokens hidden inside completion_tokens: a naive accountant that prices
> only the VISIBLE answer text will massively UNDERCOUNT cost on o-series / reasoning models,
> because the (invisible) `reasoning_tokens` are billed at the output rate and are buried in
> `completion_tokens`/`output_tokens`. Always price the FULL completion/output total.

> RED FLAG — cached tokens priced differently: `cached_tokens` ⊂ `prompt_tokens` and is billed
> at the much-lower cached rate (per-model). Pricing the whole prompt at the input rate
> overcharges; the formula MUST subtract cached from prompt and price each at its own rate.

> RED FLAG — Chat vs Responses naming: `prompt_tokens`/`completion_tokens` (Chat) vs
> `input_tokens`/`output_tokens` (Responses); reasoning lives under
> `completion_tokens_details` vs `output_tokens_details`. A formula hard-coded to one API
> shape silently reads 0 (→ free) on the other. Normalize both.

> RED FLAG — Costs API is decimal dollars, NOT cents, and is org-level/aggregated/delayed.
> Use it for end-of-period RECONCILIATION (provider_reported), not for real-time per-request
> attribution. Do not assume cents.

**Provenance / record design** (feeds the W5 append-only ledger):
- Persist the raw `usage` object verbatim + the API surface used (`chat` | `responses`).
- Per request: `cost_source = "price_map_computed"`, `price_snapshot_version = "openai@2026-06-17"`.
- Reconciliation pass: pull Costs API `amount.value`/`currency`, store as a
  `cost_source = "provider_reported"` record and assert |computed_sum − reported| within tolerance.
- Append-only **RFC-6962 hash-chained** `UsageCostRecord`: Decimal cost, hash-chained to prior
  leaf; store model, batch flag, region/release-date, and every usage sub-field so cost is
  independently re-derivable and the ledger is tamper-evident.
