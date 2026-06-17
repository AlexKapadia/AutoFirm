# Self-Consistency — Sample-and-Marginalize Majority Vote over Reasoning Paths

> Research note for AutoFirm capability **B1 (multi-model egress)** / workstream **W1**.
> Faithful to the source; the aggregation formula is reproduced verbatim with the paper's
> own notation.

---

## (1) Full citation

- **Title:** Self-Consistency Improves Chain of Thought Reasoning in Language Models
- **Authors:** Xuezhi Wang, Jason Wei, Dale Schuurmans, Quoc Le, Ed H. Chi, Sharan Narang,
  Aakanksha Chowdhery, Denny Zhou (Google Research, Brain Team)
- **Year:** submitted 2022; published 2023
- **Venue:** ICLR 2023
- **arXiv:** arXiv:2203.11171 [cs.CL]
- **URL:** https://arxiv.org/abs/2203.11171

---

## (2) Faithful structured summary

### PROBLEM
Standard chain-of-thought (CoT) prompting uses **greedy decoding** — one reasoning path,
one answer. But:
> "a complex reasoning problem typically admits multiple different ways of thinking leading
> to its unique correct answer."

Greedy decoding leaves that redundancy unused and is brittle.

### METHOD ("sample-and-marginalize")
Two steps:
1. **Sample** a *diverse set* of reasoning paths from the (single) model's decoder instead
   of greedily decoding one. Each sample `i` yields a reasoning path `r_i` and a final
   answer `a_i`.
2. **Marginalize** out the reasoning paths and take the **majority vote** over the answers:
   > "self-consistency applies a marginalization over r_i by taking a majority vote over a_i."

### KEY FORMULAE (reproduced exactly)

**Majority-vote aggregation (the headline / default):** select the answer that is most
consistent across the `m` sampled paths —

```
arg max_a  Σ_{i=1}^{m}  𝟙( a_i = a )
```

i.e. the answer with the most votes; each sampled path counts equally.

**Probabilistic (weighted) marginalization variant.** The unnormalized per-sample weight is
the model's (length-normalized) generation probability of that reasoning-path+answer:

```
P( r_i , a_i | prompt, question )  =  exp{ (1/K) Σ_{k=1}^{K} log P( t_k | prompt, question, t_{<k} ) }
```

where `t_1 … t_K` are the `K` tokens of `(r_i, a_i)` and `1/K` is the length normalization.
The weighted vote then sums these weights per distinct answer and takes the argmax.

> **Key empirical finding (Table 1):** the **unweighted** majority vote performs comparably
> to the normalized weighted-sum aggregation — so simple counting is, in practice, enough.

### Sampling / model configuration (cited exactly)
- **Models evaluated:** **PaLM-540B**, **GPT-3** (code-davinci-001 and code-davinci-002),
  **LaMDA-137B**, **UL2-20B**.
- **Default number of sampled paths:** **40** outputs per question; results averaged over
  **10 runs**.
- **Sampling settings:**
  - UL2-20B / LaMDA-137B: temperature **T = 0.5**, top-k = **40**.
  - PaLM-540B: **T = 0.7**, k = **40**.
  - GPT-3: **T = 0.7**, no top-k truncation.

### RESULTS (headline accuracy gains over CoT greedy decoding, cited exactly)
- **GSM8K: +17.9%**
- **SVAMP: +11.0%**
- **AQuA: +12.2%**
- **StrategyQA: +6.4%**
- **ARC-challenge: +3.9%**

(Gains are absolute accuracy improvements of self-consistency over standard CoT prompting.)

---

## (3) Best-parts-to-take for W1 (ensemble-quorum reconciliation)

This is the **direct theoretical foundation for the quorum/majority-vote** reconciliation
mode in W1. Two adaptations matter:

- **Cross-*model* quorum, not just cross-*sample*.** Self-consistency samples one model many
  times; W1 fans out to **N different models** behind the gateway. The same aggregator
  applies — `arg max_a Σ 𝟙(a_i = a)` over the N model answers — turning a multi-model fan-out
  into a quorum vote. This is the cheapest, most auditable reconciliation primitive available
  and needs **no trained component** (unlike LLM-Blender).
- **When to use majority/quorum (this paper) vs. rank-then-fuse (LLM-Blender):**
  - **Exact-match quorum** for outputs with a canonical comparable form: **classification
    labels, extracted fields, numeric answers, enum/boolean decisions, structured JSON.**
    Normalize first (trim, lowercase, canonical number/JSON form) then count exact matches.
  - **Rank-then-fuse / semantic** for **free-text** outputs where no two answers are
    string-equal — defer to the LLM-Blender note.
  - The branch is chosen **deterministically by declared output type**, recorded in the audit
    log.
- **Keeping quorum deterministic & auditable (critical):**
  - The *vote tally* is a pure deterministic function — given the N answers, the count and
    argmax are exact and replayable. Log every member answer + the tally.
  - **Define an exact, deterministic tie-break** (the paper does not specify one): e.g. break
    ties by the configured **model priority order** (lowest-index/highest-trust model wins),
    never randomly. This makes the gateway reproducible even on split votes.
  - For numeric/extraction tasks, require **exact-match** equality (after canonical
    normalization) — do **not** use the model's own probability weights for the tie-break, as
    those are model-internal and not comparable across heterogeneous models.
- **Quorum threshold knob.** Beyond plain majority, expose a **k-of-N quorum** gate: require
  ≥ k agreeing members or else **fail closed** (abstain / escalate to human). This is the
  fail-closed posture mandated by the platform bar — better to refuse than emit a low-agreement
  answer on a high-stakes deterministic decision.
- **Cost implications.** Cost scales **linearly in N** (N independent generations; the
  aggregation is ~free). Much cheaper to reason about than LLM-Blender's O(N²) ranker. For
  W1, N is small (e.g. 3–5 models) and fan-out is the dominant cost — gate it on task value.

### RED flags for W1
- **Quorum HURTS for non-comparable / open-ended outputs.** Majority vote presumes a
  *single canonical answer* exists. For free-text generation, near-identical-but-not-equal
  strings split the vote and the "majority" is meaningless — use rank-then-fuse instead.
- **Non-determinism from sampling.** The *method itself* relies on `T > 0` sampling to get
  diverse paths — so any single member generation is non-deterministic. W1's determinism must
  live in the **aggregation layer** (the vote is deterministic) and in **pinned seeds /
  greedy decoding** where exact reproducibility per-member is required. Document that
  member-output reproducibility and answer-diversity pull in opposite directions.
- **Equal-weight assumption.** Plain voting weights all N members equally; a weak/biased
  model can swing the vote. If models differ in trust, this paper's unweighted vote is *not*
  sufficient — consider a deterministic learned/static weighting (the optional W1 router), but
  keep weights pinned and auditable.
- **No tie-break in the paper** — W1 MUST add one (see above) or behavior on split votes is
  undefined.

### Verification status
The majority-vote formula `arg max_a Σ_{i=1}^{m} 𝟙(a_i = a)`, the weighted-marginalization
formula, the model list, the "40 paths / 10 runs" setting, the per-model temperatures, and
the five headline accuracy gains were all extracted from the ar5iv HTML render of
arXiv:2203.11171 and quoted verbatim. **Confidence: high.** One caveat: the exact LaTeX of
the weighted formula's length-normalization (`1/K`) was reconstructed from the render's plain
text — confirm the exponent/normalization typography against the PDF before hard-coding the
*weighted* variant. The unweighted majority vote (the W1-relevant formula) is unambiguous.
