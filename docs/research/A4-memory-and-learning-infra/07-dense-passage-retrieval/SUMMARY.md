# SUMMARY — Dense Passage Retrieval for Open-Domain Question Answering

## Full citation
- **Title:** Dense Passage Retrieval for Open-Domain Question Answering
- **Authors:** Vladimir Karpukhin, Barlas Oguz, Sewon Min, Patrick Lewis, Ledell Wu, Sergey Edunov, Danqi Chen, Wen-tau Yih (Facebook AI; Univ. of Washington; Princeton)
- **Year:** 2020
- **Venue:** Proceedings of EMNLP 2020 (main), peer-reviewed
- **DOI / URL:** https://aclanthology.org/2020.emnlp-main.550/ ; arXiv:2004.04906

## Questions informed
- **L1.A4.2** RAG & retrieval foundations (the dense dual-encoder retriever underpinning RAG).

## Key claims (faithful) — formula reproduced
1. **Dual-encoder architecture:** separate encoders embed question and passage; **relevance =
   dot product** of the two dense vectors: sim(q, p) = E_Q(q)^T E_P(p).
2. **Training:** in-batch negatives with a contrastive (negative-log-likelihood of the positive
   passage) objective; embeddings learned from a relatively small number of question-passage pairs.
3. **Result (exact):** the dense retriever "outperforms a strong Lucene-BM25 system greatly by
   9%-19% absolute in terms of top-20 passage retrieval accuracy" across open-domain QA datasets,
   and helps set new end-to-end QA SOTA on multiple benchmarks.

## GRADE tier
- **High.** Peer-reviewed EMNLP 2020; the canonical dense-retrieval baseline (the retriever used by
  Lewis RAG, folder 05).

## Reproducibility note
Dot-product similarity and the 9%-19% absolute top-20 accuracy gain over BM25 are stated in the
abstract/results; re-derivable on the listed QA datasets.
