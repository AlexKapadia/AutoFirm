# SUMMARY — Mutation testing in practice (tooling and adoption)

## Full citation(s)
- **(A)** "Mutation Testing in Practice: Insights from Open-Source Software Developers," 2024. https://www.researchgate.net/publication/379072181
- **(B)** "Mutation testing in the wild: findings from GitHub," Empirical Software Engineering, 2022. https://www.researchgate.net/publication/362078955
- **(C)** Tool references: PIT (Java) https://pitest.org ; Stryker (JS/TS/C#/Scala) https://stryker-mutator.io/docs/ ; mutmut and cosmic-ray (Python).

## Questions it informs
- **L1.B14.2** (operationalising mutation testing for client code: which tools, what blocks adoption).

## Key findings (exact)
1. **Active real-world tooling by language**: **PIT/Pitest** dominates Java; **Stryker** family for JS/TS/C#/Scala; **mutmut**, **cosmic-ray**, **MutPy** for Python; **Infection** for PHP.
2. Developers find mutation testing **useful for improving test-suite quality, detecting bugs, and improving maintainability**; some teams report it **drives adoption of TDD**.
3. The **biggest impediment to adoption is performance/runtime cost** (mutation testing is expensive: it re-runs the suite per mutant). Mitigations: incremental/changed-files-only mutation, test selection, parallelism, sampling operators.
4. Study (B) finds many literature tools appear mainly in teaching repos, whereas PIT/Stryker/mutmut/Infection appear in actively developed projects - i.e. these are the production-grade choices.

## Implication
AutoFirm should run mutation testing **incrementally** (on changed code per PR) to control cost, with a full-suite mutation run at release gates, using the language-appropriate production tool.

## GRADE tier
**Moderate.** Peer-reviewed/empirical adoption studies plus authoritative tool documentation. Corroborates source 01/04 on why mutation score is the right signal and how to deploy it affordably.

## Reproducibility note
Tool capabilities are documented and reproducible; the performance-cost finding is consistent across both adoption studies and the tools' own docs (all ship incremental/selection features to address it).
