# B5 / W5 — LiteLLM Open Price Catalog & Cost-Calculation Logic

> Workstream 5 (W5): 100%-accurate cross-model spend/cost accounting.
> Research folder 05 of 07. Primary-sourced.

---

## 1. Citation

| Field | Value |
| --- | --- |
| **Title** | `model_prices_and_context_window.json` — LiteLLM open model price & context-window catalog |
| **Org / Author** | BerriAI / LiteLLM (open-source, community-maintained) |
| **Year** | 2026 (file is continuously updated; no release tag on the file itself) |
| **Primary artifact URL** | https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json |
| **Browse view** | https://github.com/BerriAI/litellm/blob/main/model_prices_and_context_window.json |
| **Cost-calc docs** | https://docs.litellm.ai/docs/completion/token_usage |
| **Auto-sync docs** | https://docs.litellm.ai/docs/proxy/sync_models_github |
| **Add-pricing docs** | https://docs.litellm.ai/docs/provider_registration/add_model_pricing |
| **Date accessed** | 2026-06-17 |
| **Entries in catalog at access** | **2,784** model entries (verified by parsing the fetched file) |

---

## 2. GRADE

- **Catalog as a SCHEMA / artifact source: HIGH.** It is the de-facto community-maintained PRIMARY artifact for cross-provider model metadata; the schema is stable, self-documented (`sample_spec`), and machine-readable.
- **Catalog for PRICE ACCURACY: MODERATE, with staleness risk (see §6 RED flags).** Prices are crowd-sourced via PRs; a given commit can lag a provider's price change, and the file carries **no semver / no version field** — it is a single mutable file on a fast-moving `main`.
- **Cost-calc functions (`completion_cost`/`cost_per_token`): HIGH** as a documented, deterministic reference implementation of `cost = Σ(tokens × per-token-rate)`.

---

## 3. Faithful structured summary

### 3.1 The schema — `sample_spec` (reproduced verbatim)

The first entry in the file is a self-documenting spec describing every legal field:

```json
"sample_spec": {
  "code_interpreter_cost_per_session": 0.0,
  "computer_use_input_cost_per_1k_tokens": 0.0,
  "computer_use_output_cost_per_1k_tokens": 0.0,
  "deprecation_date": "date when the model becomes deprecated in the format YYYY-MM-DD",
  "file_search_cost_per_1k_calls": 0.0,
  "file_search_cost_per_gb_per_day": 0.0,
  "input_cost_per_audio_token": 0.0,
  "input_cost_per_token": 0.0,
  "litellm_provider": "one of https://docs.litellm.ai/docs/providers",
  "max_input_tokens": "max input tokens, if the provider specifies it. if not default to max_tokens",
  "max_output_tokens": "max output tokens, if the provider specifies it. if not default to max_tokens",
  "max_tokens": "LEGACY parameter. set to max_output_tokens if provider specifies it. IF not set to max_input_tokens, if provider specifies it.",
  "mode": "one of: chat, embedding, completion, image_generation, audio_transcription, audio_speech, image_generation, moderation, rerank, search",
  "output_cost_per_reasoning_token": 0.0,
  "output_cost_per_token": 0.0,
  "search_context_cost_per_query": {
    "search_context_size_high": 0.0,
    "search_context_size_low": 0.0,
    "search_context_size_medium": 0.0
  },
  "supported_regions": ["global", "us-west-2", "eu-west-1", "ap-southeast-1", "ap-northeast-1"],
  "supports_audio_input": true,
  "supports_audio_output": true,
  "supports_function_calling": true,
  "supports_parallel_function_calling": true,
  "supports_prompt_caching": true,
  "supports_reasoning": true,
  "supports_response_schema": true,
  "supports_system_messages": true,
  "supports_vision": true,
  "supports_web_search": true,
  "vector_store_cost_per_gb_per_day": 0.0
}
```

### 3.2 Key per-token cost fields (the ones W5 must read)

All costs are **per single token in USD** (NOT per 1K — note `input_cost_per_token: 2.5e-06` means $2.50 / 1M tokens):

