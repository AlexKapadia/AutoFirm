# BEST-PARTS — Dense Passage Retrieval (DPR)

## ADOPT
- **Dense dual-encoder + dot-product/cosine similarity as the retrieval primitive** that the whole
  memory layer rests on (it is what A-Mem and Lewis-RAG instantiate). Build implication: the L2.A4
  retriever uses learned dense embeddings, not just lexical match.
- **Quantified evidence that dense > lexical (9%-19% absolute top-20 gain over BM25).** Build
  implication: justifies the engineering cost of an embedding index; gives a concrete target for the
  `evidence/` retrieval benchmark (AutoFirm's retriever should beat a BM25 baseline by a comparable
  margin on its golden set).

## REJECT / DEFER
- **Do not abandon lexical retrieval entirely.** DPR can miss exact-match/rare-entity queries;
  pair dense with sparse (BM25) in a **hybrid retriever** (consistent with Modular RAG, folder 06,
  and CLAUDE.md s3.5 prefer-hybrids). Pure-dense rejected as the sole retriever for that reason.

## Build implication (concrete)
Confirms the **dense + hybrid (dense+lexical) retriever** for L2.A4 and supplies the **BM25 baseline
+ top-20 accuracy metric** for the retrieval evidence chart.
