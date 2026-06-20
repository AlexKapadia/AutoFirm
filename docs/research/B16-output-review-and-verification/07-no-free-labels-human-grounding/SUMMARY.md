# 07 — *No Free Labels: Limitations of LLM-as-a-Judge Without Human Grounding*

- **Org:** (arXiv preprint, 2025). arXiv:2503.05061.
- **Link:** https://arxiv.org/html/2503.05061v1
- **Tier:** Moderate–High — the sharpest statement of *when an LLM judge is NOT trustworthy*.

## Faithful structured summary

**Central thesis (verbatim):** *"if a judge model cannot generate the correct response and it is not
provided with a correct reference, how can it accurately assess the correctness of other responses?"*
LLM judges **cannot reliably evaluate questions they themselves cannot answer** unless given a
correct human-written reference.

**Quantified collapse on items the judge gets wrong** (Cohen's kappa, agreement-with-human):
- **GPT-4o pairwise (self-generated references):** kappa **dropped 0.78 -> 0.14** on questions it
  answered incorrectly.
- **Llama-3.3-70B single grading (no reference):** agreement **0.62 (correct) -> 0.21 (incorrect)**.
- **Phi-4 single grading (no reference):** **0.48 (correct) -> 0.07 (incorrect)**.
- **Reference-correctness effect:** giving GPT-4o a correct human reference lifted single-grading
  agreement on hard questions **0.21 -> 0.67**.
- **35% of MT-Bench's original references "were either entirely incorrect or inconsistent"** — i.e.
  the references themselves needed verification before trusting the eval.

## Best parts to take (for our gate) and why

1. **The hard ceiling on model review:** on exactly the cases that matter (where the artifact is
   wrong in a way the model can't independently solve) the judge's agreement **collapses toward
   chance (kappa ~0.07-0.21)**. This is the decisive evidence that a model layer must be
   **ADVISORY**, never the release authority — fail-closed must rest on deterministic truth.
2. **Reference-grounding is the only trustworthy mode** (kappa 0.21 -> 0.67). Our model layer must be
   fed the deterministic ground truth (recomputed values, the spec, the accounting identities) as its
   reference, restricting it to checking-against-truth.
3. **"Verify the references themselves" (35% bad)** -> our golden set / gold-reviewer labels must be
   independently verified before we report kappa against them, or the metric is meaningless.
