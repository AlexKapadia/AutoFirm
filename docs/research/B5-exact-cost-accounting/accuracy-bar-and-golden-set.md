# W5 — Accuracy Bar & Golden-Set / Metric Proposal

> Workstream 5: 100%-accurate cross-model spend/cost accounting.
> Drafted by the CRO research org from the primary-source research in folders 01–10 + `SYNTHESIS.md`.
> Per CLAUDE.md §3.4 (define golden set + metric **up front**) and §3.11 (**zero numerical errors**).
> Date: 2026-06-17. **Research artifact — research gates building.**

---

## 1. Is "100% accurate" achievable? The honest answer.

**Yes — but only under a precise, defensible definition, and only for the parts we control.**
"100% accurate" is NOT one claim; it decomposes into three layers with different achievability:

### Layer A — Computation exactness (FULLY achievable; the hard bar)
> **Definition:** For a given `(provider-returned usage object, frozen price snapshot)`, the computed
> `Decimal` cost equals the mathematically correct value **exactly, to the currency minor unit**, on
> every input, deterministically, with zero arithmetic/logic error.

This is **100% achievable and is the binding §3.11 bar.** It is pure arithmetic over exact `Decimal`
with a fixed rounding mode (folder 08). A single wrong cent here is **unacceptable**. We own this
completely — there is no external uncertainty. **This is where the "100%" claim is literally true.**

### Layer B — Reconciliation to the provider (achievable as ZERO-DRIFT, with caveats)
> **Definition:** Σ(our `price_map_computed` costs over a period) == the provider's own reported total
> for that period (OpenAI **Costs API**, AWS **CUR/Cost Explorer**, GCP **Cloud Billing**, OpenRouter
> `/generation`), **to the cent, zero drift**.

This is achievable **provided we price every token bucket the provider prices, at the provider's own
rates, with the provider's own usage numbers.** Because providers do **not** return a per-request cost
(except OpenRouter — folder 06), our number is a *reconstruction*. It matches **iff** the price
snapshot is the one the provider actually billed and we model every quirk in §3. Residual,
**legitimately-non-zero** sources (must be isolated and labelled, not hidden):
- **Free-tier credits / promotional grants** — provider invoice nets these out; our raw cost does not.
  Track gross cost + a separate credits ledger; reconcile **gross**, report **net**.
- **Provider-side rounding granularity** — a provider may round per-line then sum, or sum then round;
  sub-cent artifacts must be explained, not silently absorbed.
- **Aggregation lag** — Costs API / CUR are delayed and bucketed; reconcile on **closed** periods only.
- **Price changes mid-period** — a rate that changed must be snapshotted with effective dates.

### Layer C — Truthfulness of the upstream usage numbers (NOT ours to guarantee)
We **trust the provider's usage object** as ground truth (folder 07 proves local re-counting is less
accurate, not more). If a provider mis-reports its own tokens, our ledger faithfully reflects what we
were told and what we'll be billed — that is the *correct* behavior. We do **not** attempt to
"correct" provider usage; we record it verbatim so any later provider correction is auditable.

### The defensible headline claim
> **"Exact to the cent on the computation path (Layer A), and zero-drift reconciled against each
> provider's own billing export on closed periods (Layer B), with all legitimate net-vs-gross
> differences (credits, tiers, rounding policy) explicitly itemized — never silently absorbed."**

We do **NOT** claim to predict an invoice we haven't priced, nor to out-count the provider's tokenizer.
That honesty is itself part of the institution-grade bar.

---

## 2. Provider quirks the design MUST handle (enumerated — none optional)

Each is a documented RED flag from folders 01–07. A naive `tokens × flat_rate` implementation is
**wrong** on every one of these.

1. **Reasoning / thinking tokens** — OpenAI `completion_tokens_details.reasoning_tokens` (⊂
   `completion_tokens`), Google `thoughtsTokenCount`, Anthropic `output_tokens_details.thinking_tokens`,
   OpenRouter `native_tokens_reasoning`. Billed at **output** rate. **Itemize, never double-add.**
   Pricing only visible completion text **massively undercounts** o-series / thinking-model cost.
