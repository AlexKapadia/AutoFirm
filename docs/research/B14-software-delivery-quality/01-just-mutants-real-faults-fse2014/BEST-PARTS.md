# BEST-PARTS — Just et al. FSE 2014

## ADOPT
1. **Mutation score, not coverage, is the acceptance signal for client code.** This is the empirical backbone of CLAUDE.md §3.6 ("the acceptance signal is the MUTATION SCORE, not the pass rate"). 73% of real faults coupling to mutants + mutation correlating with real-fault detection *more strongly than coverage* justifies making **mutation-score a hard gate** in the AutoFirm client-delivery engine (L2.B14), with coverage as a *necessary-but-not-sufficient* secondary gate.
   - **Build implication:** the per-client CI pipeline runs mutation testing (PIT/Stryker/mutmut per language) and **fails the build on surviving mutants in security-/correctness-critical modules**; each survivor spawns a "write a harder test" task (iterate-to-perfection loop).
2. **Control for coverage when measuring test strength.** Mirror the paper's method: only count a mutant as a meaningful survivor if the line is *covered*; an uncovered mutant is a coverage gap, a covered-but-surviving mutant is a *test-strength* gap. AutoFirm should report these two failure modes separately so the fix is correctly routed (add a test vs. strengthen an assertion).
3. **Don't treat mutation as complete.** ~27% of real faults were uncoupled. AutoFirm must *combine* mutation with property-based + fuzz + adversarial tests (sources 03–05) rather than relying on mutation alone.

## REJECT / BOUND
- **Reject** "100% line coverage = done" as a quality claim anywhere in client delivery — this paper is the direct evidence it is misleading.
- **Bound:** subjects are human-written Java OSS; AutoFirm ships polyglot, agent-written code. The coupling mechanism generalizes, but mutation *operator sets* are language-specific — adopt per-language mutators, don't assume Java operators transfer.

## Concrete artifact this drives
- A `mutation-gate` CI stage contract: `{ language, tool, mutation_score, surviving_mutants[], covered_survivors[] }`; gate = `covered_survivors == 0` on critical modules, `mutation_score >= threshold` elsewhere. Feeds the `evidence/` mutation-score chart (CLAUDE.md §3.10).