| Field | Meaning |
| --- | --- |
| `input_cost_per_token` | USD per input (prompt) token |
| `output_cost_per_token` | USD per output (completion) token |
| `cache_creation_input_token_cost` | USD per token written to prompt cache (Anthropic-style cache write) |
| `cache_read_input_token_cost` | USD per token read from cache (the cheap cache-hit rate) |
| `output_cost_per_reasoning_token` | USD per reasoning/thinking token (when priced separately) |
| `input_cost_per_audio_token` | USD per audio input token |
| `input_cost_per_token_above_128k_tokens` / `_above_200k_tokens` | **tiered** input rate once the request exceeds a context threshold |
| `output_cost_per_token_above_200k_tokens` | tiered output rate above threshold |
| `cache_creation_input_token_cost_above_1hr` | longer-TTL cache-write rate (Anthropic 1-hr cache) |
| `input_cost_per_token_batches` / `output_cost_per_token_batches` | discounted Batch-API rates |
| `input_cost_per_token_priority` / `output_cost_per_token_priority` | priority-tier rates |
| `max_tokens`, `max_input_tokens`, `max_output_tokens` | context-window limits |
| `litellm_provider` | provider key (e.g. `openai`, `anthropic`, `bedrock`) |
| `mode` | `chat` / `embedding` / `completion` / `image_generation` / … |
| `supports_prompt_caching`, `supports_reasoning`, `supports_vision`, `supports_function_calling`, … | capability flags |

> **CRITICAL for exactness:** tiered fields like `*_above_128k_tokens` / `*_above_200k_tokens` mean the per-token rate is **not constant** — a correct cost computation must apply the threshold logic, not a single flat rate. Cache-write vs cache-read are **separately priced** and must be charged against the matching token buckets.

### 3.3 Full example entry — `gpt-4o` (verbatim, litellm_provider `openai`)

```json
"gpt-4o": {
  "cache_read_input_token_cost": 1.25e-06,
  "cache_read_input_token_cost_priority": 2.125e-06,
  "input_cost_per_token": 2.5e-06,
  "input_cost_per_token_batches": 1.25e-06,
  "input_cost_per_token_priority": 4.25e-06,
  "litellm_provider": "openai",
  "max_input_tokens": 128000,
  "max_output_tokens": 16384,
  "max_tokens": 16384,
  "mode": "chat",
  "output_cost_per_token": 1e-05,
  "output_cost_per_token_batches": 5e-06,
  "output_cost_per_token_priority": 1.7e-05,
  "regional_processing_uplift_multiplier_eu": 1.1,
  "regional_processing_uplift_multiplier_us": 1.1,
  "supports_function_calling": true,
  "supports_parallel_function_calling": true,
  "supports_pdf_input": true,
  "supports_prompt_caching": true,
  "supports_response_schema": true,
  "supports_system_messages": true,
  "supports_tool_choice": true,
  "supports_service_tier": true,
  "supports_vision": true
}
```

### 3.4 Full example entry — `claude-3-7-sonnet-20250219` (verbatim, litellm_provider `anthropic`)

```json
"claude-3-7-sonnet-20250219": {
  "cache_creation_input_token_cost": 3.75e-06,
  "cache_creation_input_token_cost_above_1hr": 6e-06,
  "cache_read_input_token_cost": 3e-07,
  "deprecation_date": "2026-02-19",
  "input_cost_per_token": 3e-06,
  "litellm_provider": "anthropic",
  "max_input_tokens": 200000,
  "max_output_tokens": 64000,
  "max_tokens": 64000,
  "mode": "chat",
  "output_cost_per_token": 1.5e-05,
  "search_context_cost_per_query": {
    "search_context_size_high": 0.01,
    "search_context_size_low": 0.01,
    "search_context_size_medium": 0.01
  },
  "supports_assistant_prefill": true,
  "supports_computer_use": true,
  "supports_function_calling": true,
  "supports_pdf_input": true,
  "supports_prompt_caching": true,
  "supports_reasoning": true,
  "supports_response_schema": true,
  "supports_tool_choice": true,
  "supports_vision": true,
  "supports_web_search": true
}
```

> Note the **tiered Bedrock variant** `anthropic.claude-3-5-sonnet-20241022-v2:0` additionally carries `input_cost_per_token_above_200k_tokens`, `output_cost_per_token_above_200k_tokens`, `cache_creation_input_token_cost_above_200k_tokens`, `cache_read_input_token_cost_above_200k_tokens`, `cache_creation_input_token_cost_above_1hr`, and `cache_creation_input_token_cost_above_1hr_above_200k_tokens` — confirming the threshold-tier and cache-TTL dimensions.

### 3.5 Cost-calculation logic (docs.litellm.ai)

