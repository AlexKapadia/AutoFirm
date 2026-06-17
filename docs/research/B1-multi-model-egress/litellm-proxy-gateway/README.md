# LiteLLM Proxy (BerriAI) — Self-Hosted OpenAI-Compatible Gateway

**Workstream:** B1 multi-model-egress — candidate self-hosted gateway
**Scope:** OpenAI-compatible surface, routing/fallbacks, virtual keys, circuit-breaker (cooldown) behaviour,
model discovery, and — critically for **W5** — exactly what usage/cost telemetry LiteLLM returns and logs,
and **whether cost is computed by LiteLLM from a price map or returned by the provider.**

---

## 1. Citations / URLs

- **LiteLLM Proxy docs (BerriAI)** — <https://docs.litellm.ai>
  - Cost tracking: <https://docs.litellm.ai/docs/proxy/cost_tracking>
  - Token usage & `response_cost`: <https://docs.litellm.ai/docs/completion/token_usage>
  - Router (strategies/fallbacks/retries/cooldowns): <https://docs.litellm.ai/docs/routing>
  - Virtual keys: <https://docs.litellm.ai/docs/proxy/virtual_keys>
  - Model cost map (live): `https://api.litellm.ai` / repo `model_prices_and_context_window.json`
- Accessed June 2026. Open-source, Apache-2.0, self-hostable (Docker; requires PostgreSQL via `DATABASE_URL`
  for keys/spend logging).

---

## 2. Faithful structured summary

### 2.1 OpenAI-compatible surface
LiteLLM Proxy exposes an **OpenAI-compatible** API. Primary endpoint: **`POST /chat/completions`**
(and `/v1/chat/completions`). Drop-in: point any OpenAI SDK at the proxy `base_url` with a LiteLLM virtual
key. Also exposes `/embeddings`, `/completions`, etc. The proxy normalises 100+ providers behind the OpenAI
request/response schema.

### 2.2 Model routing & fallbacks
Configured via `router_settings` (proxy `config.yaml`) or the `Router(...)` SDK object.

- **`routing_strategy`** (verbatim options): `"simple-shuffle"` (default, recommended for production),
  `"usage-based-routing-v2"` (lowest TPM), `"latency-based-routing"` (lowest response time),
  `"least-busy"` (fewest concurrent calls), `"cost-based-routing"` (lowest model cost).
- **Fallbacks:** `fallbacks` (model-group → backup model list), **`context_window_fallbacks`** (fall back
  when context exceeded), **`content_policy_fallbacks`** (fall back on content-policy errors).
- **Per-deployment `litellm_params`:** `rpm`, `tpm`, `weight`, `order` (priority tier; lower = higher),
  `max_parallel_requests`, `region_name`, `base_model` (used for **cost tracking** on Azure).
- **Pre-call checks** (`enable_pre_call_checks: true`) filter deployments by context window / region before
  routing.

### 2.3 Retries / timeouts / cooldowns (this IS the circuit-breaker behaviour)
- **`num_retries`** (e.g. 3) with automatic exponential backoff on rate-limit errors; `retry_after`.
- **`timeout`** per request.
- **Cooldown (circuit-breaker):** `allowed_fails` (failures within a minute tolerated) + **`cooldown_time`**
  (seconds a deployment is excluded after exceeding `allowed_fails`). Verbatim: *"Deployment excluded
  temporarily after exceeding `allowed_fails` within a minute."* This is LiteLLM's per-deployment
  open-circuit cooldown — functionally the Open→(timeout)→retry behaviour of §B1 circuit-breaker folder.

### 2.4 Virtual keys
- **`POST /key/generate`** mints keys (`sk-` prefix) with: `models` (allow-list), **`max_budget`** (USD spend
  cap), `duration` (expiry), `user_id` / `team_id`, `rpm_limit`, `tpm_limit`, `max_parallel_requests`,
  `aliases` (model alias map). Manage via `/key/update`, `/key/block`, `/key/unblock`.
- Optional scheduled rotation (`auto_rotate`, `rotation_interval`) when `LITELLM_KEY_ROTATION_ENABLED=true`.
- Requires a master key + PostgreSQL.

### 2.5 Model discovery
- **`GET /v1/models`** — OpenAI-compatible model list.
- **`GET /model/info`** — richer per-model metadata (incl. cost-per-token where configured).

