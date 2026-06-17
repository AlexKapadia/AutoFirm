# B5 / W5 — Google Gemini API + Vertex AI: Pricing & Usage Reporting

> **Workstream:** W5 — 100%-accurate cross-model spend/cost accounting.
> **Source family:** Google (Gemini Developer API / AI Studio + Vertex AI / Agent Platform).
> **Bar:** institution-grade. Prices are reproduced **verbatim** from primary vendor docs; mechanics (field names, tiering structure) are durable, prices are volatile and **must be snapshotted-and-frozen** (see GRADE).

---

## 1. Citations (primary vendor docs)

| # | Exact page title | Publisher | Year | URL | Accessed |
|---|---|---|---|---|---|
| C1 | *Gemini Developer API Pricing* | Google | 2026 | https://ai.google.dev/gemini-api/docs/pricing | 2026-06-17 |
| C2 | *Vertex AI / Generative AI pricing* (Agent Platform pricing) | Google | 2026 | https://cloud.google.com/vertex-ai/generative-ai/pricing | 2026-06-17 |
| C3 | *Method: models.generateContent* — `GenerateContentResponse` / `UsageMetadata` | Google | 2026 | https://ai.google.dev/api/generate-content | 2026-06-17 |
| C4 | *Context caching* (Gemini API) | Google | 2026 | https://ai.google.dev/gemini-api/docs/caching | 2026-06-17 |

> The API **does not return a cost/dollar figure** — only token counts in `usageMetadata` (confirmed C3). Cost is always computed downstream by W5.

---

## 2. Faithful structured summary

### 2.1 Gemini Developer API (AI Studio) prices — verbatim (C1)

All prices **per 1,000,000 tokens (per 1M / per MTok)**. **Standard tier** unless noted.

**Gemini 2.5 Pro** — TIERED by prompt size at the **200k-token** boundary:
```
Input            : $1.25   (prompts <= 200k tokens)  | $2.50   (prompts > 200k tokens)
Output           : $10.00  (prompts <= 200k tokens)  | $15.00  (prompts > 200k)   [includes thinking tokens]
Context caching  : $0.125  (prompts <= 200k tokens)  | $0.25   (prompts > 200k)
Cache storage    : $4.50 / 1,000,000 tokens per hour (storage price)
-- Batch tier --
Input            : $0.625  (<= 200k) | $1.25 (> 200k)
Output           : $5.00   (<= 200k) | $7.50 (> 200k)
```

**Gemini 2.5 Flash** — input is NOT tiered by prompt size; split by modality:
```
Input            : $0.30 (text / image / video)  | $1.00 (audio)
Output           : $2.50                          [includes thinking tokens]
Context caching  : $0.03 (text / image / video)  | $0.10 (audio)
Cache storage    : $1.00 / 1,000,000 tokens per hour
-- Batch tier --
Input            : $0.15 (text / image / video)  | $0.50 (audio)
Output           : $1.25
```

**Gemini 2.5 Flash-Lite**:
```
Input            : $0.10 (text / image / video)  | $0.30 (audio)
Output           : $0.40
Context caching  : $0.01 (text / image / video)  | $0.03 (audio)
Cache storage    : $1.00 / 1,000,000 tokens per hour
-- Batch tier --
Input            : $0.05 (text / image / video)  | $0.15 (audio)
Output           : $0.20
```

**Gemini 2.0 Flash**:
```
Input            : $0.10 (text / image / video)  | $0.70 (audio)
Output           : $0.40
Context caching  : $0.025 / 1M tokens (text/image/video) | $0.175 / 1M tokens (audio)
Cache storage    : $1.00 / 1,000,000 tokens per hour
-- Batch tier --
Input            : $0.05 (text / image / video)  | $0.35 (audio)
Output           : $0.20
```

> **Note (C1):** "Thinking tokens are included in output pricing across all models." There is no separate per-token thinking SKU — reasoning/thinking tokens are billed **as output tokens**.

### 2.2 Vertex AI / Agent Platform prices — verbatim (C2)

Per 1M tokens. Vertex exposes additional **Priority** and **Flex/Batch** tiers. The **tiering by 200k prompt size** is identical for **2.5 Pro**; **Flash / Flash-Lite input is flat across the 200k boundary** (the `<=200K` and `>200K` columns carry the same value).

