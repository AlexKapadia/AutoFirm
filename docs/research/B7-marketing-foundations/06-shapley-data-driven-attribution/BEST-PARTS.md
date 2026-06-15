# BEST-PARTS — Shapley / data-driven attribution

## ADOPT
- **Shapley value as the second corroborating data-driven attribution method** alongside Markov removal-effect. Because the two are marginal-contribution cousins and usually agree, running BOTH gives AutoFirm a cross-check: large divergence flags a data/modeling problem. **Build implication:** attribution module computes Shapley AND Markov credit; a QA test asserts they agree within tolerance on synthetic ground-truth paths, else fail-closed.
- **Exact Shapley formula** (reproduced in SUMMARY) as a correctness-critical, unit-tested function (hand-computable on 2-3 channels for zero-numerical-error verification, CLAUDE.md 3.11).
- **Heuristic models retained ONLY as labeled baselines** for the evidence showcase (showing how much last-click misallocates vs. data-driven), never as the decision basis.

## REJECT
- **Reject Shapley alone for sequenced journeys** — it discards order; pair with Markov (folder 05) which preserves sequence.
- **Reject any attribution (Shapley/Markov/heuristic) as a causal ROI claim.** All are observational. Budget decisions must be validated by incrementality experiments (folder 07) / MMM (folder 08). This is the hard line for institution-grade marketing measurement.

## Why
Two independent data-driven methods that agree give a robust, testable attribution signal; keeping heuristics as baselines and refusing causal claims keeps AutoFirm honest and audit-defensible.
