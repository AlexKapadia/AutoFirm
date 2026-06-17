# OpenRouter — Hosted OpenAI-Compatible Multi-Provider Gateway

**Workstream:** B1 multi-model-egress — candidate egress gateway
**Scope:** OpenAI-compatible API, model discovery + pricing, provider routing & automatic failover, and —
critically for **W5** — exactly what usage/cost telemetry OpenRouter returns, **whether per-request cost is
in the response inline or needs the `/generation` follow-up call**, and what cost unit it reports.

> Note: OpenRouter is a **hosted** gateway (not self-hostable). It is included because the prompt scopes
> "self-hostable OpenAI-compatible gateway architectures (LiteLLM proxy + OpenRouter)" and OpenRouter is the
> reference for **provider-authoritative** cost telemetry — the contrast that decides W5 exactness.

---

## 1. Citations / URLs

- **Usage Accounting** — <https://openrouter.ai/docs/use-cases/usage-accounting>
  and cookbook mirror <https://openrouter.ai/docs/cookbook/administration/usage-accounting>
- **Get generation metadata** (`GET /api/v1/generation?id=`) —
  <https://openrouter.ai/docs/api/api-reference/generations/get-generation>
- **Provider Routing** — <https://openrouter.ai/docs/guides/routing/provider-selection>
- **Model Fallbacks** — <https://openrouter.ai/docs/guides/routing/model-fallbacks>
- **List models** (`GET /api/v1/models`, with pricing) — <https://openrouter.ai/docs/api/api-reference/models/get-models>
- **API reference overview** — <https://openrouter.ai/docs/api/reference/overview>
- Accessed June 2026.

---

## 2. Faithful structured summary

### 2.1 OpenAI-compatible API
OpenRouter exposes an **OpenAI-compatible** Chat Completions API at base `https://openrouter.ai/api/v1`
(`POST /api/v1/chat/completions`). One API key, one schema, 400+ models across many upstream providers.

### 2.2 Model discovery + pricing
**`GET /api/v1/models`** returns a `data` array; each model carries `id`, `name`, `context_length`,
`architecture`, and a **`pricing`** object. Verbatim: *"All pricing values are in USD per token/request/unit,
and a value of `"0"` indicates the feature is free."* Pricing fields cover prompt and completion (and
request/image where applicable). Query params allow filtering/sorting by price, context length, throughput,
latency, popularity, recency. **Pricing IS included in model discovery** — usable directly by a deterministic
selector for cost-aware routing.

### 2.3 Provider routing & automatic failover
Set a **`provider`** object in the request body to override defaults. Fields (verbatim):
- **`order`** — *"the providers that OpenRouter will prioritize... in this list, and in this order."*
- **`allow_fallbacks`** — e.g. `{"order": ["openai","azure"], "allow_fallbacks": false}` → *"OpenRouter tries
  OpenAI, then Azure, and stops."*
- **`sort`** — `"price"` (prioritise low price, no load-balancing) or `"latency"` (prioritise low latency);
  also accepts an object with `partition` (`"model"` default groups endpoints by model first; `"none"` sorts
  globally across all fallback models).
- Plus (per docs) `require_parameters`, `data_collection`, `only`, `ignore`, quantization filters.

**Automatic failover:** *"If the first model returns an error, OpenRouter will automatically try the next
model in the list. This enables automatic failover when providers experience issues."* Model-level fallback
list + provider-level `order` give two layers of failover handled server-side by OpenRouter.

### 2.4 USAGE / COST TELEMETRY — the W5-critical detail

**Cost is provider/usage-derived and returned INLINE — no follow-up call needed.** Verbatim:
*"OpenRouter provides built-in Usage Accounting that allows you to track AI model usage **without making
additional API calls**, providing detailed information about token counts, costs, and caching status
**directly in your API responses**."* And: *"The `usage:{include:true}` and
`stream_options:{include_usage:true}` parameters are deprecated and have no effect. Full usage details are
now always included automatically in every response."* (For streaming, usage is in the **last SSE message**.)

