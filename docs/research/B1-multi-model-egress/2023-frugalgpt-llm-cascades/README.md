# FrugalGPT — Budget-Constrained LLM Cascades

> Research note for AutoFirm W1 (multi-model egress). Faithful structured summary of the
> source paper, with formulae reproduced exactly and attributed. Where a formula could not
> be verified character-for-character against the source, it is flagged explicitly.

---

## (1) Full citation

- **Title:** *FrugalGPT: How to Use Large Language Models While Reducing Cost and Improving Performance*
- **Authors / org:** Lingjiao Chen, Matei Zaharia, James Zou — Stanford University
- **Year:** 2023
- **Venue:** arXiv preprint (also presented in the LLM-efficiency line of work; widely cited as the canonical LLM-cascade paper). Not a peer-reviewed conference proceeding at time of posting — it is a **primary-source preprint**.
- **arXiv id:** arXiv:2305.05176
- **URL:** https://arxiv.org/abs/2305.05176 (HTML mirror: https://ar5iv.labs.arxiv.org/html/2305.05176)

---

## (2) Faithful structured summary

### PROBLEM

LLM APIs (the paper names GPT-4, ChatGPT, J1-Jumbo, GPT-3 family, etc.) have **heterogeneous
pricing** that differs by **two orders of magnitude**, and per-token billing makes large query
volumes expensive. Goal: get the accuracy of the best/most-expensive model at a fraction of the
cost. The paper frames three families of cost-reduction strategy:

1. **Prompt adaptation** — shorten prompts / batch queries to cut input tokens.
2. **LLM approximation** — caching and model fine-tuning to avoid calling an expensive API.
3. **LLM cascade** — query a sequence of LLMs cheapest-first, stopping early when an answer is
   judged reliable. **FrugalGPT is an instantiation of the LLM-cascade strategy.**

### METHOD

For each query *q*, FrugalGPT routes through an **ordered list of LLM APIs** and stops at the
first one whose answer is judged reliable by a learned **scoring function**:

1. Maintain an ordered list `L` of selected LLM APIs (a subset/permutation of the K available
   APIs `{f_i(·)}` for `i = 1..K`).
2. For position *i* in the list, call API `f_{L_i}(q)` to get a candidate answer.
3. Compute a **reliability score** `g(q, f_{L_i}(q)) ∈ [0,1]` from a trained regression model
   (the paper uses a **DistilBERT** scorer that takes the query + the generated answer).
4. If `g(q, f_{L_i}(q)) ≥ τ_i` (the per-position threshold), **accept and return** that answer.
   Otherwise **escalate** to position *i+1*.
5. The returned answer comes from the first position *z* where the threshold is met.

This is the classic deterministic cascade: cheap models handle easy queries; only hard queries
escalate to expensive models.

### KEY FORMULAE (reproduced and attributed)

**Budget-constrained objective (Eq. — general strategy form).** Maximize expected task reward
subject to an average-cost budget *b*:

```
maximize   E_{(q,a) ~ Q×A} [ r( a , â(s,q) ) ]
subject to E_{(q,a) ~ Q×A} [ c(s,q) ] ≤ b
```

where `a` = correct answer, `â(s,q)` = answer produced by strategy `s`, `r(·,·)` = reward
(answer-quality) function, `c(s,q)` = cost of processing `q` under `s`, `b` = user budget.

**FrugalGPT cascade specialization** — learn the LLM list `L` and thresholds `τ`:

```
max_{L, τ}   E[ r( a , f_{L_z}(q) ) ]
s.t.         E[ Σ_{i=1..z} ( c̃_{L_i,2}·‖f_{L_i}(q)‖ + c̃_{L_i,1}·‖q‖ + c̃_{L_i,0} ) ] ≤ b
where        z = arg min_i { i : g(q, f_{L_i}(q)) ≥ τ_i }
```

i.e. *z* is the **first** position in the cascade whose reliability score clears its threshold.
The cost term is **linear in tokens**: `c̃_{L_i,1}` is the per-input-token price, `c̃_{L_i,2}` the
per-output-token price, and `c̃_{L_i,0}` a fixed per-call cost for API `L_i`. (Symbols `c̃` and the
exact `arg min` index notation are transcribed from the HTML mirror of the optimization section;
treat the precise subscript ordering of input vs. output coefficients as **approximate** — see
RED FLAG / verification note below.)

**Scoring function signature:**

```
g(·,·) : Q × A → [0,1]
```

a regression model predicting the probability the generated answer is correct.

