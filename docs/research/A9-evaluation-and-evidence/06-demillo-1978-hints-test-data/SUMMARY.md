# SUMMARY — Hints on Test Data Selection: Help for the Practicing Programmer

## Full citation
- **Title:** Hints on Test Data Selection: Help for the Practicing Programmer
- **Authors:** Richard A. DeMillo, Richard J. Lipton, Frederick G. Sayward
- **Year:** 1978
- **Venue:** Computer (IEEE Computer), Vol. 11, No. 4, pages 34-41
- **DOI/URL:** 10.1109/C-M.1978.218136 | https://www.scirp.org/reference/referencespapers?referenceid=2763951

## Questions informed
- **L1.A9.3** Mutation testing & test-adequacy theory -- the FOUNDATIONAL primary source.

## GRADE tier: High (foundational primary)
The original paper that introduced mutation testing and its two founding hypotheses. Primary,
seminal, universally cited. No down-rate; it is the source of record for the Competent Programmer
Hypothesis and the Coupling Effect.

## Key claims (founding hypotheses, stated faithfully)

### Competent Programmer Hypothesis (CPH)
Programmers are competent: they "tend to develop programs close to the correct version." The
faults that occur in such programs are therefore assumed to be "merely a few simple faults which
can be corrected by a few small syntactical changes." => mutation operators apply single small
syntactic changes to model realistic faults.

### Coupling Effect
Stated by the authors as: "Test data that distinguishes all programs differing from a correct one
by only simple errors is so sensitive that it also implicitly distinguishes more complex errors."
i.e. a test set that detects all *simple* faults will, with high probability, also detect *complex*
faults. (Later operationalized/empirically studied by Offutt 1992 -- see source 07.)

### Core method (as introduced)
Create *mutants* of a program by single syntactic changes; a test set is adequate to the extent it
*kills* (distinguishes by output) these mutants. A test set that kills mutants is, by the coupling
effect, also good at catching real complex faults -- so the mutant-kill rate is a measure of test
*adequacy*, not merely of code execution.

## Reproducibility note
The CPH and Coupling-Effect statements are reproduced as quoted by the Jia & Harman survey
(source 07) and the University of Luxembourg mutation-testing theory page, both attributing them
to DeMillo, Lipton & Sayward 1978. The exact wording of the Coupling Effect quote is the
load-bearing statement; cross-checked across two independent secondary sources that quote the 1978
primary. Page locator: Computer 11(4):34-41.
