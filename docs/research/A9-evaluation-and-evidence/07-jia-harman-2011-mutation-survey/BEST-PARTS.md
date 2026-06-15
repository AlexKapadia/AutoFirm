# BEST-PARTS — Jia & Harman 2011 (Mutation Testing Survey)

## ADOPT

1. **Adopt MS = killed / non-equivalent as AutoFirm's exact mutation-score gate.** CLAUDE.md §3.6
   demands "high mutation score (~100% on security-/correctness-critical modules)." *Build
   implication:* the eval harness computes MS with **equivalent mutants excluded from the
   denominator** (otherwise the gate is unachievable). Security/correctness modules: target MS=1
   (all non-equivalent mutants killed); other modules: a documented threshold. Surviving mutant ->
   write a harder adversarial test (CLAUDE.md §3.6/§3.7 loop).

2. **Adopt the EMP as a first-class, budgeted problem.** Equivalent mutants are undecidable in
   general; ignoring them silently corrupts the score. *Build implication:* the harness flags
   suspected-equivalent survivors for human/agent triage rather than counting them as failures --
   and records the equivalence rationale in the audit log (CLAUDE.md §5.6). Never inflate MS by
   quietly dropping un-triaged survivors.

3. **Adopt the cost-reduction taxonomy to make mutation feasible at AutoFirm scale.** AutoFirm runs
   continuously across many client codebases; full mutation is expensive. *Build implication:*
   - default to **diff-based + selective mutation** (mutate only changed/covered lines with a
     high-yield operator set) -- aligns with Google's diff-based approach (source 09);
   - use **weak mutation** for fast inner-loop feedback and **strong mutation** at the gate;
   - consider **subsuming higher-order mutants** to cut count without weakening teeth.

4. **Adopt the operator taxonomy as the fault model for client code (L1.B14.2).** Standard
   first-order operators (arithmetic/relational/logical/statement-deletion) for shipped software.

## REJECT / DEFER

- **REJECT** reporting MS over *all* mutants including equivalents (mathematically wrong; the
  paper's formula uses the non-equivalent denominator).
- **REJECT** mutant sampling as the *only* strategy for security-critical modules -- sampling
  trades thoroughness for speed; critical modules get full (selective) mutation, not a sample.
- **DEFER** specific tool choice (mutmut/cosmic-ray/Stryker, named in CLAUDE.md §3.6) to L2.A9 /
  L2.B14 -- this is a language-/stack-dependent engineering decision.

## Why this matters to AutoFirm
This is the authoritative High-tier reference for L1.A9.3. It gives AutoFirm the exact mutation-
score formula, the equivalent-mutant pitfall that must be handled to make the gate real, and the
cost-reduction menu (selective/weak/sampling/HOM) that makes mutation testing affordable at the
platform's always-on scale -- directly engineering CLAUDE.md §3.6 into a runnable gate.
