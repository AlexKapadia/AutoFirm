# B5 / W5 — Token-Counting Accuracy: Local Tokenizers vs. Provider-Returned Usage

> Workstream 5 (W5): 100%-accurate cross-model spend/cost accounting.
> Research folder 07 of 07. Primary-sourced (vendor docs).

---

## 1. Citations

| # | Title | Org | Year | URL | Accessed |
| --- | --- | --- | --- | --- | --- |
| A | `tiktoken` — fast BPE tokenizer for OpenAI models | OpenAI | 2026 | https://github.com/openai/tiktoken | 2026-06-17 |
| B | OpenAI Cookbook — "How to count tokens with tiktoken" | OpenAI | 2026 | https://cookbook.openai.com/examples/how_to_count_tokens_with_tiktoken | 2026-06-17 |
| C | Token counting (Claude / Anthropic) | Anthropic | 2026 | https://platform.claude.com/docs/en/docs/build-with-claude/token-counting | 2026-06-17 |
| D | Messages — Count Message Tokens (API ref) | Anthropic | 2026 | https://platform.claude.com/docs/en/api/messages-count-tokens | 2026-06-17 |

---

## 2. GRADE

- **tiktoken (OpenAI) = VENDOR PRIMARY, HIGH** for what it does (text BPE encoding) and, by its own scope, for what it does **not** do (chat overhead, tools, images, reasoning).
- **Anthropic token-counting docs = VENDOR PRIMARY, HIGH** — explicitly states the count is an **estimate** and that billing reflects actual API usage.
- **Conclusion (provider-returned usage = source of truth) = HIGH confidence**, drawn directly from both vendors' own wording.

---

## 3. Faithful structured summary

### 3.1 tiktoken — what it counts (and what it does NOT)

- tiktoken is "a fast BPE (Byte Pair Encoding) tokenizer for OpenAI's models." It encodes **text** to token IDs and back: *"It's reversible and lossless, so you can convert tokens back into the original text."*
- Encodings include **`cl100k_base`** (GPT-3.5/4 era) and **`o200k_base`** (GPT-4o era); the right one is selected per model via `tiktoken.encoding_for_model(...)`.
- **Scope limit (verbatim sense):** tiktoken counts **only the encoding of raw text**. The README and the OpenAI Cookbook warn that chat-completion APIs add **"message formatting overhead"** (per-message and per-role special tokens, e.g. `<|im_start|>`/`<|im_end|>` and the priming tokens) that must be added **on top** of the raw text count.
- tiktoken does **NOT** count: **tool / function-call schema tokens**, **image tokens**, or **reasoning/thinking tokens**. Those are computed server-side by the model and are invisible to a pure text tokenizer.

> Implication: a naive `len(enc.encode(text))` undercounts a real chat request — it misses chat-template wrapping, the system prompt's framing, every tool's JSON schema, image tiles, and any hidden reasoning tokens.

### 3.2 Anthropic — NO public local tokenizer; count via API; it is an ESTIMATE

- **There is no public, offline local tokenizer for Claude 3+ / Claude 4+.** Anthropic does not ship a `tiktoken`-equivalent. The only way to obtain a count is the **`POST /v1/messages/count_tokens`** endpoint (or the `usage` object returned by an actual `messages` call).
- The count-tokens endpoint **"accepts the same structured list of inputs for creating a message, including support for system prompts, tools, images, and PDFs"** — i.e. it accounts for the full request shape, not just text.
- **Explicit estimate disclaimer (verbatim):** *"The token count should be considered an **estimate**. In some cases, the actual number of input tokens used when creating a message may differ by a small amount."* And: *"Token counts may include tokens added automatically by Anthropic for system optimizations. **You are not billed for system-added tokens. Billing reflects only your content.**"*
- count_tokens does **not** use prompt caching: *"token counting provides an estimate without using caching logic … prompt caching only occurs during actual message creation."* → so even Anthropic's own pre-call estimate cannot reflect cache-hit billing.
- Returned counts live in the **`usage`** object of a real message: `input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens` — these are the billed quantities.

### 3.3 The quantified ERROR story (why local estimates diverge from the bill)

Sources of divergence between a local estimate and provider-billed usage:

