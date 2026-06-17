# B5 / W5 Research — Anthropic Claude API: Pricing + Usage Reporting

> Workstream 5 (W5): 100%-accurate cross-model spend/cost accounting.
> This folder captures the PRIMARY Anthropic documentation needed to compute exact cost
> from provider-returned usage. Prices are volatile — this is a **frozen snapshot**.

---

## 1. Full Citation

| Field | Value |
| --- | --- |
| Page title | "Pricing" — Claude API Docs (Anthropic) |
| Publisher | Anthropic |
| Year | 2026 |
| URL (canonical) | `https://docs.anthropic.com/en/docs/about-claude/pricing` |
| URL (resolved, 301) | `https://platform.claude.com/docs/en/docs/about-claude/pricing` |
| Date accessed | 2026-06-17 |

| Field | Value |
| --- | --- |
| Page title | "Messages" — Claude API Docs (usage object) |
| Publisher | Anthropic |
| Year | 2026 |
| URL (resolved, 301) | `https://platform.claude.com/docs/en/api/messages` |
| Date accessed | 2026-06-17 |

| Field | Value |
| --- | --- |
| Page title | "Token counting" — Claude API Docs |
| Publisher | Anthropic |
| Year | 2026 |
| URL (resolved) | `https://platform.claude.com/docs/en/docs/build-with-claude/token-counting` |
| Endpoint reference | `https://platform.claude.com/docs/en/api/messages-count-tokens` |
| Date accessed | 2026-06-17 |

> NOTE on host migration: `docs.anthropic.com/...` 301-redirects to `platform.claude.com/docs/...`
> as of the access date. Both hosts serve the same primary docs. The pricing page itself
> states: *"For the most current pricing information, visit claude.com/pricing."*

---

## 2. Faithful Structured Summary (reproduced EXACTLY)

### 2.1 Model pricing table (verbatim, USD, per MTok = per million tokens)

Columns as published: `Base Input Tokens | 5m Cache Writes | 1h Cache Writes | Cache Hits & Refreshes | Output Tokens`

```
Model                       Base Input   5m Cache Write   1h Cache Write   Cache Hits & Refreshes   Output
--------------------------  ----------   --------------   --------------   ----------------------   ----------
Claude Fable 5              $10  / MTok   $12.50 / MTok    $20    / MTok    $1    / MTok             $50  / MTok
Claude Mythos 5 (ltd)       $10  / MTok   $12.50 / MTok    $20    / MTok    $1    / MTok             $50  / MTok
Claude Opus 4.8             $5   / MTok   $6.25  / MTok    $10    / MTok    $0.50 / MTok             $25  / MTok
Claude Opus 4.7             $5   / MTok   $6.25  / MTok    $10    / MTok    $0.50 / MTok             $25  / MTok
Claude Opus 4.6             $5   / MTok   $6.25  / MTok    $10    / MTok    $0.50 / MTok             $25  / MTok
Claude Opus 4.5             $5   / MTok   $6.25  / MTok    $10    / MTok    $0.50 / MTok             $25  / MTok
Claude Opus 4.1 (deprec.)   $15  / MTok   $18.75 / MTok    $30    / MTok    $1.50 / MTok             $75  / MTok
Claude Opus 4 (retired*)    $15  / MTok   $18.75 / MTok    $30    / MTok    $1.50 / MTok             $75  / MTok
Claude Sonnet 4.6           $3   / MTok   $3.75  / MTok    $6     / MTok    $0.30 / MTok             $15  / MTok
Claude Sonnet 4.5           $3   / MTok   $3.75  / MTok    $6     / MTok    $0.30 / MTok             $15  / MTok
Claude Sonnet 4 (retired*)  $3   / MTok   $3.75  / MTok    $6     / MTok    $0.30 / MTok             $15  / MTok
Claude Haiku 4.5            $1   / MTok   $1.25  / MTok    $2     / MTok    $0.10 / MTok             $5   / MTok
Claude Haiku 3.5 (retired*) $0.80/ MTok   $1     / MTok    $1.60  / MTok    $0.08 / MTok             $4   / MTok
```
\* "retired, except on Bedrock and/or Vertex AI" per the deprecation page.

Verbatim note from page: *"MTok = Million tokens."*

