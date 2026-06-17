# RouteLLM — Learned Router Between a Strong and a Weak LLM (2024)

> Research note for AutoFirm **W1 multi-model egress** (B1). Faithful summary of a primary
> source. Formulae reproduced exactly; where transcription risk exists it is flagged.

---

## (1) Full citation

- **Title:** *RouteLLM: Learning to Route LLMs with Preference Data*
- **Authors:** Isaac Ong, Amjad Almahairi, Vincent Wu, Wei-Lin Chiang, Tianhao Wu,
  Joseph E. Gonzalez, M Waleed Kadous, Ion Stoica
- **Org:** LMSYS / UC Berkeley (Sky Computing Lab) + Anyscale
- **Year:** 2024 (submitted 2024-06-26; latest v4 2025-02-23)
- **Venue:** arXiv preprint (cs.LG)
- **arXiv id:** 2406.18665
- **URL:** https://arxiv.org/abs/2406.18665 — HTML: https://arxiv.org/html/2406.18665v4

---

## (2) Faithful structured summary

### PROBLEM
Strong LLMs (e.g. GPT-4) are high quality but expensive; weak LLMs (e.g. Mixtral-8x7B)
are cheap but lower quality. Routing **each query at inference time** to the cheapest model
that will still answer it well captures most of the strong model's quality at a fraction of
the cost. The paper learns this router **from human preference data** (Chatbot Arena),
augmented with synthetic / golden-label data, and shows the learned routers transfer to
unseen strong/weak model pairs.

### METHOD — four router families
A query `q` is routed between a strong model `M_strong` and a weak model `M_weak`. All routers
estimate **`P_θ(win_s | q)`** = probability the strong model "wins" (gives the preferred
answer) for `q`. Four parameterisations are trained:

1. **Similarity-weighted (SW) ranking** — a Bradley-Terry style win-probability weighted by
   embedding similarity of `q` to labelled arena battles (non-parametric, no training).
2. **Matrix factorization (MF)** — learns model & query embeddings; scoring function
   (reproduced exactly):
   `δ(M, q) = w_2^T ( v_m ⊙ (W_1^T v_q + b) )`
   where `⊙` is the Hadamard (element-wise) product, `v_m` a model embedding and `v_q` a query
   embedding. *(Transcription-risk: the exact bilinear form / bias placement should be
   re-checked against §4 of the paper before implementation — flagged below.)*
3. **BERT classifier** — fine-tuned BERT mapping `q → P_θ(win_s | q)`.
4. **Causal LLM classifier** — an instruction-tuned LLM that outputs the win label.

Training objective (max-likelihood over preference data `D_pref`):
`max_θ  Σ_{(q, l_{s,w}) ∈ D_pref}  log P_θ( l_{s,w} | q )`.

### KEY FORMULAE (reproduced exactly)

**Routing decision rule** with cost threshold `α ∈ [0,1]`:

```
            { M_weak     if  P(win_s | q) <  α
R^α(q)  =   {
            { M_strong   if  P(win_s | q) ≥  α
```

Raising `α` routes more queries to the strong model (higher cost, higher quality); `α` is the
single knob that sweeps the cost–quality curve.

**Performance Gap Recovered (PGR)** — fraction of the strong-vs-weak quality gap the router
recovers:

```
PGR(M_R^α) = [ r(M_R^α) − r(M_w) ] / [ r(M_s) − r(M_w) ]
```

where `r(·)` is average response quality. `PGR = 0` ⇒ router = weak model; `PGR = 1` ⇒ router
matches the strong model.

**Average Performance Gap Recovered (APGR)** — area under the PGR-vs-cost curve (Eq. 7):

```
APGR(M_R^α) = ∫_0^1  PGR(M_R^α)  d( c(M_R^α) )
```

Discretised over 10 equally-spaced cost points `{c_i}` (for each `c_i` pick the `α_i` meeting
the cost constraint):

```
APGR(M_R^α) ≈ (1/10) Σ_{i=1}^{10}  PGR(M_R^{α_i})
```

