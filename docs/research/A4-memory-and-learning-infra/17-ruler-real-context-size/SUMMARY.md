# SUMMARY — RULER: What's the Real Context Size of Your Long-Context Language Models?

## Full citation
- **Title:** RULER: What's the Real Context Size of Your Long-Context Language Models?
- **Authors:** Cheng-Ping Hsieh, Simeng Sun, Samuel Kriman, Shantanu Acharya, Dima Rekesh, Fei Jia,
  Yang Zhang, Boris Ginsburg (NVIDIA)
- **Year:** 2024
- **Venue:** **COLM 2024** (Conference on Language Modeling) — peer-reviewed
- **arXiv ID / URL:** arXiv:2404.06654 — https://arxiv.org/abs/2404.06654

## Questions informed
- **L1.A4.2** RAG, retrieval foundations & context-window limits — **second independent primary**
  corroborating that effective context << advertised context, so "context windows are not memory."

## Key claims (faithful)
1. **Claimed vs. effective context gap (exact):** among long-context LLMs advertising ≥32K tokens,
   "only half of them can maintain satisfactory performance at the length of 32K." Effective usable
   context is substantially below the advertised window.
2. **Monotone degradation with length:** "almost all models exhibit large performance drops as the
   context length increases," even for models scoring near-perfect on the vanilla
   needle-in-a-haystack (NIAH) retrieval probe — i.e. passing simple retrieval ≠ usable long context.
3. **NIAH is too easy:** RULER extends single-needle retrieval with multi-hop tracing, aggregation,
   and multi-needle tasks; the harder synthetic tasks expose failures the standard NIAH hides.

## GRADE tier
- **High.** Peer-reviewed (COLM 2024), controlled synthetic benchmark across many models, results
  consistent with and *independent from* Lost-in-the-Middle (folder 08 — TACL; different authors/org,
  NVIDIA vs. Stanford/Princeton/Berkeley; different probe design). No down-rate.

## Why this strengthens the body of evidence
The "context windows are not memory / don't context-stuff" axiom in SYNTHESIS L1.A4.2 previously
leaned mainly on Lost-in-the-Middle (08). RULER is an **independent second primary** with a
*different* failure signature (degradation with raw length, not just positional U-shape), so the
axiom no longer rests on a single study. Together they are mutually corroborating, not co-dependent.

## Reproducibility note
The "half maintain at 32K" and "large drops with length" findings are in the abstract + results
tables at the arXiv URL; the RULER task generator is open-sourced by the authors.