**Learned parameters:** `L ∈ [K]^m` (ordered list of *m* APIs), `τ` (per-position thresholds),
and the scorer `g` (DistilBERT). The optimizer prunes the combinatorial search over LLM lists by
ignoring lists with little answer disagreement and approximates the objective by interpolation
across samples.

### RESULTS (headline numbers, as cited)

- **Up to 98% cost reduction** while matching the best individual LLM (GPT-4), **or** up to
  **+4% accuracy** improvement over GPT-4 at comparable cost. (Abstract — primary claim.)
- Per-dataset case-study figures cited from the paper's experiments:
  - **HEADLINES** (financial news): ≈ **98%** cost savings while matching GPT-4; a separate
    operating point reports cost cut ~80% with **+1.5%** accuracy.
  - **OVERRULING** (legal): ≈ **73%** cost savings with ~+1% accuracy over GPT-4.
  - **COQA** (reading comprehension): ≈ **59%** cost savings matching GPT-3-class accuracy.
- Three datasets used overall: **HEADLINES, OVERRULING, COQA**.

> Verification note: the **98% / +4%** headline and the three dataset names are verified directly
> from the abstract and results. The exact per-dataset percentages (73%, 59%, the 80%/+1.5%
> operating point) are transcribed from the results/case-study section via the HTML mirror and
> should be **re-checked against the PDF tables** before being quoted in any external artifact.

---

## (3) Best-parts-to-take for AutoFirm W1

AutoFirm W1 = **deterministic selection policy + optional learned router + ensemble-quorum
reconciliation**, behind a self-hosted OpenAI-compatible gateway. Map FrugalGPT onto that:

- **Adopt the cascade-with-threshold as the deterministic core.** Order models cheapest→strongest;
  call in sequence; **escalate only when a reliability score falls below a fixed, auditable
  threshold `τ_i`.** Keep the *escalation rule itself deterministic* (a comparison against a
  config-pinned threshold), even if the score that feeds it comes from a learned model — this
  satisfies the "deterministic where it matters / fail-closed" bar: if the scorer is unavailable
  or returns NaN, **fail closed by escalating** (never silently accept a cheap answer).
- **The scorer `g` is exactly the "optional learned router."** Use a small, swappable regression
  model (FrugalGPT used DistilBERT) that scores `(query, candidate answer) → [0,1]`. Treat it as
  an *advisory signal* gated by deterministic thresholds, not as the decision-maker. This is the
  clean determinism-core / optional-ML-layer split from the W1 design.
- **Use FrugalGPT's exact cost model as the gateway's accounting unit.** The linear
  per-input-token + per-output-token + fixed-per-call cost (`c̃_{·,1}, c̃_{·,2}, c̃_{·,0}`) is the
  right shape for a billing/egress ledger and for any budget-constrained optimizer. Pin these
  coefficients per model in config so the budget constraint is reproducible and audited.
- **Budget constraint as a first-class config knob.** The `E[cost] ≤ b` objective gives W1 a
  principled "spend ceiling per tenant/job" lever — solve for thresholds offline against a golden
  set, then freeze them; do not tune online to the live distribution (avoids overfitting).
- **Where it does NOT directly serve W1:** FrugalGPT is a *single-answer* cascade — it picks one
  model's answer. W1 also wants **ensemble-quorum reconciliation** (multiple models vote). FrugalGPT
  gives the *cheap-first escalation* half but not the quorum half — take its threshold/scoring
  machinery for the cascade leg and pair it with a separate quorum policy for high-stakes queries.

### RED FLAGS / caveats

- **Scorer generalization risk.** `g` is *trained per task/distribution*. A scorer fit on
  HEADLINES will not transfer to arbitrary AutoFirm workloads. W1 must either (a) retrain/calibrate
  per workload with a labelled golden set, or (b) fall back to a deterministic, model-agnostic
  reliability proxy (e.g. self-consistency / agreement) when no scorer is calibrated. **Do not ship
  a single global scorer and assume it generalizes** — that would be overfitting to the benchmark.
- **Telemetry dependence.** Learning `L`, `τ`, and `g` needs labelled (query, answer, correctness)
  data. If AutoFirm cannot collect ground-truth correctness for a workload, the *learned* parts are
  not available and W1 should degrade gracefully to the deterministic cascade with hand-set
  thresholds + quorum. Design for "no telemetry" as the default path.
- **Cost-coefficient drift.** Provider prices change; the `c̃` coefficients must be config, not
  code, and re-validated, or the budget math silently goes wrong.
