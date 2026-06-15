# SUMMARY — An Analysis and Survey of the Development of Mutation Testing

## Full citation
- **Title:** An Analysis and Survey of the Development of Mutation Testing
- **Authors:** Yue Jia, Mark Harman
- **Year:** 2011
- **Venue:** IEEE Transactions on Software Engineering (TSE), Vol. 37, No. 5, pages 649-678
- **DOI/URL:** 10.1109/TSE.2010.62 | https://ieeexplore.ieee.org/document/5487526

## Questions informed
- **L1.A9.3** Mutation testing & test-adequacy theory -- the canonical SURVEY (PRIMARY/High).

## GRADE tier: High
Peer-reviewed IEEE TSE (flagship SE journal), the standard reference survey of mutation testing
(>2,000 citations). Authoritative for definitions, formulae, hypotheses, and cost-reduction
taxonomy. No down-rate.

## Key claims / definitions (reproduced faithfully)

### Founding hypotheses (attributed)
- **Competent Programmer Hypothesis (CPH):** introduced by DeMillo, Lipton & Sayward (1978) --
  programmers write programs "close to the correct version," so faults are small syntactic
  deviations (modeled by single-change mutants). (See source 06.)
- **Coupling Effect:** "complex faults are coupled to simple faults in such a way that a test data
  set that detects all simple faults in a program will detect a high percentage of the complex
  faults." -- the operational form, attributed to Offutt (1989/1992) extending DeMillo et al. 1978.

### Mutation score / adequacy (formula reproduced)
    MS = (# killed mutants) / (# non-equivalent mutants)
The mutation (adequacy) score is the ratio of killed mutants to the total number of
**non-equivalent** mutants. A test set is "mutation-adequate" when MS = 1 (all non-equivalent
mutants killed).

### Equivalent mutants & the Equivalent Mutant Problem (EMP)
An *equivalent mutant* is "syntactically different but functionally equivalent to the original
program" -- it can never be killed because it produces identical output on all inputs. Detecting
equivalence is **undecidable in general** (reduces to the program-equivalence problem), so the EMP
is a major practical cost driver and must be handled (excluded from the denominator).

### Cost-reduction taxonomy ("do fewer / do faster / do smarter")
- **Selective mutation:** use a reduced, high-yield set of mutation operators (Offutt's "do fewer").
- **Mutant sampling:** randomly sample a fraction x% of generated mutants.
- **Weak mutation:** check for an infected *internal state* after the mutated component executes,
  rather than requiring the fault to propagate to program output (strong mutation). Cheaper.
- **Higher-Order Mutation (HOM):** mutants formed by >1 fault; useful HOMs ("subsuming HOMs") can
  be harder to kill and reduce mutant count while preserving test strength.

## Reproducibility note
Mutation-score formula and the CPH/Coupling-Effect attributions extracted from the Univ. of
Luxembourg mutation-testing theory page (a mirror maintained by mutation-testing researchers) and
cross-referenced to the Jia & Harman TSE survey metadata. MS = killed/non-equivalent is the
safety-critical formula (DEPTH-RUBRIC §3.5); reproduce exactly from TSE 37(5) before coding the
gate. Definitions of selective/weak/sampling/HOM are standard and consistent across the survey.
