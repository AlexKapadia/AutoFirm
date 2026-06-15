# SUMMARY — Generative Agents: Interactive Simulacra of Human Behavior

## Full citation
- **Title:** Generative Agents: Interactive Simulacra of Human Behavior
- **Authors:** Joon Sung Park, Joseph C. O'Brien, Carrie J. Cai, Meredith Ringel Morris, Percy Liang, Michael S. Bernstein
- **Year:** 2023
- **Venue:** Proceedings of the 36th Annual ACM Symposium on User Interface Software and Technology (UIST '23), peer-reviewed
- **DOI / URL:** 10.1145/3586183.3606763 — https://dl.acm.org/doi/10.1145/3586183.3606763 ; arXiv:2304.03442 — https://arxiv.org/abs/2304.03442

## Questions informed
- **L1.A4.1** Agent-memory taxonomy (memory stream = episodic; reflection = abstraction).
- **L1.A4.2** Retrieval foundations (recency/relevance/importance scoring).
- **L1.A4.3** Learning-over-time (reflection generation).

## Key claims (faithful) — formulae reproduced exactly
1. **Memory stream**: an append-only natural-language record of all observations (episodic memory).
2. **Retrieval score** combines three components:
   `score = alpha_recency * recency + alpha_importance * importance + alpha_relevance * relevance`
   with **all three alpha weights set to 1** in their implementation.
   - **Recency** = exponential decay over game hours since last retrieval, **decay factor 0.995**.
   - **Relevance** = **cosine similarity** between the embedding of the memory and the query.
   - **Importance** = an **LLM-assigned integer poignancy score on a 1-10 scale** (1 = mundane, 10 = highly significant).
   (recency and relevance/importance are normalized to [0,1] before combining.)
3. **Reflection**: higher-level abstract thoughts the agent synthesizes from observations; reflections
   are themselves stored and retrievable. Trigger (exact): "we generate reflections when the sum of
   the importance scores for the latest events perceived by the agents exceeds a threshold (150 in
   our implementation)" — yielding "roughly two or three [reflections] a day."
4. Architecture = observe -> store in memory stream -> retrieve (by the score above) -> reflect -> plan.

## Empirical results
- Ablations show that **removing any of the three retrieval components (recency/relevance/importance)
  or removing reflection degrades believability**; the full architecture scored highest in human
  believability evaluation (the paper's headline qualitative+rated result).

## GRADE tier
- **High.** Peer-reviewed UIST '23; the canonical, most-cited source for the recency+relevance+importance
  retrieval heuristic and LLM-synthesized reflection.

## Reproducibility note
Formula, decay factor (0.995), alpha=1, and threshold 150 transcribed from the paper's Memory and
Reflection sections (ACM full-text / arXiv). Directly re-implementable.