> Verification note: **PGR and APGR VERIFIED 2026-06-17 against the canonical paper
> (ar5iv.labs.arxiv.org/abs/2406.18665).** The paper typesets the router as `R_bin^α`; the
> `M_R^α` notation above is a faithful reproduction of the identical formulae —
> `PGR = (r(R) − r(M_weak)) / (r(M_strong) − r(M_weak))`, `APGR = ∫_0^1 PGR d(c)` with the
> `(1/10) Σ` discretisation. The "over 2×" abstract claim is also confirmed verbatim. No error.

**Call-Performance Threshold, CPT(x%)** (verbatim): *"Given a desired router performance, i.e.
achieving a PGR of x%, the CPT(x%) represents the minimum percentage of calls to the strong
model needed to reach the desired PGR."* Lower CPT = cheaper to hit the target.

### RESULTS (headline numbers, cite exactly)
- **MT-Bench (GPT-4 vs Mixtral-8x7B):** matrix-factorization router hits **CPT(50%) ≈ 23.21%**
  strong-model calls vs **49.03%** for the random-router baseline; reported **cost savings up
  to 3.66×** while maintaining ~95% of GPT-4 quality (Table 6 context).
- **MMLU (5-shot):** SW-ranking **CPT(50%) ≈ 35.40%** vs **50.07%** random (~30% reduction).
- **GSM8K (8-shot):** causal-LLM router **CPT(50%) ≈ 33.64%** vs ~50% random (~33% reduction).
- **Abstract headline (verbatim):** *"evaluations on public benchmarks show that our approach
  can reduce costs by over 2 times without sacrificing response quality."*
- Routers trained on one strong/weak pair **transfer** to new pairs without retraining.

---

## (3) Best-parts-to-take — for AutoFirm W1

W1 = **deterministic selection policy + OPTIONAL learned router + ensemble-quorum
reconciliation** behind a self-hosted OpenAI-compatible gateway.

**Adopt:**
- **The `α`-threshold contract as the OPTIONAL layer.** A learned router is exactly a function
  `q → P(win_s | q)` plus a tunable threshold `α`. Wrap it so the **deterministic policy runs
  first** (hard rules: PII/compliance class, required tool-calling, latency SLA, kill-switch),
  and only when the deterministic policy returns *"either model is admissible"* does the
  learned `P(win_s|q) ≥ α` decide. The router can be **disabled by config** (`α = 1` forces the
  strong model = fail-safe, fail-closed default).
- **PGR / APGR / CPT as our gateway KPIs.** They are model-agnostic, deterministic given a
  golden set, and feed straight into the `evidence/` showcase: report APGR and a PGR-vs-cost
  curve per model pair, with the **random-router baseline** as the floor.
- **Preference-data telemetry.** The router needs `(query, which model won)` labels. W1 can
  mint these for free from **ensemble-quorum runs**: when ≥2 models answer and a judge/quorum
  picks a winner, that is a preference label. Log `(prompt-embedding, candidate models,
  winner, cost, latency)` to an append-only audit store — this *is* the training set.
- **Matrix-factorization router** is attractive: tiny, interpretable (model & query
  embeddings), retrainable on our own telemetry, and degrades gracefully to SW-ranking when
  data is sparse.

**RED flags / cautions:**
- **Overfit-to-benchmark risk (HIGH).** Routers are tuned on MT-Bench/MMLU/GSM8K distributions.
  Our traffic is *company-building* prompts (finance, code, docs) — a different distribution.
  **Do not import their thresholds; learn `α` on our own golden set** and re-validate per model
  pair. Keep the deterministic core authoritative so a mis-calibrated router cannot cause harm.
- **Telemetry/cold-start.** No preference data ⇒ no router. The deterministic policy must be a
  complete standalone system; the router is additive only once telemetry exists.
- **Binary strong/weak only.** RouteLLM routes between *two* models. W1's egress is N-way;
  treat RouteLLM as the *pairwise* primitive, not the multi-model selector (see RouterBench).

**Could NOT fully verify:** the exact MF scoring formula `δ(M,q)=w_2^T(v_m ⊙ (W_1^T v_q + b))`
(bias term placement / dimensionality) — confirm against §4 + the released `route-llm` code
before coding the router. Everything else above is reproduced from the paper text.
