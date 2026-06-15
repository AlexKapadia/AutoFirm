# SUMMARY — Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks

## Full citation
- **Title:** Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks
- **Authors:** Patrick Lewis, Ethan Perez, Aleksandra Piktus, Fabio Petroni, Vladimir Karpukhin, Naman Goyal, Heinrich Kuttler, Mike Lewis, Wen-tau Yih, Tim Rocktaschel, Sebastian Riedel, Douwe Kiela (Facebook AI Research / UCL / NYU)
- **Year:** 2020
- **Venue:** Advances in Neural Information Processing Systems 33 (NeurIPS 2020), peer-reviewed
- **arXiv ID / URL:** arXiv:2005.11401 — https://arxiv.org/abs/2005.11401

## Questions informed
- **L1.A4.2** RAG & retrieval foundations (the seminal RAG formulation).

## Key claims (faithful)
1. **Parametric + non-parametric memory.** RAG combines a pre-trained seq2seq generator (parametric
   memory) with a **dense vector index of Wikipedia** accessed by a neural retriever (non-parametric
   memory). The index is a Maximum Inner Product Search (MIPS) over DPR passage embeddings.
2. **Two formulations:** **RAG-Sequence** (same retrieved document conditions the whole output) and
   **RAG-Token** (a different document may be used per token); the answer marginalizes over the top-k
   retrieved documents:
   p(y|x) ~ sum over z in top-k(p(.|x)) of p_eta(z|x) * p_theta(y|x,z)  (RAG-Sequence form).
3. **Result (faithful):** RAG set state-of-the-art on three open-domain QA datasets, outperforming
   both parametric-only seq2seq models and task-specific retrieve-and-extract pipelines; it also
   produced more specific, diverse, and factual language than a parametric-only baseline.
4. Knowledge can be **updated by swapping the non-parametric index** without retraining the generator.

## GRADE tier
- **High.** Peer-reviewed NeurIPS 2020; the foundational, originating RAG paper.

## Reproducibility note
RAG-Sequence/RAG-Token marginalization and the MIPS-over-DPR retriever are described in the Methods;
exact dataset SOTA numbers are in the results tables at the arXiv URL.
