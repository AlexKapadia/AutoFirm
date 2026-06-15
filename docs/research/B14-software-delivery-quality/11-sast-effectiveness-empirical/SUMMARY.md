# SUMMARY — Empirical effectiveness and limits of SAST tools

## Full citation(s)
- **(A)** Croft, R. et al. / NIST SATE-derived analysis - "An empirical study of security warnings from static application security testing tools," Journal of Systems and Software, 2019. https://www.sciencedirect.com/science/article/abs/pii/S0164121219302018
- **(B)** "Do Developers Use Static Application Security Testing (SAST) Tools Straight Out of the Box? A Large-Scale Empirical Study," 2024. https://dl.acm.org/doi/fullHtml/10.1145/3674805.3690750
- **(C)** "Do I really need all this work to find vulnerabilities? An empirical case study comparing vulnerability detection techniques on a Java application," 2022. arXiv:2208.01595. https://arxiv.org/pdf/2208.01595

## Questions it informs
- **L1.B14.3** (secure-SDLC: realistic capability of SAST/DAST gates).

## Key findings (exact)
1. **False-positive rates vary widely**: a NIST-derived study found FP rates between **3% and 48%** across ten SAST tools; a tool with a *low* FP rate had a *true-positive rate of zero* on security issues - i.e. low FP can mean low recall, not high accuracy.
2. **High false negatives**: SAST tools miss **47%-80% of vulnerabilities** under test conditions; **combining multiple tools** reduces the false-negative rate only to **30%-69%**, at the cost of more false positives.
3. Developers **prioritise reducing false negatives** (missed real vulns) over false positives - missing a vuln is worse than a false alarm.

## Implication
No single SAST tool is sufficient. Effective secure-SDLC layers **multiple complementary techniques** (SAST + DAST + SCA/dependency scanning + secrets scanning + fuzzing + manual review) and **triages** findings rather than trusting a single scanner's verdict. This directly supports a defense-in-depth, fail-closed gate design.

## GRADE tier
**Moderate-High.** Multiple independent peer-reviewed empirical studies converging on the same conclusion (high variance in FP, substantial FN, tool-combination helps but does not solve). Strong corroboration across (A)(B)(C).

## Reproducibility note
The 3-48% FP range and 47-80% FN range are reported in the cited studies and benchmark datasets (Juliet/SATE, real C++/Java projects). Numbers are tool- and benchmark-dependent; used as order-of-magnitude design constraints, not precise constants.
