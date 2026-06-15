# SUMMARY — Retrieval-Augmented Generation for Large Language Models: A Survey

## Full citation
- **Title:** Retrieval-Augmented Generation for Large Language Models: A Survey
- **Authors:** Yunfan Gao, Yun Xiong, Xinyu Gao, Kangxiang Jia, Jinliu Pan, Yuxi Bi, Yi Dai, Jiawei Sun, Meng Wang, Haofen Wang
- **Year:** 2023-2024 (submitted 2023-12-18; revised through 2024)
- **Venue:** arXiv preprint (widely cited)
- **arXiv ID / URL:** arXiv:2312.10997 — https://arxiv.org/abs/2312.10997

## Questions informed
- **L1.A4.2** RAG & retrieval foundations (paradigm taxonomy + component breakdown).

## Key claims (faithful)
1. **Three RAG paradigms (progression):**
   - **Naive RAG** — basic index -> retrieve -> generate ("retrieve-read"). Drawbacks: low retrieval
     precision and recall (irrelevant/missing chunks), hallucination/lack of grounding, and clumsy
     augmentation (redundancy, context-length pressure).
   - **Advanced RAG** — adds **pre-retrieval** optimizations (better indexing, query rewriting/expansion,
     routing) and **post-retrieval** optimizations (re-ranking, context compression/selection) to
     raise retrieval quality.
   - **Modular RAG** — composable modules (search, memory, routing, fusion, predict, task-adapter) and
     reconfigurable patterns (e.g., rewrite-retrieve-read, iterative/recursive/adaptive retrieval).
2. **Tripartite foundation / three core components:** **Retrieval**, **Generation**, **Augmentation**.
3. RAG addresses LLM problems of **hallucination, outdated knowledge, and non-transparent reasoning**
   by grounding in external, updatable sources.

## GRADE tier
- **Moderate.** arXiv survey (secondary), heavily cited; used for the paradigm taxonomy / option
  space, not as sole basis for any number.

## Reproducibility note
The Naive/Advanced/Modular taxonomy and the retrieval/generation/augmentation decomposition are the
survey's central organizing figures, re-derivable from the abstract + Section 2-4 at the arXiv URL.