**Gemini 2.5 Pro (Vertex):**
```
Standard  Input  : $1.25 (<=200K) | $2.50 (>200K)
Standard  Output : $10   (<=200K) | $15   (>200K)   ("text, response and reasoning")
Standard  Cached : $0.13 (<=200K) | $0.25 (>200K)
Priority  Input  : $2.25 (<=200K) | $4.50 (>200K)
Priority  Output : $18   (<=200K) | $27   (>200K)
Priority  Cached : $0.23 (<=200K) | $0.45 (>200K)
Flex/Batch Input : $0.625(<=200K) | $1.25 (>200K)
Flex/Batch Output: $5    (<=200K) | $7.5  (>200K)
```

**Gemini 2.5 Flash (Vertex):**
```
Standard  Input  : $0.30 (text/image/video, both tiers) | $1 (audio, both tiers)
Standard  Output : $2.50
Standard  Cached : $0.03 (text/image/video) | $0.10 (audio)
Priority  Input  : $0.54 (text/image/video) | $1.80 (audio)
Priority  Output : $4.50
Priority  Cached : $0.05 (text/image/video) | $0.18 (audio)
Flex/Batch Input : $0.15 (text/image/video) | $0.50 (audio)
Flex/Batch Output: $1.25
```

**Gemini 2.5 Flash-Lite (Vertex):**
```
Standard  Input  : $0.10 (text/image/video) | $0.30 (audio)
Standard  Output : $0.40
Standard  Cached : $0.01 (text/image/video) | $0.03 (audio)
Priority  Input  : $0.18 (text/image/video) | $0.54 (audio)
Priority  Output : $0.72
Priority  Cached : $0.02 (text/image/video) | $0.05 (audio)
Flex/Batch Input : $0.05 (text/image/video) | $0.15 (audio)
Flex/Batch Output: $0.20
```

> **`unverified`:** The Vertex page render (C2) did **not** surface per-hour cache **storage** cost explicitly; it showed only cached-input retrieval rates. Treat Vertex cache-storage cost as **unverified** and snapshot from C2 directly per model before relying on it. C1 (AI Studio) explicitly states `$4.50/1M/hr` (Pro) and `$1.00/1M/hr` (Flash family).

### 2.3 `usageMetadata` field names — verbatim (C3)

Returned in `GenerateContentResponse.usageMetadata`. **Token counts only — no cost field.**
```
promptTokenCount        : "Number of tokens in the prompt. When cachedContent is set, this is
                           still the total effective prompt size meaning this includes the number
                           of tokens in the cached content."
cachedContentTokenCount : "Number of tokens in the cached part of the prompt (the cached content)"
candidatesTokenCount    : "Total number of tokens across all the generated response candidates."
toolUsePromptTokenCount : "Output only. Number of tokens present in tool-use prompt(s)."
thoughtsTokenCount      : "Output only. Number of tokens of thoughts for thinking models."
totalTokenCount         : "Total token count for the generation request
                           (prompt + thoughts + response candidates)."
```
Modality breakdown arrays also present: `promptTokensDetails[]`, `cacheTokensDetails[]`,
`candidatesTokensDetails[]`, `toolUsePromptTokensDetails[]`, plus `serviceTier` (enum).

> **Critical accounting relationships (from the verbatim descriptions):**
> - `promptTokenCount` **includes** `cachedContentTokenCount` (cached tokens are inside the prompt count, not additive). To bill correctly: **billable-fresh-input = `promptTokenCount` − `cachedContentTokenCount`** at the input rate, and `cachedContentTokenCount` at the (discounted) cached rate. Naively billing `promptTokenCount` at the full input rate **double-charges** the cached portion.
> - `thoughtsTokenCount` is **separate** from `candidatesTokenCount` but is **billed as output**. Output billing base = `candidatesTokenCount + thoughtsTokenCount` (consistent with `totalTokenCount = prompt + thoughts + response candidates`).
> - `toolUsePromptTokenCount` is an additional input-side count for tool-use prompts.

