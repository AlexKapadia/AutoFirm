# BEST-PARTS — RAG Survey (Gao et al.)

## ADOPT
- **Advanced-RAG re-ranking + query rewriting as the default, not Naive RAG.** Build implication:
  AutoFirm's retriever is a pipeline = query-rewrite -> dense retrieve (cosine, from A-Mem/DPR) ->
  **re-rank** -> context-compress, precisely because Naive RAG's documented failure modes (low
  precision/recall, hallucination) are unacceptable at the institution-grade bar.
- **Modular RAG composition** as the architecture style: retrieval, memory, routing, and fusion are
  separate, swappable modules — matches AutoFirm's modular-agent-company ethos and lets the L2.A4
  branch-experiment swap one module without rebuilding the layer.
- **The Naive-RAG drawback list as an explicit test matrix** (precision, recall, grounding,
  redundancy) — each becomes an adversarial retrieval test for `evidence/`.

## REJECT / DEFER
- **Reject Naive RAG as a shippable design** — it is the baseline to beat, not adopt.
- **Defer the most elaborate iterative/recursive retrieval loops** until latency budgets are known
  (they multiply LLM calls).

## Build implication (concrete)
Sets the **retriever pipeline shape (Advanced/Modular RAG: rewrite -> retrieve -> re-rank ->
compress)** and the **retrieval-quality test matrix** for L2.A4 and the evidence showcase.