Tokenizer note (verbatim): *"Opus 4.7 and later use a new tokenizer compared to previous
models... This new tokenizer may use up to 35% more tokens for the same fixed text."*
(Token-counting page adds: Fable 5 / Mythos 5 use the Opus-4.7 tokenizer, *"roughly 30% more
tokens than models before Claude Opus 4.7 for the same text"*.)

### 2.2 Prompt caching multipliers (verbatim)

```
Cache operation        Multiplier                  Duration
---------------------  --------------------------  ---------------------------------
5-minute cache write   1.25x base input price      Cache valid for 5 minutes
1-hour cache write     2x base input price         Cache valid for 1 hour
Cache read (hit)       0.1x base input price       Same duration as preceding write
```

Verbatim: *"A cache hit costs 10% of the standard input price."*
Verbatim: *"These multipliers stack with other pricing modifiers, including the Batch API
discount and data residency."*

### 2.3 Batch API discount (verbatim)

*"The Batch API allows asynchronous processing of large volumes of requests with a **50%
discount on both input and output tokens**."* (Confirmed against the published batch table,
e.g. Opus 4.8 batch input $2.50/MTok = 50% of $5; batch output $12.50/MTok = 50% of $25.)

### 2.4 Other modifiers that affect exact cost (verbatim)

- **Data residency / `inference_geo`**: For Opus 4.6, Sonnet 4.6, and later, `inference_geo: "us"`
  applies a **1.1x pricing multiplier** on ALL token pricing categories (input, output, cache
  writes, cache reads). `inference_geo: "global"` (default) = standard. The `usage` object
  returns the `inference_geo` field used.
- **Fast mode** (research preview, Opus 4.6/4.7/4.8 only): premium flat per-MTok rates that
  REPLACE base rates (e.g. Opus 4.8 fast = `$10 / MTok` input, `$50 / MTok` output). Caching
  and data-residency multipliers stack on top. Not available with Batch API.
- **Server tools**: Web search billed **$10 per 1,000 searches** (separate from tokens);
  web fetch = no surcharge; code execution = $0.05/hour/container beyond 1,550 free hrs.
- **Cloud platforms** (Bedrock/Vertex) and **Claude Platform on AWS** (Claude Consumption
  Units, $0.01/CCU) bill independently — out of W5 first-party scope but must be flagged.

### 2.5 `usage` object field names — Messages API (verbatim)

The Messages API returns ONLY token counts. Verbatim from docs:
*"Anthropic's API bills and rate-limits by token counts, as tokens represent the underlying
cost to our systems."* **No cost/dollar figure is ever returned in the API response.**

Top-level `usage` fields (verbatim):
```
input_tokens                  (number)
output_tokens                 (number)
cache_creation_input_tokens   (number)   -- total tokens written to cache this request
cache_read_input_tokens       (number)   -- tokens served from cache (priced at 0.1x)
cache_creation                (object)   -- TTL breakdown, see below
output_tokens_details         (object)
server_tool_use               (object)
inference_geo                 (string)
service_tier                  (string)
```

`cache_creation` (object) sub-fields (verbatim) — the 5m vs 1h TTL ephemeral split:
```
ephemeral_5m_input_tokens     (number)   -- tokens used to create the 5-minute cache entry
ephemeral_1h_input_tokens     (number)   -- tokens used to create the 1-hour cache entry
```

`output_tokens_details` (object) sub-field (verbatim):
```
thinking_tokens               (number)   -- tokens generated as internal reasoning
```

`server_tool_use` (object) sub-fields (verbatim):
```
web_fetch_requests            (number)
web_search_requests           (number)
code_execution_requests       (number)   -- appears in code-execution responses
```

Verbatim example response from the Messages docs:
```json
{
  "usage": {
    "input_tokens": 2095,
    "output_tokens": 503,
    "cache_creation_input_tokens": 2051,
    "cache_read_input_tokens": 2051,
    "cache_creation": {
      "ephemeral_5m_input_tokens": 0,
      "ephemeral_1h_input_tokens": 0
    },
    "output_tokens_details": {
      "thinking_tokens": 0
    },
    "server_tool_use": {
      "web_fetch_requests": 2,
      "web_search_requests": 0
    },
    "inference_geo": "inference_geo",
    "service_tier": "standard"
  }
}
```

### 2.6 `/v1/messages/count_tokens` endpoint (verbatim)

Returns a single field:
```json
{ "input_tokens": 14 }
```
Verbatim caveats:
- *"The token count should be considered an **estimate**. In some cases, the actual number of
  input tokens used when creating a message may differ by a small amount."*
- *"Token counts may include tokens added automatically by Anthropic for system optimizations.
  **You are not billed for system-added tokens**. Billing reflects only your content."*
