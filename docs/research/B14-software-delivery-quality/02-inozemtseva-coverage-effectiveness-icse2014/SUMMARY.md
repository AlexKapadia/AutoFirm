# SUMMARY — Coverage Is Not Strongly Correlated with Test Suite Effectiveness

## Full citation
- **Title:** Coverage Is Not Strongly Correlated with Test Suite Effectiveness
- **Authors:** Laura Inozemtseva, Reid Holmes
- **Year:** 2014
- **Venue:** Proceedings of the 36th International Conference on Software Engineering (ICSE 2014), pp. 435-445. ACM Distinguished Paper Award.
- **URL/DOI:** https://dl.acm.org/doi/10.1145/2568225.2568271 ; PDF https://pdfs.semanticscholar.org/3b6c/26c317344ee98bf11a2ac744e6d8b2ae6f6d.pdf

## Questions it informs
- **L1.B14.2** (coverage gates vs. true effectiveness); cross-feeds **L1.A9.3**.

## Core problem
Code coverage is widely used as a proxy for a suite's fault-detection ability. This paper measures whether that proxy holds at scale, and whether stronger coverage criteria help.

## Method and scale (exact)
- **5 large open-source Java projects**, each on the order of 100K lines of code and each already having **1000+ test methods**.
- Effectiveness measured via **mutation testing**.
- Computed correlation between coverage and effectiveness both ignoring and controlling for suite size (number of test cases).

## Key findings (exact)
1. Ignoring suite size, there is a **moderate to high correlation** between coverage and effectiveness (confounded by size).
2. Controlling for the number of test cases, the correlation drops to **low to moderate**: coverage is **not strongly correlated** with effectiveness.
3. **Stronger coverage criteria do not provide greater insight** than weaker ones.
4. Implication: a coverage target alone is a weak quality gate; suite size and assertion strength dominate.

## GRADE tier
**High.** Peer-reviewed ICSE, Distinguished Paper, large realistic subjects, explicit confound control. Corroborates source 01 from the coverage side.

## Reproducibility note
Subjects are named large OSS Java projects; method (random sub-suites + mutation score + size control) is reproducible. Cross-checked against the morning-paper summary, ICSE proceedings, and the It-Will-Never-Work-in-Theory review.
