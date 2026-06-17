# Hybrid LLM — Cost-Efficient, Quality-Aware Query Routing (ICLR 2024)

> Research note for AutoFirm **W1 multi-model egress** (B1). Faithful summary of a primary
> source. Formulae reproduced exactly; transcription risk flagged where it exists.

---

## (1) Full citation

- **Title:** *Hybrid LLM: Cost-Efficient and Quality-Aware Query Routing*
- **Authors:** Dujian Ding, Ankur Mallick, Chi Wang, Robert Sim, Subhabrata Mukherjee,
  Victor Rühle, Laks V. S. Lakshmanan, Ahmed Hassan Awadallah
- **Org:** Microsoft (with University of British Columbia)
- **Year:** 2024
- **Venue:** ICLR 2024 (main conference)
- **arXiv id:** 2404.14618
- **URL:** https://arxiv.org/abs/2404.14618 — HTML: https://arxiv.org/html/2404.14618v1

---

## (2) Faithful structured summary

### PROBLEM
A large (cloud) model `L` is high quality but costly; a small (edge-deployable) model `S` is
cheap but weaker. Route **easy queries to `S`** and only **hard queries to `L`**, at a
**test-time-tunable** quality level, to cut cost with little/no quality loss. The router never
calls both models — it decides up front from the query alone (no judge, unlike a cascade).

### METHOD — quality-gap labels + three routers

**Quality gap (verbatim):** *"Quality gap of a query x as `H(x) := q(S(x)) − q(L(x))`"* — the
difference in response quality between small and large model, where `q(·)` is a quality score
(**BART score** in their main setup). `H(x) ≥ 0` means the small model is *at least as good*,
so the query should be routed to `S`.

Three labelling strategies train a router `p_w(x)` (predicted prob. that `S` suffices):

1. **Deterministic router** — hard labels from a single sampled response each:
   `y_i^det = 1[ q(S(x_i)) ≥ q(L(x_i)) ]`, trained with binary cross-entropy.
2. **Probabilistic router** — soft labels capturing sampling randomness (verbatim):
   `y_i^prob := Pr[ H(x_i) ≥ 0 ] = Pr[ q(S(x_i)) ≥ q(L(x_i)) ] = E[ 1[ q(S(x_i)) ≥ q(L(x_i)) ] ]`,
   estimated by **sampling 10 responses from each model** and averaging the indicator; same BCE
   loss, relaxed targets.
3. **Transformation router** — relaxes the bar by margin `t > 0` to fix class imbalance when `L`
   strongly dominates: `Pr[ H(x) ≥ −t ] = Pr[ q(S(x)) > q(L(x)) − t ]`. The relaxation `t` is
   chosen to **maximise label spread** (verbatim):
   `t* = argmax_t  (1/N²) Σ_{i,i'} | y_i^trans(t) − y_{i'}^trans(t) |`.

### KEY FORMULA — routing decision & cost control
Route to the **small** model when the router score exceeds a threshold (verbatim intent):
*"Queries with router score higher than the threshold to the small model,"* because a *"high
value of `Pr[H(x) ≥ 0]` corresponds to queries for which there is high likelihood that response
quality of small model will be at least as high as large model."* Formally:

```
route(x) =  S   if  p_w(x) ≥ τ
            L   otherwise
```

**Cost advantage** (verbatim) = *"percentage of queries routed to smaller model,"* tuned
dynamically by moving the threshold `τ` at test time — **no retraining** needed to slide along
the cost–quality curve. *(Transcription-risk: confirm threshold direction and that `τ` is on
`p_w` directly, against §3–4, before coding.)*

### RESULTS (headline, cite exactly) — MixInstruct unless noted
- *"22% fewer calls to GPT-3.5-turbo with 1% drop in response quality (BART score)."*
- **Abstract headline:** *"up to 40% fewer calls to the large model, with no drop in response
  quality."*
- Similar-sized pair (Llama-2 7b vs 13b): *"40% cost advantage with no drop in response
  quality."*
- Medium gap (Llama-2 13b vs GPT-3.5-turbo): *"20% cost advantage with ≤1% quality drop."*
- Large gap (FLAN-t5 800m vs Llama-2 13b): *"40% cost advantages with 10.3% quality drop"* using
  the transformation router (`r_trans`) — i.e. the bigger the quality gap, the less free lunch.

---

## (3) Best-parts-to-take — for AutoFirm W1

**Adopt:**
- **Judge-free routing as the cheap fast path.** Unlike a cascade (RouterBench) or quorum,
  Hybrid-LLM decides from the **query alone** — one forward pass of a small router, no second
  model call. This is the ideal **OPTIONAL learned layer** inside W1's deterministic core: when
  the deterministic policy admits either model, `p_w(x) ≥ τ` cheaply diverts easy queries to the
  small model *before* any expensive call. `τ = 1` ⇒ always use the large model (fail-safe
  default), so the layer is disable-by-config.
- **The `H(x)` quality-gap label is exactly the telemetry W1 already produces.** Every time the
  ensemble-quorum runs both a small and large model and scores them, we get
  `q(S(x)), q(L(x)) → H(x)` — directly usable to train/refresh `p_w`. The **probabilistic
  soft-label** version (sample N, average the indicator) is the more robust choice and is worth
  the extra sampling during the offline labelling pass.
- **Transformation-router trick for imbalance.** Company-building traffic will be dominated by
  hard prompts where the large model wins, giving a lopsided label set. The `t`-margin relaxation
  is a clean, principled fix — adopt it (with `t*` chosen by their spread-maximisation) rather
  than ad-hoc class weighting.
- **Threshold `τ` = the cost knob**, identical in spirit to RouteLLM's `α` and RouterBench's `λ`.
  W1 should expose **one cost-quality dial** to tenants and map all three formalisms onto it.

**RED flags / cautions:**
- **Diminishing returns scale with the quality gap.** Their own large-gap result (10.3% quality
  drop for 40% savings) is the warning: when `S` is far weaker than `L`, routing easy queries
  away buys little and risks real quality loss. W1 must **measure the realised quality drop on
  our golden set**, not assume the headline 40%/0% transfers.
- **Quality metric is BART score.** Their "no quality drop" is *relative to BART score*, which is
  a proxy and may not track AutoFirm's domain correctness (finance accuracy, code correctness).
  W1 must **re-define `q(·)` with our own task-appropriate, deterministic graders** (e.g.
  numeric-exactness checks, test-pass rates) — never inherit BART as the quality oracle.
- **Overfit / distribution-shift (HIGH).** `p_w` is trained on a fixed query distribution; a new
  client/company shifts it. Keep the deterministic core authoritative, retrain `p_w` on rolling
  telemetry, and **fail closed to the large model** whenever the router is low-confidence or
  stale.

**Could NOT fully verify:** the exact threshold inequality direction and whether `τ` is applied
to `p_w(x)` directly vs a calibrated transform — confirm against §3–4 of the paper and the
released code before implementing the routing comparator.
