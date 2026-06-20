# 04 — Zheng et al., *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*

- **Authors / org:** Lianmin Zheng, Wei-Lin Chiang, Ying Sheng, et al. (LMSYS / UC Berkeley).
- **Year:** 2023 (NeurIPS 2023 Datasets & Benchmarks). arXiv:2306.05685.
- **Link:** https://arxiv.org/abs/2306.05685
- **Tier:** High — the foundational, most-cited study establishing both the promise and the failure
  modes of LLM-as-a-judge.

## Faithful structured summary

Establishes that a strong LLM can serve as a scalable evaluator, and **systematically names the
biases that make it untrustworthy as a sole authority.**

**Agreement with humans (verbatim):** *"strong LLM judges like GPT-4 can match both controlled and
crowdsourced human preferences well, achieving over 80% agreement, the same level of agreement
between humans."* (i.e. LLM-judge vs human agreement ~= human-vs-human agreement, both >80%.)

**The three biases (verbatim definitions):**
1. **Position bias** — "specific positions within a prompt are preferentially selected." Mitigated by
   **swapping the order** of the two candidates and only counting a win if it holds under both orders.
2. **Verbosity bias** — the judge **favours longer responses** independent of quality.
3. **Self-enhancement bias** — the judge **overestimates the quality of its own outputs** (tendency
   to prefer responses in its own style/family).

**Other limitation:** limited grading ability on **math/reasoning** — the judge can be fooled by a
confident wrong answer it cannot itself verify.

**Mitigations proposed:** position-swap, **reference-guided grading** (supply a correct reference so
the judge checks against it rather than its own belief), chain-of-thought / few-shot judging, and
**multi-judge / aggregation**.

## Best parts to take (for our gate) and why

1. **A single LLM judge is biased in three named, measured ways** -> never the acceptance authority.
   In our gate the model layer is **advisory and add-only**; deterministic checks are the floor.
2. **Position bias mitigation (swap) is mandatory** if we ever do pairwise model review.
3. **Reference-guided grading** is the trustworthy mode: give the model the deterministic facts
   (recomputed values, the spec) as its "reference," constraining it to checking-against-truth rather
   than free judgement — directly relevant to how we wire `MODEL_ADVISORY`.
4. **>80% human-human agreement is the realistic ceiling** — our gate-vs-gold-reviewer kappa target
   should be calibrated to "matches a careful human," not to an impossible 100% on subjective items.
