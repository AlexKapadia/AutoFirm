# 06 — *Self-Preference Bias in LLM-as-a-Judge*

- **Org:** (arXiv preprint, 2024). arXiv:2410.21819.
- **Link:** https://arxiv.org/abs/2410.21819
- **Tier:** Moderate–High — quantifies the self-preference bias named qualitatively in Zheng (04).

## Faithful structured summary

**Definition (verbatim):** self-preference bias is measured as
**Bias = P(Y'=1 | S=1, Y=1) - P(Y'=1 | S=0, Y=1)** — "the difference between the conditional
probability of the evaluator f rating itself favorably given that the human evaluator has rated it
favorably, and the conditional probability ... given that the human evaluator has rated it
unfavorably" (an Equal-Opportunity fairness framing).

**Key findings:**
- **GPT-4 exhibits the strongest self-preference bias, score ~= 0.520.** Its confusion matrix shows a
  **true-positive rate of 0.945 vs a true-negative rate of 0.425** for its own outputs (it rates its
  own work favorably even when humans would not).
- **Mechanism — perplexity/familiarity (verbatim):** *"LLMs assign significantly higher evaluations
  to outputs with lower perplexity than human evaluators, regardless of whether the outputs were
  self-generated."* LLMs naturally produce low-perplexity text, so their own style feels "familiar"
  and triggers inflated ratings independent of actual quality.

## Best parts to take (for our gate) and why

1. **A model reviewing output in its own style will over-pass it** — the strongest argument that the
   reviewer model must be a **different family from the builder**, and that **model output can never
   clear a deterministic FAIL** (low-perplexity, fluent, wrong artifacts are exactly what fools a
   judge but are caught by recomputation/identity checks).
2. **Quantifies the danger:** TPR 0.945 vs TNR 0.425 means a self-judge waves through bad work ~57%
   of the time — concrete evidence for the plan's "model layer add-only, deterministic floor binding."
3. **Low perplexity != correct** — our efficacy golden set should include *fluent-but-wrong*
   artifacts (a confidently-formatted model with a sign-flipped cash line) to prove the deterministic
   floor catches what a model judge would pass.
