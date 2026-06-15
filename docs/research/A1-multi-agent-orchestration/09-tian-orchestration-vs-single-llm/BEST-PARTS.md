# BEST-PARTS — Tian et al. 2025 (Orchestration vs Single LLM)

## ADOPT
1. **Heterogeneous orchestration as a quality ceiling-raiser** — orchestrating *different* frontier
   models "matches or exceeds the strongest single model." *Build implication:* for AutoFirm's most
   critical verdicts (final gate sign-off, real-world validation §3.12), a cross-model consensus can
   exceed any single model — complements source 05 (mixed-model debate) and source 02 (Opus+Sonnet
   split). Cite for L1.A1.2 alongside 02/03.
2. **Hide running vote tallies and authorship in consensus** — the cited finding that "showing ongoing
   votes amplifies herding … premature consensus" and "revealing authorship increases self-voting"
   gives AutoFirm two **concrete anti-bias rules** for any voting/consensus gate: tally privately,
   anonymize authorship. Directly hardens the QA/North Star consensus mechanism against the MAST
   FM-3.1 "premature termination" failure (source 04).

## REJECT / caution
- **Consensus/voting as the PRIMARY topology for all work** — REJECT: consensus is a *verification/
  decision* mechanism over a shared question, not a way to run breadth-first parallel company work
  (use hierarchy, sources 02/03). Reserve it for high-stakes single decisions.
- **Trusting fast convergence** — REJECT as a success signal: speed can mean herding to a wrong
  premature consensus. AutoFirm must measure *correctness*, not convergence speed (ties A9 efficacy
  tests; CLAUDE.md §3.6).

## Build implication (concrete)
- A **cross-model, anonymized, private-tally consensus primitive** for AutoFirm's highest-stakes
  gates (final DoD, public-data validation). Encodes two cited anti-herding rules (anonymize
  authorship; hide running votes). Strengthens L1.A1.2 evidence that orchestration ≥ best single
  model, and feeds the L2.A9 evaluation design.