Token counts are **native** (model's own tokenizer): *"credit usage and model pricing are based on these
native token counts."*

**Inline `usage` object (verbatim fields):**

| Field | Meaning |
| --- | --- |
| `prompt_tokens` | input tokens (native) |
| `completion_tokens` | output tokens (native) |
| `total_tokens` | sum |
| **`cost`** | charge for the request, **in credits** (OpenRouter's billed unit) |
| `cost_details.upstream_inference_cost` | what the upstream provider charged (BYOK; else 0/null) |
| `prompt_tokens_details.cached_tokens` | tokens read from cache |
| `completion_tokens_details.reasoning_tokens` | reasoning tokens |

**Optional follow-up — `GET /api/v1/generation?id=<id>`** (audit / async): returns `total_cost`, `usage`,
`upstream_inference_cost`, `cache_discount`, `tokens_prompt`, `tokens_completion`, `native_tokens_prompt`,
`native_tokens_completion`, `native_tokens_cached`, `native_tokens_reasoning`, `latency`, `generation_time`,
`moderation_latency`, `finish_reason`, `native_finish_reason`, `provider_name`, `provider_responses`,
`is_byok`, `streamed`, `model`, `api_type`. **This call is OPTIONAL** — for historical auditing or async
fetch — because the same cost/usage is already inline.

| What | Where | Cost included? | Follow-up needed? | Unit |
| --- | --- | --- | --- | --- |
| Per-request cost | inline `usage.cost` (every response, incl. last SSE chunk) | **Yes** | **No** | credits |
| Native token counts | inline `usage.prompt_tokens` / `completion_tokens` | Yes | No | tokens |
| Authoritative billed cost + provider/timing detail | `GET /api/v1/generation?id=` | Yes (`total_cost`) | Optional (audit) | credits |
| Upstream provider's raw cost | `cost_details.upstream_inference_cost` / `upstream_inference_cost` | BYOK only; else **0/null** | inline + on generation | credits/USD |

**Unit caveat (W5):** inline `usage.cost` and `total_cost` are in **OpenRouter credits**. Per-token
`/api/v1/models` pricing is in **USD per token**. AutoFirm must record the **credit→USD convention** to keep
cost attribution exact and reconcilable.

---

## 3. Best parts to take → AutoFirm

- **OpenRouter is the gold standard for in-band, provider-authoritative cost (W5).** Per-request `cost` (and
  `total_cost`) reflect what OpenRouter **actually billed**, on **native** token counts — not a re-derived
  estimate — and arrive **inline on the same response, with no follow-up call.** This is exactly the
  cost-attribution-to-the-unit W5 needs.
- **W1 cost-aware selection:** `GET /api/v1/models` pricing (USD/token, `"0"`=free) feeds AutoFirm's
  **deterministic selection policy** directly; `provider.order` + `allow_fallbacks` + `sort:"price"` provide
  server-side failover/cost-routing that the deterministic layer can drive explicitly (set `order` from
  AutoFirm's own decision rather than trusting OpenRouter's default load-balancing — keeps routing
  deterministic and auditable).
- **Reconciliation anchor:** even if AutoFirm self-hosts LiteLLM as the primary egress, OpenRouter's
  inline `cost`/`total_cost` is a **provider-authoritative ground-truth** to validate LiteLLM's price-map
  estimates against (close the W5 exactness gap noted in the LiteLLM folder).

---

## 4. VERDICT — LiteLLM vs OpenRouter for cost-attribution exactness (W5)

| | **LiteLLM Proxy** | **OpenRouter** |
| --- | --- | --- |
| Per-request cost location | **In-band** (`x-litellm-response-cost` header + `_hidden_params["response_cost"]`) | **In-band** (`usage.cost`, every response) |
| Follow-up call needed? | **No** | **No** (optional `/generation` for audit only) |
| Cost source | **Estimated** — tokens × LiteLLM **price map** (`api.litellm.ai`) | **Provider-authoritative** — what OpenRouter actually billed, on **native** tokens |
| Self-hostable? | **Yes** (Docker + Postgres) | No (hosted SaaS) |
| Unit | USD | Credits (per-token pricing in USD) |

**Both deliver per-request cost in-band with no async follow-up.** The decisive difference is **accuracy of
the cost number**: **LiteLLM = estimated (price-map × tokens)**, **OpenRouter = actual billed (native
tokens)**. For "cost exact to the unit," **OpenRouter's inline cost is authoritative; LiteLLM's is only as
exact as its pinned price map.** Recommended architecture: **self-host LiteLLM for the OpenAI-compatible
egress + control/keys/bulkhead**, but treat its cost as an estimate and **reconcile against
provider-authoritative figures** (OpenRouter inline `cost`, or each provider's own billing/usage API) to
keep W5 attribution truly to-the-unit.

### RED FLAGS / telemetry gaps for W5
1. **LiteLLM cost is estimated, not billed.** Risk of drift from the real invoice if the price map is stale
   or the provider tiers/discounts. → Pin & version the price map; reconcile periodically.
2. **Unit mismatch.** OpenRouter cost is in **credits**, its model pricing in **USD/token**; LiteLLM is USD.
   → Store the credit→USD convention explicitly or attribution silently mis-scales.
3. **`upstream_inference_cost` is BYOK-only** on OpenRouter (`0`/null otherwise) — do not rely on it for the
   raw upstream cost on standard (non-BYOK) requests; use `usage.cost` / `total_cost` instead.
4. **Retry double-counting.** Both gateways may retry/fallback internally; ensure cost is attributed per
   *actual billed attempt* (capture per-response cost, not per-logical-request) — ties to the jittered-retry
   discipline in the resilience folder.

### Could-not-verify from primary docs
- Exact JSON nesting of OpenRouter's `cost_details` / `*_details` objects was confirmed by field name via
  the usage-accounting page but not seen as a full verbatim JSON sample (page intermittently 404'd on direct
  fetch; corroborated via OpenRouter site search). Validate against a live response before relying on nesting.
- Whether LiteLLM can be configured to surface a **provider-returned** cost (vs its price-map estimate) for
  providers that return billed cost was not found in primary docs — assume **estimate-only** until verified.
