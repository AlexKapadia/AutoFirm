# BEST-PARTS — Panko Spreadsheet Errors

## ADOPT
- **Treat any agent-generated spreadsheet as ~90%-likely-to-contain-an-error until proven otherwise.** This is the empirical justification for mandatory automated audit of generated models (CLAUDE §3.6 tests-with-teeth). → Drives a `spreadsheet_audit` gate that must run on every generated workbook before delivery.
- **Error taxonomy as a test matrix:** explicitly hunt **mechanical** (wrong cell ref), **logic** (wrong formula), and **omission** (missing line item / missing period) errors. Omission is hardest → needs a *completeness* check against the model contract (every statement line present, every period filled).
- **The confidence gap is the core risk:** the generator's own "looks right" is worthless (humans estimate 18% vs actual 86%). → Acceptance must come from an *independent* evaluator/audit pass, never the generator's self-assessment (generator/evaluator split, CLAUDE §4.9).

## REJECT
- Relying on visual/manual review alone — even group review (triads) still left **27%** of spreadsheets wrong. Manual review is necessary-not-sufficient; automated formula-graph auditing is required.

## BUILD IMPLICATION
Component: `spreadsheet_audit_gate` running independently of the builder, checking (a) no orphan hard-coded constants, (b) row-formula consistency, (c) statement completeness (omission defence), (d) balance-sheet ties / known identities (e.g. Assets = Liabilities + Equity exact to the unit — CLAUDE §3.11 zero-numerical-error). Feeds `evidence/` with an error-class kill report (mutation: inject mechanical/logic/omission faults, confirm the gate catches each).