- **`cost_per_token(model, prompt_tokens, completion_tokens)`** → returns `(prompt_tokens_cost_usd, completion_tokens_cost_usd)`. It looks the model up in the catalog and multiplies token counts by the per-token rates. (Docs note it can use "the live list from `api.litellm.ai`" — a remote, mutable source: another staleness vector.)
- **`completion_cost(completion_response=...)`** or **`completion_cost(model=..., prompt=..., completion=...)`** → single USD float. Docs: it "combines `token_counter` and `cost_per_token` to return the cost for that query (counting both cost of input and output)." When passed a real response object it reads the response's `usage` token counts (provider-reported); when passed raw strings it **estimates** via a local `token_counter` (estimate-only path — avoid for billing).
- **`litellm.model_cost`** → dict of the whole catalog in memory, e.g. `{'gpt-3.5-turbo': {'max_tokens': 4000, 'input_cost_per_token': 1.5e-06, 'output_cost_per_token': 2e-06}, ...}`. (`get_model_info(model)` returns the same per-model record incl. capability flags — used to know whether cache/reasoning fields apply.)

The formula reduces to:

```
cost_usd = input_tokens            * input_cost_per_token
         + output_tokens           * output_cost_per_token
         + cache_creation_tokens   * cache_creation_input_token_cost
         + cache_read_tokens       * cache_read_input_token_cost
         + reasoning_tokens        * output_cost_per_reasoning_token   (if priced separately)
         [+ tiered overrides when total tokens cross *_above_NNNk_tokens thresholds]
```

---

## 4. Versioning & STALENESS (binding finding)

- The catalog is **one mutable JSON file on a fast-moving `main` branch**. It has **no semantic version, no version field, and no per-entry effective-date** for the price itself (`deprecation_date` is about model lifecycle, not price provenance).
- LiteLLM's own runtime **auto-syncs the file from GitHub `main`** — "automatic sync every 6 hours" (or manual) "without requiring a restart" (per the sync-models-from-GitHub docs). So a long-running process can silently change its price map mid-run.
- Prices are **community PRs** (many observed updating Claude/DeepSeek/etc.), so a given snapshot may lag a real provider price change, and errors are possible until a corrective PR lands.
- **Reproducibility requirement:** to make cost numbers reproducible and auditable, **pin a specific commit SHA** of `model_prices_and_context_window.json` (`raw.githubusercontent.com/BerriAI/litellm/<SHA>/model_prices_and_context_window.json`), never `main`. The docs do not advertise SHA pinning — W5 must impose it.

---

## 5. Best parts to take → mapped to W5

1. **Use the catalog SCHEMA as W5's frozen price-snapshot format.** Adopt the exact field names (`input_cost_per_token`, `output_cost_per_token`, `cache_creation_input_token_cost`, `cache_read_input_token_cost`, `output_cost_per_reasoning_token`, the `*_above_NNNk_tokens` tier fields, `litellm_provider`, `mode`) so W5's price map is a drop-in superset and stays interoperable.
2. **Exact `Decimal` cost = f(provider-reported usage, versioned frozen price snapshot).** Multiply provider-returned token buckets by per-token `Decimal` rates from a **frozen, SHA-pinned** snapshot — never floating-point, never the live `main`. Implement the §3.5 formula including cache buckets, separate reasoning-token pricing, and threshold tiers.
3. **`cost_source` provenance flag.** Record `cost_source = price_map_computed` whenever W5 derives cost from the snapshot (and `provider_reported` when a provider/aggregator hands back an authoritative cost — see folder 06). Cost numbers without provenance are not auditable.
4. **Pin by commit SHA; record the SHA in the audit log.** Each cost record stores the price-snapshot SHA so any number can be recomputed identically later. Disable LiteLLM's 6-hourly auto-sync in any path that must be reproducible.
5. **Treat the catalog as the schema authority, NOT the price oracle.** For institution-grade billing, prefer provider-reported cost where available (folder 06) and reconcile against the catalog-computed figure to catch drift / stale-price errors.

---

## 6. RED flags

- **No versioning / no semver / no per-price effective date** on the catalog; it is a single mutable file on `main`. **Pinning a commit SHA is mandatory** for reproducible billing.
- **Runtime auto-sync every ~6h** can mutate the in-memory price map mid-run — must be disabled on reproducible paths.
- **`cost_per_token` may pull a "live list from api.litellm.ai"** — a second remote mutable source; avoid for audited billing.
- **Prices are crowd-sourced PRs** — possible lag/error vs. the provider's actual rate; never the sole source of truth for money.
- **Per-token, not per-1K** — `2.5e-06` is $2.50/1M tokens; an off-by-1000 unit error is easy and unacceptable on a deterministic path.
