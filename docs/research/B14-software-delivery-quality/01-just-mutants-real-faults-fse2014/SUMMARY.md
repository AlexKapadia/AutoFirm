# SUMMARY — Are Mutants a Valid Substitute for Real Faults in Software Testing?

## Full citation
- **Title:** Are Mutants a Valid Substitute for Real Faults in Software Testing?
- **Authors:** Rene Just, Darioush Jalali, Laura Inozemtseva, Michael D. Ernst, Reid Holmes, Gordon Fraser
- **Year:** 2014
- **Venue:** Proceedings of the 22nd ACM SIGSOFT International Symposium on the Foundations of Software Engineering (FSE 2014), pp. 654-665. DOI: 10.1145/2635868.2635929
- **URL/DOI:** https://dl.acm.org/doi/10.1145/2635868.2635929 ; author copy https://homes.cs.washington.edu/~rjust/publ/mutants_real_faults_fse_2014.pdf

## Questions it informs
- **L1.B14.2** (testing strategy: mutation testing for client products)
- Cross-feeds **L1.A9.3** (mutation testing and test-adequacy theory).

## Core problem
Mutation testing injects small artificial faults (mutants); a suite's mutation score = fraction of mutants it detects (kills). The field assumed via the coupling effect (DeMillo et al. 1978) that killing mutants implies catching real faults, but this had only been shown between mutants, not against real developer-fixed faults. This paper tests that assumption empirically.

## Method and scale (exact)
- **357 real faults** from **5 open-source applications** totalling **321,000 lines of code**. (Paper abstract; corroborated by Just UW project page and CS7580 lecture notes.)
- Mutants generated with the Major framework; about **230,000 mutants** total (about **644 per fault** average per CS7580 lecture notes).
- Explicitly **controlled for code coverage** as a confound (compared only mutants covered by all suites), separating reachability from detection.

## Key findings (exact)
1. **73% of the real faults were coupled** to mutants from commonly used operators: a test killing the coupled mutants also detected the real fault.
2. **Mutant detection correlates with real-fault detection, and more strongly than code coverage does.**
3. The remaining ~27% of faults were **not coupled** to standard mutants, motivating additional operators and non-mutation tactics.

## GRADE tier
**High.** Peer-reviewed top SE venue (FSE), controlled empirical study on real faults, large N. Up-rated for sample size and explicit confound control. Slight down-rate for indirectness to agent-written code; coupling mechanism is author-agnostic.

## Reproducibility note
Subjects/faults are the Defects4J-style corpus; Major is open source. The 73% and 357/5/321 kLOC figures are cross-checked against three independent renderings (ACM DL abstract, Just UW author page, NEU CS7580 lecture notes).
