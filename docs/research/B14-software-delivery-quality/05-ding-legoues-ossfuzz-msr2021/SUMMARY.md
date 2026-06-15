# SUMMARY — An Empirical Study of OSS-Fuzz Bugs

## Full citation
- **Title:** An Empirical Study of OSS-Fuzz Bugs
- **Authors:** Zhen Yu Ding, Claire Le Goues
- **Year:** 2021
- **Venue:** 2021 IEEE/ACM 18th International Conference on Mining Software Repositories (MSR 2021). arXiv:2103.11518
- **URL/DOI:** https://arxiv.org/abs/2103.11518 ; data https://zenodo.org/records/4625208

## Questions it informs
- **L1.B14.2** (coverage-guided fuzzing; bug classes it catches); background for **L1.B14.1** (continuous fuzzing as a CI gate).

## Context (the system)
OSS-Fuzz is Google's continuous-fuzzing service running coverage-guided fuzzers (libFuzzer, AFL/AFL++, Honggfuzz) against open-source projects; it has reported tens of thousands of bugs since 2016.

## Method and scale (exact)
- Analysed **23,907 bugs** found by OSS-Fuzz across **316 projects**.

## Key findings (exact)
1. **52% of the bugs primarily harmed system availability** (crashes, timeouts, out-of-memory, abort).
2. The remainder includes **memory-safety / security** bugs (buffer overflow, use-after-free) - the high-severity class fuzzing is prized for.
3. The study characterises bug lifecycle (detection, flakiness, time-to-fix); a notable subset of bugs are flaky/hard to reproduce, which matters for CI gating.

## GRADE tier
**High** for the bug-population characterisation (peer-reviewed MSR, very large N from a production system). Secondary numbers beyond 23,907 / 316 / 52% (precise memory-safety percentage, median time-to-fix) could not be cleanly re-fetched from the PDF this pass and are **NOT relied upon**; flagged as open items.

## Reproducibility note
Dataset public (Zenodo 4625208); the 23,907 / 316 / 52% figures corroborated by the arXiv abstract and MSR program listing. Memory-safety percentage left as an open verification item rather than asserting an unverified number.