### 2.6 USAGE / COST TELEMETRY — the W5-critical detail

**Cost is computed by LiteLLM from a price map — NOT returned by the provider.** Verbatim:
*"LiteLLM automatically tracks spend for all known models. See our model cost map."* And the cost function
*"combines `token_counter` and `cost_per_token`"*, where `cost_per_token` *"uses the live list from
`api.litellm.ai`"*. So: **LiteLLM counts/echoes the response token usage, then multiplies by its own
per-token price map** (`model_prices_and_context_window.json`). Provider-specific adjustments (Vertex PayGo /
priority pricing, Bedrock service tiers, Azure base-model mapping) are applied when tier metadata is present.

| What | Field / mechanism (verbatim) | Cost included? | Follow-up call? | Unit |
| --- | --- | --- | --- | --- |
| Per-response cost (programmatic) | `response._hidden_params["response_cost"]` — *"LiteLLM returns `response_cost` in all calls."* | **Yes, in-band** | **No** | USD |
| Per-response cost (header) | **`x-litellm-response-cost`** response header — *"Expect to see x-litellm-response-cost in the response headers with calculated cost."* | **Yes, in-band** | **No** | USD |
| Cost helper | `completion_cost(completion_response=...)` returns overall USD cost (`token_counter` × `cost_per_token`) | computed on demand | No | USD |
| Token usage | `response.usage` → `prompt_tokens`, `completion_tokens`, `total_tokens` | Yes, in-band | No | tokens |
| Spend ledger (DB) | `LiteLLM_SpendLogs` table: `api_key` (hashed), `user`, `team_id`, `request_tags`, `end_user`, `model_group`, `api_base`, **`spend`** (USD), `total_tokens`, `completion_tokens`, `prompt_tokens` | Yes (persisted) | No | USD + tokens |
| Per-key/user/team spend | `/key/info` → `"spend"`; `/user/info`; `/team/info` | Yes | No | USD |

**Bottom line for W5:** LiteLLM gives **per-request cost in-band** (both as a response header and as
`_hidden_params["response_cost"]`) on the *same* response — **no async follow-up call needed.** The caveat is
that this cost is **LiteLLM's own estimate** (tokens × LiteLLM price map), **not the provider's authoritative
billed amount**. Exactness therefore depends entirely on LiteLLM's price map matching the provider's real
billing for that model/tier on that date.

---

## 3. Best parts to take → AutoFirm

- **Use LiteLLM Proxy as the self-hosted OpenAI-compatible front door (W1).** `POST /chat/completions` +
  virtual keys (least-privilege, per-tenant `max_budget`/`models`/`rpm`/`tpm`) maps cleanly to AutoFirm's
  security defaults (scoped credentials, deny-by-default, kill-switch via key block).
- **W1 selection:** treat LiteLLM's `routing_strategy` + `fallbacks`/`context_window_fallbacks` +
  `allowed_fails`/`cooldown_time` as the *gateway-level* breaker, and layer AutoFirm's **own deterministic
  selection policy + optional learned router + ensemble-quorum** above it. Don't outsource the must-never-fail
  routing decision to the gateway — keep it deterministic and testable; use the gateway's cooldown as a
  second line of defence.
- **W5 cost-attribution:** capture **`x-litellm-response-cost` header AND `response.usage` tokens on every
  call** and persist to AutoFirm's own append-only audit ledger (don't rely solely on `LiteLLM_SpendLogs`).
- **RED FLAG / W5 exactness gap:** LiteLLM cost is **price-map-derived, not provider-billed** — it is
  *to-the-unit deterministic given the token count and price map*, but can **drift from the provider's actual
  invoice** if the price map is stale or the provider applies tiering/discounts LiteLLM doesn't model. For
  "cost exact to the unit," AutoFirm must (a) pin/version the LiteLLM price map, (b) reconcile against
  provider billing periodically, and (c) prefer **provider-authoritative cost where available**. This is the
  key contrast with OpenRouter — see verdict in the OpenRouter folder.
- **Determinism note:** cost = `tokens × price_map[model]` is a pure deterministic computation → exactly
  unit-testable and reproducible, satisfying §3.11 zero-numerical-error on deterministic paths.