1. **Chat-template / role-framing tokens.** Every message is wrapped with special/priming tokens; OpenAI's own cookbook shows you must add a fixed per-message + per-name + priming overhead that raw `encode()` omits.
2. **System-prompt wrapping.** The system prompt is re-framed server-side; its effective token cost ≠ the raw text length.
3. **Tool / function schemas.** Tool definitions are serialized and counted server-side; a text tokenizer never sees them. (Anthropic's own docs show a tools example jumping a 14-token text request to **403 input tokens** once a single `get_weather` tool is added.)
4. **Multimodal (images / PDFs).** Images are billed by tile/resolution, not by any text encoding — e.g. Anthropic's image example counts **1,551** input tokens and a PDF example **2,188**, none of which a text tokenizer can produce.
5. **Hidden reasoning / thinking tokens.** Reasoning tokens are generated server-side and billed, but are not in the input text at all; current-turn thinking **does** count toward input on Claude.
6. **Tokenizer drift across model versions — large.** Anthropic states the **Claude Opus 4.7 tokenizer produces "roughly 30% more tokens than models before Claude Opus 4.7 for the same text"**, and warns: *"don't reuse token counts measured on a model before Claude Opus 4.7 to estimate costs."* A stale local tokenizer can therefore be **~30% wrong** on identical text.
7. **System-added optimization tokens** that Anthropic counts in the estimate but does **not** bill — the estimate can even over-count vs. the bill.

Net: local estimates can be off by anywhere from a few tokens (text-only) to **tens of percent** (tools/images/reasoning/version drift) — far outside a 100%-accurate-billing tolerance.

---

## 4. Conclusion (binding for W5)

- **Provider-returned usage MUST be the source of truth for billing.** Use the API response `usage` object (OpenAI `usage`, Anthropic `usage` with `input_tokens`/`output_tokens`/`cache_*_input_tokens`, or an aggregator's authoritative counts e.g. OpenRouter `native_tokens_*` — folder 06).
- **Local tokenizers (tiktoken) and the Anthropic count_tokens API are ESTIMATE-ONLY** — valid for **pre-call budgeting** (context-window fit, rate-limit / cost forecasting, model routing) but **NEVER** for charging money or for the audited cost record.
- This is the same principle as folder 05's `cost_source`: a cost computed from a local token estimate is at best `estimate_only` and must never be persisted as the authoritative spend figure.

---

## 5. Best parts to take → mapped to W5

1. **Two-tier token accounting.**
   - `token_source = provider_reported` → from the live API `usage`/`native_tokens_*`; the ONLY input to billing.
   - `token_source = local_estimate` → tiktoken / count_tokens; tagged estimate-only, used solely for pre-call budgeting and routing.
2. **Never bill from a local estimate.** W5's cost engine accepts billed cost only when token counts carry `token_source = provider_reported`; otherwise the record is flagged `estimate_only` and excluded from authoritative spend.
3. **Pin the tokenizer/encoding version when estimating.** Because of the ~30% Opus-4.7 tokenizer jump, any local estimate must record which encoding/model it used; never reuse counts across tokenizer generations.
4. **Account cache + reasoning buckets from provider usage**, not from text — only the API knows `cache_read_input_tokens` / reasoning tokens.
5. **Reconciliation as a quality gate.** Diff local pre-call estimate vs. provider-reported actual and surface large gaps (a signal of mis-modeled tools/images/reasoning), but **always settle on the provider-reported number** for the ledger.

---

## 6. RED flags

- **tiktoken (and any text tokenizer) UNDERCOUNTS** chat-template overhead, tool-schema tokens, image tokens, and reasoning tokens → **never bill from it.**
- **Anthropic has NO public offline tokenizer** for Claude 3+/4+; count_tokens is API-only and **self-declared an estimate** that excludes caching logic.
- **Tokenizer version drift is large** (~30% more tokens on Claude Opus 4.7 vs. earlier) — a stale local estimator is materially wrong; provider usage is immune to this since it reflects the actual model's tokenizer.
- Provider counts may include **system-added tokens** in an estimate that are **not billed** — only the real `usage` from a completed call (or an aggregator's authoritative cost) is the true ledger entry.
