# BEST-PARTS — Powell, Lawson & Baker (Operational Spreadsheet Errors)

## ADOPT
- **Independent empirical backing for the audit gate.** This is a *second* peer-reviewed research
  group (Dartmouth SERP) confirming Panko's prevalence/taxonomy — so the safety-critical claim "any
  generated model is error-prone until independently audited" now rests on ≥3 independent sources
  (Panko 02 + Powell/Lawson/Baker 14 + Grossman&Ozluk 01), meeting DEPTH-RUBRIC §1 for a
  correctness-critical claim.
- **Tools-beat-humans → mandate automated auditing, not review-by-eye.** Automated inspection
  caught all but ~17.8% of errors and outperformed unaided human inspection. → The
  `spreadsheet_audit_gate` MUST be a programmatic formula-graph analysis (openpyxl), with human/LLM
  review as a supplement, never the primary control (reinforces Panko's confidence-gap conclusion).
- **Impact-weighting insight for test design.** Most errors are low-impact; a minority hit
  "key aspects." → The audit gate should not just count errors but **flag errors on output/decision
  cells** (the DCF result, the valuation, the headline metric) with higher severity — an
  impact-ranked error report, mirroring the study's finding.
- **Two-stage protocol as the engine's audit shape:** run automated inspection first, then targeted
  human/LLM review of *only* the residual flagged formulas — efficient and evidence-backed.

## REJECT
- **Reject treating a clean visual pass as acceptance** — confirmed errors lived in 14/25 real,
  in-production operational spreadsheets that their owners believed were correct.
- **Reject one-true-taxonomy rigidity** — the authors show categorization is purposive; AutoFirm's
  error-class matrix (mechanical / logic / omission / hard-coding) is a *checklist for coverage*,
  not an ontological claim.

## BUILD IMPLICATION
Component: hardens `spreadsheet_audit_gate`. New behaviors: (1) automated-first, residual-only-human
two-stage audit; (2) **impact-ranked** error severity — errors touching output/decision cells are
escalated; (3) explicit omission + hard-coding checks (the two classes this group refined). Feeds
`evidence/` with an error-class kill report whose severity is weighted by whether the injected fault
reached an output cell — proving the gate catches the *high-impact* minority, not just totals.