- *"Token counting is **free to use**"* (rate-limited separately from message creation).
- FAQ: *"token counting provides an estimate without using caching logic... prompt caching only
  occurs during actual message creation."*

**Conclusion: `count_tokens` does NOT match billed usage — it is an ESTIMATE of input tokens
only, and is the wrong source for cost accounting. Use the actual `usage` object from the
Messages response.**

---

## 3. GRADE Tier

| Aspect | Confidence | Rationale |
| --- | --- | --- |
| `usage` field names & mechanics | **HIGH** | Primary vendor docs, reproduced verbatim. Field names are stable contract. |
| Caching multipliers (1.25x / 2x / 0.1x) | **HIGH** | Stated explicitly as multipliers on the primary pricing page. |
| Batch 50% discount | **HIGH** | Stated verbatim and cross-checked against published batch table. |
| Exact per-MTok prices | **MODERATE — snapshot & freeze** | Volatile; page itself defers to `claude.com/pricing`. Freeze with `accessed=2026-06-17`. |

---

## 4. "Best parts to take" — mapped to W5 design

**Does Anthropic return a cost number?** NO. The Messages API returns ONLY token counts
(no dollar/cost field). Therefore for Anthropic, `cost_source = price_map_computed` **always**.

**Exact cost formula** (Decimal, never float). For a single Messages response, with prices
drawn from a **versioned frozen price snapshot** keyed by `(model, accessed_date)`:

```
base_in   = price[model].base_input          # $/MTok
out_price = price[model].output              # $/MTok
w5m       = price[model].cache_write_5m       # = 1.25 * base_in
w1h       = price[model].cache_write_1h       # = 2.00 * base_in
read      = price[model].cache_read           # = 0.10 * base_in
geo_mult  = 1.1 if usage.inference_geo == "us" else 1.0   # Opus4.6/Sonnet4.6+ only

cost = ( input_tokens                                   * base_in
       + cache_creation.ephemeral_5m_input_tokens        * w5m
       + cache_creation.ephemeral_1h_input_tokens        * w1h
       + cache_read_input_tokens                          * read
       + output_tokens                                    * out_price
       ) / 1_000_000 * geo_mult
```

CRITICAL field-to-price mapping for the cost formula:
- `input_tokens` → base input price. (This is the UNCACHED input; it does NOT include cache
  reads or cache writes — those are reported separately.)
- `cache_creation.ephemeral_5m_input_tokens` → **5m write = 1.25x base input**.
- `cache_creation.ephemeral_1h_input_tokens` → **1h write = 2x base input**.
- `cache_read_input_tokens` → **read = 0.1x base input**.
- `output_tokens` → output price. `output_tokens_details.thinking_tokens` is a SUBSET of
  `output_tokens` (extended-thinking tokens are already counted in `output_tokens` and billed
  at the output rate — do NOT add them again).
- If Batch API: multiply input AND output components by 0.5 (or use the frozen batch price rows).
- If Fast mode: REPLACE base/output with the fast-mode rates, then apply cache/geo multipliers.

> RED FLAG — `cache_creation_input_tokens` vs `cache_creation.{5m,1h}`: the top-level
> `cache_creation_input_tokens` is the TOTAL cache-write tokens; the `cache_creation` object
> splits it by TTL at DIFFERENT prices (1.25x vs 2x). A naive formula that prices the single
> top-level total at one rate will be WRONG whenever both TTLs are used. The exact-cost path
> MUST read the `ephemeral_5m_input_tokens` / `ephemeral_1h_input_tokens` split.

> RED FLAG — naive token counting: summing only `input_tokens + output_tokens` and applying
> base/output prices ignores cache reads (0.1x) and cache writes (1.25x/2x). For a cache-heavy
> agent workload this overstates input cost by up to 10x on reads and understates writes.

> RED FLAG — `count_tokens` is an ESTIMATE, not billed usage. Never accost on it. Always
> source cost from the response `usage` object.

**Provenance / record design** (feeds the W5 append-only ledger):
- Persist the raw `usage` object verbatim alongside the computed cost — never discard it.
- `cost_source = "price_map_computed"` for every Anthropic record.
- `price_snapshot_version` = the frozen snapshot id (e.g. `anthropic@2026-06-17`).
- Append-only **RFC-6962 hash-chained** `UsageCostRecord`: each record commits to the prior
  record's leaf hash; cost is a Decimal; store `model`, `inference_geo`, `service_tier`,
  batch/fast flags, and every usage sub-field so the cost is independently re-derivable.