2. **Prompt-cache tokens — and the inverted subset relationship:**
   - OpenAI `cached_tokens` and Google `cachedContentTokenCount` are **SUBSETS of the prompt count** →
     subtract before pricing base input, then price the cached portion at the (lower) cached rate.
   - Anthropic `cache_read_input_tokens` / `cache_creation_input_tokens` and Bedrock
     `cacheReadInputTokens` are **SEPARATE from** the base input count.
   - Anthropic cache **write** has two TTLs at different prices: 5m = **1.25×**, 1h = **2×** base input;
     read = **0.1×**. The split is in `cache_creation.{ephemeral_5m,ephemeral_1h}`, not the top-level total.
3. **Tiered pricing by prompt size (Google)** — Gemini 2.5 Pro steps from `$1.25→$2.50` input and
   `$10→$15` output **above a 200k-token prompt**. Rate is keyed on **prompt size**, not per-call total.
   Price map must carry threshold fields (LiteLLM `input_cost_per_token_above_200k_tokens`, folder 05).
4. **Per-1K vs per-1M unit (AWS Bedrock)** — historically per-1K, page now per-1M. **Wrong divisor =
   1000× error.** Store an explicit `unit` / `unit_divisor` on every price row.
5. **Provisioned Throughput / time-based billing (Bedrock)** — `$/model-unit/hour`, **not token-based**.
   A separate cost stream (`units × hours × rate`); cannot be derived from tokens. Burndown multipliers
   (e.g. 5× output, Claude 3.7+) are **quota only, not billing** — using them for cost over-states 5×.
6. **Batch / tiered discounts** — 50% off on Anthropic / OpenAI / Bedrock batch; OpenAI **+10%**
   regional-residency uplift; Vertex Priority/Flex tiers. Discount/uplift is a property of the
   `(surface, tier)`, snapshotted with the price.
7. **Bedrock (and any reseller) rates ≠ native provider rates** — same model, different price by
   **surface**. Price map keyed by `(model, surface)`, not model alone.
8. **Chat vs Responses field-name divergence (OpenAI)** — `prompt_tokens/completion_tokens` vs
   `input_tokens/output_tokens`. A hard-coded shape silently reads **0 → "free"**. Normalize both.
9. **Currency minor unit ≠ always 2dp (ISO 4217)** — USD 2, JPY 0, BHD/KWD/OMR 3. Quantize to the
   per-currency exponent; unknown currency fails closed (folder 09).
10. **Float for money = silent drift** — `0.1+0.2≠0.3`; and `Decimal(0.1)` from a float re-imports the
    error. `Decimal` from **strings** only; defer rounding to the ledger boundary (folder 08).
11. **Free-tier credits / promo grants** — net out at the invoice; tracked as a separate ledger so
    reconciliation is gross-vs-gross, reporting net-of-credits.
12. **`count_tokens` / local tokenizers are estimates** — Anthropic states its own count "should be
    considered an estimate" and excludes caching; tiktoken misses chat/tool/image/reasoning tokens
    (one tool: 14→403 tokens). **Never write a local estimate to a billable record** (folder 07).
13. **Catalog staleness (LiteLLM)** — no versioning, mutable single file, ~6h runtime auto-sync.
    **Pin a commit SHA**; disable auto-sync on audited paths (folder 05).

---

## 3. The golden set (defined up front — §3.4)

**100% synthetic and public-data only** (§3.12, §5.5 — no real PII/secrets). The golden set is a
labelled corpus of `(provider, model, surface, raw_usage_object, frozen_price_row) → expected_Decimal_cost`,
where the expected cost is **hand-computed independently** and checked in as the oracle. It must cover
the full quirk matrix in §2:

