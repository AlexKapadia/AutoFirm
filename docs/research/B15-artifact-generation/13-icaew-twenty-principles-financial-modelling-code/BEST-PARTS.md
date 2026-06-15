# BEST-PARTS — ICAEW Twenty Principles + Financial Modelling Code

## ADOPT
- **Treat the FAST style contract as standards-convergent, not single-vendor.** ICAEW's
  independently-authored P10/P12/P13/P14/P15 match the FAST core (separate inputs/workings/outputs;
  consistent formulae; short/simple formulae; no embedded constants; calculate-once-then-reference).
  This closes the prior B15.1 gap where the "three convergent standards" claim leaned on FAST (03)
  + Grossman & Ozluk (01) alone — now corroborated by a chartered-accountancy body that *also*
  formally recognizes FAST. → The `financial_model_builder` style contract is justified by ≥3
  independent authorities (FAST 03 + Grossman&Ozluk 01 + ICAEW 13), satisfying DEPTH-RUBRIC §1 for
  this architecture-level claim.
- **Add ICAEW-specific machine-checkable rules the audit gate should enforce:**
  - P7 "include a documentation sheet" → generated workbooks must emit an assumptions/README sheet.
  - P14 "never embed in a formula anything that might change" → orphan-constant lint (already
    planned via Panko) now has a second standards citation.
  - P19/18 "build in checks, controls and alerts" + "test rigorously" → generated models should
    ship with built-in **balance/integrity check rows** (e.g. A=L+E flag cell), not just external
    audit — the model self-reports its own ties.
  - P17 "backup and version control" → generated artifacts are committed to the private workspace
    with provenance (ties to L1.A6.4).
- **Use ICAEW grouping (environment / build / risk-and-controls) as the lint-report sectioning** so
  the transparency report maps cleanly onto a recognized professional rubric, not a bespoke one.

## REJECT
- **Rejecting any single-standard exclusivity:** do not hard-code one vendor's idiom (e.g. Operis
  named-ranges) as the only valid style — ICAEW deliberately abstracts to commonly-held principles;
  the engine encodes the convergent core and treats house-style as per-company config (generality,
  CLAUDE §3.9).

## BUILD IMPLICATION
Component: strengthens `spreadsheet_audit_gate` and `financial_model_builder`. The style contract
now cites three independent standards bodies; new checks added — documentation-sheet presence (P7),
built-in integrity-check rows (P19), and version/provenance on save (P17). Feeds `evidence/` with a
"standards-convergence" table showing each enforced rule mapped to FAST + Grossman&Ozluk + ICAEW
principle numbers, demonstrating the rule set is not overfit to one source.
