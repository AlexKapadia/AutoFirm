# SUMMARY — An Empirical Evaluation of Property-Based Testing in Python

## Full citation
- **Title:** An Empirical Evaluation of Property-Based Testing in Python
- **Venue:** Proceedings of the ACM on Programming Languages (PACMPL), OOPSLA 2025. DOI: 10.1145/3764068
- **Year:** 2025
- **URL/DOI:** https://dl.acm.org/doi/10.1145/3764068 ; open PDF https://cseweb.ucsd.edu/~mcoblenz/assets/pdf/OOPSLA_2025_PBT.pdf
- Note: confirm the exact author list from the ACM DL record at the DOI before any external citation.

## Questions it informs
- **L1.B14.2** (quantifies PBT effectiveness vs. example-based unit tests via mutation score).

## Method and scale (exact)
- Studied real-world Python projects using **Hypothesis** (Python's most popular PBT library); corpus on the order of hundreds of programs across 40+ projects.
- Defined **12 categories** of property-based tests via formal definitions plus static analysis to classify tests in the wild.
- Measured test strength with **mutation testing** (mutations killed).

## Key findings (exact)
1. On average, **each property-based test finds about 50 times as many mutations as the average unit test.**
2. PBTs that **look for exceptions, test membership in collections, and check types** are **over 19 times more effective** at finding mutations than other kinds of PBT.
3. The 12-category taxonomy lets teams prioritise high-yield PBT patterns.

## GRADE tier
**High.** Peer-reviewed top PL venue (OOPSLA/PACMPL), large empirical corpus, mutation-based ground truth. The 50x and 19x figures verified via the ACM DL abstract and the open UCSD PDF listing.

## Reproducibility note
Corpus is real OSS Python with Hypothesis; mutation tooling is open. The 50x figure is corroborated directionally by source 03. Treat 50x as a population average (high variance), not a per-test guarantee.
