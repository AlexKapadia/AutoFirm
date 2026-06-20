# 05 — Verga et al., *Replacing Judges with Juries: Evaluating LLM Generations with a Panel of Diverse Models (PoLL)*

- **Authors / org:** Pat Verga et al. (Cohere).
- **Year:** 2024. arXiv:2404.18796.
- **Link:** https://arxiv.org/abs/2404.18796
- **Tier:** High — the primary source for jury/ensemble model-evaluation.

## Faithful structured summary

Argues that a **single large judge (e.g. GPT-4) concentrates intra-model bias** (notably
self-preference), and proposes a **Panel of LLM evaluators (PoLL)**: a jury of **smaller, diverse
models from different providers/families** whose votes are aggregated.

Key reported findings:
- The PoLL of **three small models from different providers (Command-R, GPT-3.5-turbo, Claude Haiku)**
  **beat a single large judge (GPT-4) across six datasets** (single-hop QA, multi-hop QA, Chatbot
  Arena), achieving **higher correlation with human judgments** than GPT-4 alone.
- It did so at **~7x lower cost** than the single large judge.
- **Heterogeneous panels mitigate bias:** pooling across families reduces **positional and stylistic
  (self-preference) biases** because no single model's idiosyncrasy dominates the vote.

> CAUTION (cross-reference): later work (e.g. "Nine Judges, Two Effective Votes") warns that if panel
> members share training lineage their **errors correlate**, shrinking the effective independence of
> the jury. Diversity must be *real* (different families) to deliver the bias reduction.

## Best parts to take (for our gate) and why

1. **If the model-advisory layer is enabled, use a small diverse JURY, not one big judge** — cheaper,
   less biased, better human correlation. Aggregate by majority/consensus.
2. **Self-preference is structurally diluted** by cross-family voting — important because our builders
   may themselves be cheap models; a jury from *other* families reviewing their output avoids the
   builder grading its own family's style.
3. **Independence must be engineered** (distinct model families) or the jury's benefit evaporates —
   mirrors our deterministic checks' design rule that checks never see each other's results.
4. **Still advisory:** even a jury stays add-only on top of the deterministic floor (per 02, 07).
