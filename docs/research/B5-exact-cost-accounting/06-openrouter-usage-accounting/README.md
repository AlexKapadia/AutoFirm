# B5 / W5 — OpenRouter Usage Accounting & Generation Endpoint

> Workstream 5 (W5): 100%-accurate cross-model spend/cost accounting.
> Research folder 06 of 07. Primary-sourced (vendor docs).

---

## 1. Citation

| Field | Value |
| --- | --- |
| **Title** | Usage Accounting — Track AI Model Token Usage (OpenRouter) |
| **Org** | OpenRouter |
| **Year** | 2026 |
| **Usage-accounting doc URL** | https://openrouter.ai/docs/cookbook/administration/usage-accounting |
| **Generation-endpoint doc URL** | https://openrouter.ai/docs/api/api-reference/generations/get-generation |
| **API reference overview** | https://openrouter.ai/docs/api/reference/overview |
| **Date accessed** | 2026-06-17 |

---

## 2. GRADE

- **OpenRouter docs = VENDOR PRIMARY, HIGH** for the API contract (field names, behaviour, cost semantics). It is the authoritative source for how OpenRouter bills and reports.
- **As a cost source for W5: HIGH for OpenRouter-routed traffic** — cost is computed by OpenRouter from the upstream provider's **native** token counts, i.e. it is a `provider_reported`-class authoritative number for any call routed through OpenRouter.
- Caveat: this only covers traffic that actually goes through OpenRouter; direct-to-provider traffic is out of scope here (use folder 05 + the provider's own `usage`).

---

## 3. Faithful structured summary

### 3.1 Enabling usage accounting

- **Current behaviour (2026): usage details are now ALWAYS included automatically in every response.** The previously-required request parameters `usage: { include: true }` and `stream_options: { include_usage: true }` are **deprecated and have no effect** — they are retained only for backward compatibility.
- For historical / asynchronous auditing, the response `id` can be passed to `GET /api/v1/generation?id=...` to fetch authoritative stats after the request completes.

### 3.2 The `usage` object on a completion response (field names verbatim)

```json
{
  "completion_tokens": 2,
  "completion_tokens_details": { "reasoning_tokens": 0 },
  "cost": 0.95,
  "cost_details": { "upstream_inference_cost": 19 },
  "prompt_tokens": 194,
  "prompt_tokens_details": {
    "cached_tokens": 0,
    "cache_write_tokens": 100,
    "audio_tokens": 0
  },
  "total_tokens": 196
}
```

Fields:

| Field | Meaning (per docs) |
| --- | --- |
| `prompt_tokens` | input tokens (native tokenizer count) |
| `completion_tokens` | output tokens |
| `total_tokens` | sum |
| `cost` | **"The total amount charged to your account"** — expressed in OpenRouter **credits** |
| `cost_details.upstream_inference_cost` | upstream provider's inference cost; **only populated for BYOK requests**, otherwise `0`/`null` |
| `prompt_tokens_details.cached_tokens` | tokens read from cache |
| `prompt_tokens_details.cache_write_tokens` | tokens written to cache |
| `prompt_tokens_details.audio_tokens` | audio input tokens |
| `completion_tokens_details.reasoning_tokens` | reasoning/thinking tokens in the output |
| `is_byok` | (on generation-stats records) whether the call used Bring-Your-Own-Key |

> **Does OpenRouter return ACTUAL cost per request? YES.** The `cost` field is the actual amount charged for that specific request, returned inline on every response (and again via the generation endpoint). This is a per-request authoritative cost, not an estimate.

### 3.3 `GET /api/v1/generation?id=...` — authoritative async stats

Query the endpoint with the generation `id` to retrieve "generation stats (including token counts and cost) after the request is complete … useful for auditing historical usage or when you need to fetch stats asynchronously."

Response fields (names verbatim from the API reference; example shape below — the literal numeric values are illustrative and marked as such):

```jsonc
// Example response SHAPE (field names authoritative; values illustrative)
{
  "data": {
    "id": "gen-...",
    "model": "<provider/model-slug>",
    "provider_name": "<upstream provider>",
    "total_cost": 0.0015,            // authoritative charge for the generation (credits)
    "usage": 0.0015,                 // usage charged
    "tokens_prompt": 10,             // normalized (GPT-style) prompt tokens
    "tokens_completion": 25,         // normalized completion tokens
    "native_tokens_prompt": 10,      // upstream provider's NATIVE tokenizer prompt count
    "native_tokens_completion": 25,  // native completion count
    "native_tokens_reasoning": 5,    // native reasoning/thinking tokens
    "native_tokens_cached": 3,       // native cached tokens
    "native_tokens_completion_images": 0,
    "num_media_prompt": 1,
    "num_media_completion": 0,
    "is_byok": false,
    "upstream_inference_cost": 0.0012, // BYOK-only upstream cost; else 0/null
    "cache_discount": null,            // how much the response saved via cache
    "origin": "https://openrouter.ai/",
    "streamed": true,
    "generation_time": 1200,
    "finish_reason": "stop",
    "native_finish_reason": "...",
    "latency": 0,
    "created_at": "..."
  }
}
```

Full field inventory returned by the endpoint (verbatim names):
`id`, `request_id`, `session_id`, `upstream_id`; `model`, `provider_name`, `router`, `api_type`; `created_at`, `generation_time`, `latency`, `moderation_latency`; `tokens_prompt`, `tokens_completion`, `native_tokens_prompt`, `native_tokens_completion`, `native_tokens_cached`, `native_tokens_reasoning`, `native_tokens_completion_images`; `num_media_prompt`, `num_media_completion`, `num_input_audio_prompt`, `num_fetches`, `num_search_results`; `total_cost`, `usage`, `upstream_inference_cost`, `cache_discount`; `origin`, `http_referer`, `user_agent`, `external_user`, `app_id`, `preset_id`, `data_region`, `service_tier`, `is_byok`; `finish_reason`, `native_finish_reason`, `streamed`, `cancelled`, `web_search_engine`, `provider_responses`, `response_cache_source_id`.

### 3.4 The accuracy / normalization claim (verbatim)

- **"Token counts are calculated using the model's native tokenizer."** Credit usage and model pricing are based on these **native** token counts — i.e. the upstream provider's own tokenizer, **not** a normalized GPT tokenizer.
- The response carries **both**: `tokens_prompt`/`tokens_completion` (normalized, GPT-style, for cross-model comparison) **and** `native_tokens_*` (the real upstream counts the bill is based on). **Billing follows the `native_tokens_*` figures.**
- "For more precise token accounting, use the `/api/v1/generation` endpoint for precise token accounting using the model's native tokenizer."

### 3.5 Credits & markup model

- `cost` / `total_cost` are denominated in **OpenRouter credits** (the standard unit shown). They represent the amount actually charged to the account.
- For **BYOK** requests, `upstream_inference_cost` exposes the underlying provider's cost separately; for non-BYOK it is `0`/`null` (OpenRouter's charge already bundles inference + its margin). `cache_discount` reports cache savings.

