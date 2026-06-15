# BEST-PARTS — Anderl et al. (2016) Markov attribution

## ADOPT
- **Markov / removal-effect attribution as AutoFirm's default multi-touch attribution method** (over heuristic last/first/linear-click). It is data-driven, peer-reviewed, interpretable, and proven cross-industry. **Build implication:** an `attribution` module that ingests touchpoint paths -> builds a transition matrix -> computes normalized removal effects per channel. Deterministic given the path data (testable for determinism per CLAUDE.md 5.5).
- **Removal effect as the credit formula** (reproduced exactly in SUMMARY). **Build implication:** this is a safety/correctness-critical formula -> needs >=3 corroborating sources (Anderl 2016 + Shapley equivalence folder 06 + MMM/incrementality cross-check folder 07/08) and an exact unit test on a tiny hand-computable graph (zero numerical error, CLAUDE.md 3.11).
- **Heuristic-model rejection is evidence-backed.** **Build implication:** the playbook must NOT ship last-click as the basis for budget reallocation; it may report it only as a baseline for comparison.

## REJECT
- **Reject treating ANY click-path attribution (Markov OR Shapley) as causal.** Anderl et al. measure *correlational* credit on observed paths; it does not establish that a channel *caused* incremental conversions. This is the central limitation — resolved by pairing attribution with incrementality experiments (folder 07) and MMM (folder 08).

## Why
Gives AutoFirm a rigorous, interpretable, cross-industry-general attribution default with an exact, testable formula — while explicitly flagging the causality gap that the experiment/MMM layers must close.