| Class | Cases (examples) | Asserts |
|-------|------------------|---------|
| **Base happy path** | each provider, input+output only | exact cost to the cent |
| **Cache — separate (Anthropic/Bedrock)** | read-only, 5m write, 1h write, mixed | each TTL at its own multiplier; total = sum |
| **Cache — subset (OpenAI/Google)** | cached ⊂ prompt | base priced on (prompt − cached); cached at cached rate; no double-count |
| **Reasoning** | o-series, Gemini thinking, Claude thinking | reasoning at output rate; **not** added on top of completion total |
| **Tiered (Gemini)** | prompt at 199,999 / 200,000 / 200,001 tokens | **boundary-exact** rate switch (on/just-over/just-under) |
| **Unit trap (Bedrock)** | per-1K row vs per-1M row | correct divisor; no 1000× error |
| **Provisioned Throughput** | units × hours | time-based stream priced separately; tokens NOT used |
| **Batch / tier discount / uplift** | 50% batch, +10% regional | discount/uplift applied from snapshot |
| **Currency** | USD (2dp), JPY (0dp), BHD (3dp) | quantize to ISO-4217 minor unit; unknown ⇒ fail closed |
| **FX** | non-USD with rate + timestamp | original+rate+timestamp+converted all stored; converted exact |
| **Degenerate** | zero tokens, single token, max-context, missing/`None` fields | no crash; exact; missing field ⇒ fail closed, not silent 0 |
| **Provenance** | OpenRouter (provider_reported) vs computed | `cost_source` set correctly; both native+normalized counts stored |
| **Adversarial** | field-name swap (Chat vs Responses), float injected, negative/huge token counts | never silently reads 0; rejects float; rejects nonsensical usage |
| **Multi-provider run** | a synthetic session spanning ≥3 providers + ≥2 currencies | per-role and per-model rollups sum to the grand total exactly |

The expected-cost oracle is computed **by hand / by an independent reference implementation**, not by
the code under test — otherwise the test is tautological (§3.6).

---

## 4. The metric (the acceptance signal — §3.6: this, not pass-rate, is proof)

W5 is "done" only when **all** of these are green, with mutation-tested teeth:

1. **M1 — Exact-to-the-unit computation.** For every golden case, `computed_cost == expected_cost`
   exactly (Decimal equality at the currency minor unit). **Zero tolerance.** This is the §3.11 bar.
2. **M2 — Zero-drift reconciliation (multi-provider synthetic run).** Over a synthetic session spanning
   ≥3 providers and ≥2 currencies, `Σ ledger == Σ (per-provider provider_reported export)` with
   **drift == 0** (gross-vs-gross; credits itemized separately). Any non-zero drift must resolve to a
   labelled, explained legitimate cause or it **fails**.
3. **M3 — Rollup consistency.** Per-role, per-model, per-provider, and per-currency rollups each sum
   **exactly** to the grand total (no penny created or lost; largest-remainder allocation verified).
4. **M4 — Determinism.** Identical `(usage, snapshot)` ⇒ byte-identical `Decimal` cost across many
   repeated runs (property/determinism test, §5.5).
5. **M5 — Ledger integrity.** The RFC-6962 hash chain verifies end-to-end; any mutated record is
   detected; corrections appear as reversing entries (the chain never breaks).
6. **M6 — Provenance correctness.** Every record's `cost_source` and `token_source` are set per §5 of
   `SYNTHESIS.md`; no local estimate is ever written as billable.
7. **M7 — Generality (anti-overfit, §3.9).** Property-based tests over randomized valid usage objects
   and price rows (not just the enumerated golden cases) hold the cost-formula invariants; **mutation
   testing** kills injected faults (wrong rounding mode, dropped cache bucket, off-by-1000 unit, added
   reasoning tokens) — **survivors mean a weak test, fix until killed.**

> Coverage gates (line ≥ 90% / branch ≥ 85%) are **necessary but not sufficient** (§3.6). The
> load-bearing signals are **M1 (exactness)**, **M2 (zero drift)**, and the **mutation score** (M7).

---

## 5. Honest scope boundaries (stated, not hidden)

- We reconcile against provider **exports on closed periods**, not live unbilled estimates.
- We reconcile **gross** cost; credits/promos are a separate ledger, reported as net.
- Prices are **snapshotted and frozen** by `(model, surface, accessed_date, catalog_sha)`; we never
  trust a live price for an already-recorded request.
- We treat provider-returned usage as ground truth and store it verbatim; we do not re-tokenize to
  "correct" it (folder 07 shows that would be *less* accurate).
- Provisioned-Throughput / time-based and token-based costs are **separate streams**, summed at the
  ledger, never conflated.
