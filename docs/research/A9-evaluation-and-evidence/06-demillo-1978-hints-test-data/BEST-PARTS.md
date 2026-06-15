# BEST-PARTS — DeMillo, Lipton & Sayward 1978

## ADOPT

1. **Adopt the Coupling Effect as the THEORETICAL JUSTIFICATION for CLAUDE.md's mutation mandate.**
   CLAUDE.md §3.6 demands "tests with teeth" proven by mutation testing; this 1978 paper is *why*
   that works -- a suite that kills simple mutants will, by the coupling effect, also catch complex
   real faults. *Build implication:* AutoFirm's QA doctrine can now cite the founding theory, not
   just the tooling: mutation score is a *principled* adequacy measure, not an arbitrary gate.

2. **Adopt the CPH framing for AutoFirm-generated code.** Agent-written code, like human code, is
   "close to correct" with small faults -- exactly the fault class mutation operators model.
   *Build implication:* standard first-order mutation operators (arithmetic, relational, logical,
   statement-deletion) are an appropriate fault model for the code AutoFirm ships for clients
   (feeds L1.B14.2 client-product testing strategy).

3. **Adopt "adequacy != execution".** The paper's core insight is that killing mutants measures
   whether tests *distinguish wrong programs*, not merely run lines -- the conceptual root of
   "coverage necessary but not sufficient." *Build implication:* AutoFirm's gate is mutation-kill,
   corroborated empirically by Google (source 09) and Cao et al. (source 02).

## REJECT / DEFER

- **REJECT** nothing -- this is foundational theory. The one caveat: the CPH/coupling effect are
  *hypotheses* with strong but not absolute empirical support; AutoFirm relies on them as
  well-validated working assumptions (Offutt 1992, Andrews 2005 -- sources 07/08), not as proven
  theorems. Documented as such.
- **DEFER** higher-order mutation (combining faults) to source 07 -- the 1978 paper is first-order.

## Why this matters to AutoFirm
This is the bedrock primary source for L1.A9.3. It lets AutoFirm justify its entire "tests with
teeth / mutation-tested" doctrine (CLAUDE.md §3.6) from first principles with an exact, attributed
quotation of the Coupling Effect -- the single most important theoretical claim underpinning the
QA bar.
