# BEST-PARTS — Heuristic Evaluation Method, Math Model & Severity

## What AutoFirm should ADOPT and why

1. **The 3-5 independent-evaluator panel as the design-review agent count.** ADOPT: spawn
   3-5 independent evaluator agents (different prompts/personas, no shared transcript) to review
   each client UI, then aggregate. Build implication: directly sets the fan-out count for the
   CDO's visual-verification loop (CLAUDE.md §4.9.5) — grounded in the Poisson model, not guesswork.
   Independence is mandatory (agents must not see each other's findings first) to avoid correlated
   misses.

2. **The Poisson model as a coverage stop-rule.** ADOPT ProblemsFound(i)=N(1-(1-L)^i) with
   L~=0.34 to *estimate remaining defects* and decide when enough evaluators have run. With L=0.34:
   1 evaluator ~34%, 3 ~71%, 5 ~88%. Build implication: the design-review loop has a quantitative
   exit criterion (e.g. run agents until estimated coverage >= a threshold), feeding `evidence/`
   with a real number instead of "looks done."

3. **The 0-4 severity scale as the defect-triage contract.** ADOPT verbatim. Build implication:
   every evaluator-agent finding carries a 0-4 severity; a UI cannot pass the Definition-of-Done
   with any open severity-3 or severity-4. This makes the §4.9.7 gate machine-enforceable and
   maps cleanly to the autoresearch fix loop (fix highest-severity first).

4. **severity = frequency x impact x persistence as the scoring rationale.** ADOPT so evaluator
   agents justify each rating against the three factors (not a vibe number) — satisfies the
   "explain every decision" bar (CLAUDE.md §3.11).

5. **The method IS the competitive-teardown method (L1.B13.1).** ADOPT heuristic evaluation as
   the structured lens for tearing down category-leading products: rate competitor flows against
   H1-H10, record what they do well, distil principles (not pixels). Build implication: the design
   brief's competitive research (§4.9.2) is a heuristic evaluation of competitors, producing a
   structured pattern library rather than screenshots.

## What AutoFirm should REJECT / DEFER

- **REJECT a single evaluator agent.** The model proves one evaluator finds only ~34% — a single
  reviewer is provably insufficient; always panel.
- **DEFER weighting lambda per domain.** Use L~=0.34 as the general default; only re-estimate from
  observed early-evaluator data if a specific client product warrants it (generality, §3.9).

## Concrete build implication
This source operationalizes the entire design-review loop: a 3-5 independent evaluator-agent panel,
scoring each finding 0-4 with frequency/impact/persistence rationale, using the Poisson coverage
estimate as the stop-rule, and applying the same lens as a teardown method against competitors.
It turns CLAUDE.md §4.9.5's "different agent judges" into a quantified, defensible protocol.
