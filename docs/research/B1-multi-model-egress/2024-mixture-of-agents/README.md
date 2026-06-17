# Mixture-of-Agents (MoA) — Layered Aggregation of Multiple LLMs

> Research note for AutoFirm capability **B1 (multi-model egress)** / workstream **W1**.
> Faithful to the source; the layered-output formula is reproduced verbatim with the
> paper's own notation.

---

## (1) Full citation

- **Title:** Mixture-of-Agents Enhances Large Language Model Capabilities
- **Authors:** Junlin Wang, Jue Wang, Ben Athiwaratkun, Ce Zhang, James Zou
  (Duke University / Together AI / Stanford)
- **Year:** 2024
- **Venue:** arXiv preprint (cs.CL); later ICLR 2025
- **arXiv:** arXiv:2406.04692 [cs.CL]
- **URL:** https://arxiv.org/abs/2406.04692

---

## (2) Faithful structured summary

### PROBLEM
How to "harness the collective expertise of multiple LLMs" — combine heterogeneous models so
the ensemble's complementary strengths produce an output better than any single member,
*without* training a new model. The paper notes the empirical "collaborativeness of LLMs":
models produce better responses when shown other models' outputs as reference, even when
those references are individually weaker.

### METHOD — Mixture-of-Agents (MoA)
A **layered** architecture. Each layer has `n` LLM **agents**; every agent in layer `i`
reads **all** outputs of the previous layer as auxiliary context, then generates its own
response. Roles:
- **Proposers** — "excel at generating useful reference responses for use by other models";
  provide context and diverse perspectives.
- **Aggregators** — "proficient in synthesizing responses from other models into a single,
  high-quality output."

**Layer output formula (Section 2.2), reproduced exactly:**

```
y_i = ⊕_{j=1}^{n} [ A_{i,j}( x_i ) ] + x_1 ,        x_{i+1} = y_i
```

> "where `+` here means concatenation of texts; `⊕` means application of the
> Aggregate-and-Synthesize prompt."

Notation: `A_{i,j}` = the j-th agent (LLM) in layer `i`; `x_i` = the input to layer `i`;
the `n` agent outputs in a layer are concatenated, the original prompt `x_1` is appended, and
the **Aggregate-and-Synthesize prompt** drives the next layer's synthesis. The final layer
emits the single answer.

**Aggregate-and-Synthesize prompt** instructs the model to "synthesize these responses into a
single, high-quality response," to "critically evaluate the information provided," and to make
the output "refined, accurate, and comprehensive" rather than merely replicate the inputs.

### KEY FORMULA (reproduced exactly — see verbatim quote above)
`y_i = ⊕_{j=1}^{n} [ A_{i,j}(x_i) ] + x_1` , with `x_{i+1} = y_i`, where `⊕` = apply the
Aggregate-and-Synthesize prompt and `+` = text concatenation.

### RESULTS (headline numbers, cited exactly)
- **Architecture:** default **MoA = 3 layers, 6 proposers**; **MoA-Lite = 2 layers**.
- **Models used:** Qwen1.5-110B-Chat, Qwen1.5-72B-Chat, WizardLM-8x22B,
  LLaMA-3-70B-Instruct, Mixtral-8x22B-v0.1, dbrx-instruct (all **open-source**).
- **AlpacaEval 2.0 (length-controlled win rate):** **MoA = 65.1%** vs **GPT-4 Omni = 57.5%**;
  **MoA-Lite = 59.3%** (still > GPT-4 Omni). MoA beats GPT-4 Omni by **~7.6 absolute points**
  using only open-source models.
- **MT-Bench:** MoA ≈ **9.25 ± 0.10** avg; MoA-Lite ≈ **9.18 ± 0.09**.
- **FLASK:** MoA excels on robustness, correctness, factuality, insightfulness, completeness.

---

## (3) Best-parts-to-take for W1 (ensemble-quorum reconciliation)