---

## 4. Best parts to take → mapped to W5

1. **OpenRouter is a `provider_reported` cost source.** For any traffic routed through OpenRouter, record `cost_source = provider_reported` and take `cost` / `total_cost` as authoritative — no price-map multiplication needed. This is the cleanest path to 100%-accurate spend on multi-model traffic.
2. **Always store BOTH `native_tokens_*` and `tokens_*`.** Bill from `native_tokens_*` (what the provider/OpenRouter actually counted); keep normalized `tokens_*` only for cross-model analytics. W5's schema should mirror this dual-count design.
3. **Capture the cache + reasoning buckets** (`prompt_tokens_details.cached_tokens`, `cache_write_tokens`, `completion_tokens_details.reasoning_tokens`, `native_tokens_cached`, `native_tokens_reasoning`) so cache and reasoning spend are accounted, not lumped into prompt/completion.
4. **Reconcile, then prefer provider-reported.** Compute the catalog-based figure (folder 05) and diff it against OpenRouter's `cost`; persist the provider-reported number as truth and flag any divergence as a price-map staleness signal.
5. **Use `GET /api/v1/generation?id=...` for the audit trail.** Fetch authoritative per-generation stats asynchronously and write them to W5's append-only audit log keyed by generation `id`. Handle `upstream_inference_cost` being BYOK-only.

---

## 5. RED flags / notes

- `usage:{include:true}` is **deprecated/no-op** in 2026 — do not gate on it; usage is always returned. (If older code relies on toggling it, it will silently still get usage — harmless, but don't treat its absence as "no accounting".)
- `cost` is in **OpenRouter credits**, not necessarily raw USD — pin the credit→USD basis in W5 if mixing with direct-provider USD costs.
- `upstream_inference_cost` is **BYOK-only** (`0`/`null` otherwise) — do not treat a null as "free".
- Example numeric values in the generation-endpoint payload above are **illustrative** (field names are authoritative; exact docs example values were partly unverified at access — marked accordingly).
- Coverage is **OpenRouter-routed traffic only**; direct-to-provider calls need the provider's own `usage` + the folder-05 price map.
