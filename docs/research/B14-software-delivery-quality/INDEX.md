# INDEX — B14 Software delivery & engineering quality for client products

Status: SEEDED (researched to DEPTH-RUBRIC; not yet QA-PASSED by CRO).
Owner: B14 Research Analyst. Single-writer dir.

## Questions
- L1.B14.1 CI/CD pipeline design (build/test/scan gates, deploy/rollback, preview envs)
- L1.B14.2 Testing strategy (test pyramid, property/fuzz/mutation, coverage + mutation-score gates)
- L1.B14.3 Code-organisation & maintainability + secure-SDLC (SAST/DAST/dep-scan)

## Sources (one folder each: SUMMARY.md + BEST-PARTS.md)
| # | Source | Tier | Primary question |
|---|---|---|---|
| 01 | Just et al., Mutants vs real faults, FSE 2014 | High | B14.2 |
| 02 | Inozemtseva & Holmes, Coverage not strongly correlated, ICSE 2014 | High | B14.2 |
| 03 | Claessen & Hughes, QuickCheck, ICFP 2000 | High | B14.2 |
| 04 | Empirical Eval of PBT in Python, OOPSLA 2025 | High | B14.2 |
| 05 | Ding & Le Goues, OSS-Fuzz bugs, MSR 2021 | High | B14.2/B14.1 |
| 06 | Forsgren/Humble/Kim, Accelerate + DORA | Mod-High | B14.1 |
| 07 | NIST SP 800-218 SSDF v1.1 (+800-218A) | High | B14.3 |
| 08 | OWASP SAMM & DSOMM | Mod-High | B14.3 |
| 09 | McCabe, Cyclomatic Complexity, IEEE TSE 1976 | High | B14.3 |
| 10 | Cohen/SmartBear Cisco code-review study | Low-Mod | B14.3 |
| 11 | SAST effectiveness empirical (FP/FN studies) | Mod-High | B14.3 |
| 12 | Mutation testing in practice (tooling/adoption) | Moderate | B14.2 |

See SYNTHESIS.md for the surveyed space, verdicts, and the L2.B14 recommendation.
