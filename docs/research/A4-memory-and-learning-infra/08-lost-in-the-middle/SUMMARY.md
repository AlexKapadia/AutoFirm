# SUMMARY — Lost in the Middle: How Language Models Use Long Contexts

## Full citation
- **Title:** Lost in the Middle: How Language Models Use Long Contexts
- **Authors:** Nelson F. Liu, Kevin Lin, John Hewitt, Ashwin Paranjape, Michele Bevilacqua, Fabio Petroni, Percy Liang
- **Year:** 2024 (arXiv preprint 2023; published 2024)
- **Venue:** Transactions of the Association for Computational Linguistics (TACL), Vol. 12, peer-reviewed
- **DOI / URL:** 10.1162/tacl_a_00638 — https://aclanthology.org/2024.tacl-1.9/ ; arXiv:2307.03172

## Questions informed
- **L1.A4.2** Limits of context windows (why a long window is not a substitute for memory/retrieval).

## Key claims (faithful)
1. **U-shaped positional performance (the core finding, exact):** "Performance is often highest when
   relevant information occurs at the beginning or end of the input context, and significantly
   degrades when models must access relevant information in the middle of long contexts."
2. The degradation holds **even for explicitly long-context models** — a larger window does not fix
   the middle-of-context blind spot.
3. Tasks: **multi-document QA** (relevant document placed at varying positions among distractors) and
   **key-value retrieval**; performance varies substantially with the position of the relevant item.

## GRADE tier
- **High.** Peer-reviewed TACL; the canonical evidence for context-position effects. (Specific
  per-position percentage drops live in the paper's figures; the qualitative U-shape is the
  load-bearing, exactly-quoted claim used here.)

## Reproducibility note
Main finding quoted verbatim from the abstract (TACL/arXiv). The U-shaped curve is reproducible via
the released multi-document-QA and key-value protocols.