MoA is the **maximal-quality / maximal-cost** end of the reconciliation spectrum — a learned
fusion done *via prompting* (no trained fuser, unlike LLM-Blender). Relevance to W1:

- **No trained component needed** — the "aggregator" is just another LLM call with the
  Aggregate-and-Synthesize prompt. So MoA is **cheaper to adopt** than LLM-Blender (no model
  to fine-tune/host) but **far more expensive to run** than majority-vote (multiple layers ×
  multiple agents = many generations).
- **Use MoA-style aggregation ONLY for high-value free-text outputs.** It is the right tool
  when (a) output is open-ended prose, (b) quality matters more than cost, and (c) a single
  best-of-N pick (LLM-Blender) is judged insufficient because *synthesis across* answers adds
  value. For extraction/classification/numeric tasks, MoA is **the wrong tool** — use exact
  quorum.
- **A single aggregation layer is the pragmatic W1 form.** Full 3-layer MoA multiplies cost
  steeply. For the gateway, the useful primitive is **1 layer of N proposers → 1 aggregator
  call** ("MoA-Lite"-like). This is essentially "fan out to N, then have one trusted model
  synthesize," which slots cleanly behind the OpenAI-compatible gateway as a reconciliation
  mode.
- **Keeping it deterministic & auditable.** The synthesis step is generative, so: (a) pin the
  aggregator model + version + the exact Aggregate-and-Synthesize prompt (hash it) in the
  audit log; (b) run the aggregator at **T=0 / greedy** for reproducibility; (c) log all
  proposer outputs `A_{i,j}(x_i)` and the concatenation order — since `⊕` concatenation order
  can change the synthesis, **fix proposer ordering deterministically** (by model priority),
  never randomize.
- **Map to W1's three-tier reconciliation policy:**
  1. exact-match **quorum/majority** (Self-Consistency) for structured/numeric → cheapest,
     fully deterministic, default for decisions;
  2. **rank-then-pick** (LLM-Blender PairRanker, return top-1 verbatim) for free text where a
     single best answer suffices;
  3. **MoA synthesis** (this paper) only for high-value free text where blending genuinely
     adds quality and a review/eval gate exists.

### RED flags for W1
- **Cost / latency explosion.** Full MoA = (layers × proposers) generations + aggregator
  calls — easily **10×+** a single call. Latency compounds because layers are **sequential**
  (layer `i+1` needs layer `i`). Strictly gate on task value; default to 1 aggregation layer.
- **Non-determinism + hallucination from generative synthesis.** Like GenFuser, the aggregator
  *writes a new string* and can introduce content absent from all proposers, or silently
  "correct" a correct field to a wrong one. **Never** route extraction/numeric/regulator-facing
  outputs through MoA synthesis. Pin to greedy decoding.
- **Aggregator is a single point of bias/failure.** The final answer is whatever the
  aggregator decides — a strong proposer minority can be overruled. Unlike a vote, there's no
  auditable tally; the only audit trail is the prompt+inputs+output. Acceptable for prose,
  unacceptable for hard decisions.
- **Ordering sensitivity.** `⊕` concatenation order affects output; must be fixed
  deterministically or the gateway is not reproducible.

### Verification status
The layered-output formula `y_i = ⊕_{j=1}^{n}[A_{i,j}(x_i)] + x_1`, the `⊕`/`+` definitions,
proposer/aggregator roles, the 3-layer/6-proposer + MoA-Lite architecture, the model list,
and the AlpacaEval 2.0 / MT-Bench numbers were extracted from the ar5iv HTML render of
arXiv:2406.04692 and quoted verbatim. **Confidence: high** on the formula structure and the
headline AlpacaEval numbers (65.1% / 57.5% / 59.3%). One caveat: an earlier abstract-only
fetch rendered the layer-input argument as `x_{i-1}` whereas the method-section render gives
`A_{i,j}(x_i)` with `x_{i+1}=y_i`; the latter (method section) is reproduced here as
authoritative — confirm the exact subscript against the PDF before hard-coding.