### 2.4 Context caching billing (C4)
> "Cache token count: The number of input tokens cached, billed at a reduced rate when included in subsequent prompts."
> "Storage duration: The amount of time cached tokens are stored (TTL), billed based on the TTL duration of cached token count."
> "Other charges apply, such as for non-cached input tokens and output tokens."
> "The number of cached tokens is returned in the `usage_metadata` from the create, get, and list operations of the cache service, and also in `GenerateContent` when using the cache."

Two cost components per cache: (a) **per-token discounted read** of `cachedContentTokenCount`, and (b) **storage** = `cachedContentTokenCount × storage_rate_per_1M_per_hour × TTL_hours`. C4 itself carries **no numbers** (defers to C1); take rates from §2.1.

### 2.5 Vertex vs AI Studio (Gemini Developer API) billing differences
- **Billing surface:** AI Studio bills via the Gemini Developer API account; **Vertex bills through Google Cloud billing** (appears on the GCP invoice / Cloud Billing reports), and exposes extra service tiers (**Priority**, **Flex/Batch**) not all present on the AI Studio page.
- **Per-token rates for the same tier (Standard) match** for 2.5 Pro/Flash/Flash-Lite (C1 vs C2), with one rounding artifact: AI Studio prints Pro cached input as `$0.125`, Vertex prints `$0.13` — **treat as the same SKU; snapshot per surface to be exact.**
- **Neither surface returns a cost number in the API response** — both return only `usageMetadata` token counts; cost is computed downstream (AI Studio) or aggregated by Cloud Billing (Vertex).

---

## 3. GRADE

```
Mechanics (field names, tiering structure, cache model, "no cost in response"):
    PRIMARY vendor docs --> HIGH confidence. Stable across versions.
Prices (all $ figures, the 200k thresholds' associated rates):
    MODERATE confidence --> VOLATILE. Snapshot-and-freeze with a version stamp + accessed date.
    Re-fetch C1/C2 on every price-map version bump; never hardcode a price without a frozen,
    dated snapshot row. Pro cached-input rounding ($0.125 vs $0.13) shows surfaces drift.
```

---

## 4. Best parts to take → W5 design

1. **Exact cost = f(provider-returned usage, versioned frozen price snapshot).**
   `cost = Decimal(price_per_1M_for_tier_and_modality) / Decimal(1_000_000) * Decimal(token_count)`.
   Use `decimal.Decimal` end-to-end; never float. Sum components per category, then round once at report time.

2. **`cost_source` provenance:** Gemini/Vertex are always `price_map_computed` (the API returns no cost). Tag every cost row so reconciliation can distinguish `provider_reported` (none here) vs `price_map_computed`.

3. **Decompose the usage object correctly (do NOT bill `promptTokenCount` flat):**
   ```
   fresh_input_tokens  = promptTokenCount - cachedContentTokenCount   # never negative
   cached_input_tokens = cachedContentTokenCount
   output_tokens       = candidatesTokenCount + thoughtsTokenCount    # thinking billed as output
   tool_input_tokens   = toolUsePromptTokenCount                      # input-side
   cost = fresh_input*input_rate + cached_input*cached_rate
        + output_tokens*output_rate + tool_input_tokens*input_rate
        + (cachedContentTokenCount * storage_rate_per_1M_per_hr * ttl_hours)
   ```

4. **RED — tiered-pricing-by-prompt-size quirk (Gemini):** for **2.5 Pro** the input/output/cached rates **jump** when the prompt exceeds **200,000 tokens** (e.g. input $1.25→$2.50, output $10→$15). The selector key is **prompt size**, not the per-call token count. W5 MUST branch the rate on `promptTokenCount > 200_000` per model. Flash / Flash-Lite are flat across 200k today — but the price map MUST still carry a `tier_threshold` field so a future flat→tiered change is data-only, not code.

5. **Modality matters:** input rates differ for `audio` vs `text/image/video` on Flash/Flash-Lite/2.0. The price map key is `(model, tier, modality, prompt_size_band)`. Use `promptTokensDetails[]` modality breakdown to attribute correctly.

6. **Service tier:** persist `serviceTier` from `usageMetadata` and the request tier (Standard/Priority/Flex/Batch) — the rate set differs materially (Vertex Priority output is ~1.8× Standard).

7. **Snapshot discipline:** freeze a dated price-map version (id + accessed date + source URL); compute historical costs against the snapshot in force at invocation time, never "latest".
