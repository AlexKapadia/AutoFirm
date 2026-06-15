# BEST-PARTS — Ulwick, Outcome-Driven Innovation

## ADOPT
1. **Adopt the Opportunity Algorithm as AutoFirm's deterministic opportunity-PRIORITIZATION formula.**
   `Opportunity = Importance + max(Importance - Satisfaction, 0)` is exact, auditable, and
   reproducible — ideal for AutoFirm's deterministic core (CLAUDE SS3.5 deterministic guardrails,
   SS3.11 explain-every-decision). Each opportunity score self-justifies (which outcome, what
   importance, what satisfaction gap). Build implication: an `OpportunityScore` pure function with
   exact unit tests (SS3.6 zero numerical errors on deterministic paths).
2. **Adopt desired-outcome statements as the measurable form of a JTBD.** They convert Christensen's
   conceptual job (source 05) into testable, scoreable hypotheses for the ledger — bridging *what to
   test* into *how much it matters*.
3. **Adopt the "important-but-unsatisfied" targeting rule** as the opportunity-selection heuristic:
   rank outcomes by opportunity score, pursue the top unmet ones. Generalizes across the industry
   panel (any job, any industry, same math).

## REJECT / DEFER
- **Reject the vendor 86%-success figure as evidence** — Strategyn self-reported, Low tier, conflict
  of interest. Cite only with caveat; never use to justify a design choice.
- **Reject sole reliance on survey importance/satisfaction** for a fully autonomous platform —
  AutoFirm may not always have a clean survey panel; the formula stays, but the *inputs* must be
  sourced from real public/permitted data (ties to L1.B4.4 public-data boundary), with a fail-closed
  default when inputs are missing.
- **Defer the full ODI 8-step process** to L2.B3 design; adopt the formula + outcome-statement
  concept now.

## Build implication
A pure, exact `opportunity_score(importance, satisfaction)` function (deterministic, unit-tested to
the decimal) is a concrete deliverable for L2.B3. It is the quantitative ranking layer atop the
JTBD/job inputs and feeds directly into evidence/ (rank charts, opportunity heatmaps).
