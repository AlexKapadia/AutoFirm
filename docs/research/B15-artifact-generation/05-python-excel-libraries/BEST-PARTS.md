# BEST-PARTS — Python Excel Libraries

## ADOPT
- **XlsxWriter as the default engine for generating new financial models** (faster, richest formatting/charts/conditional-format/data-validation — needed for institution-grade FAST workbooks built from scratch). Primary writer in `financial_model_builder`.
- **openpyxl when AutoFirm must read-back or modify an existing client workbook** (audit, template fill, round-trip). The `spreadsheet_audit_gate` reads workbooks via openpyxl.
- **Live formulas, not dead values** — write formula strings (ontology "live formulas, not dead values"). Inputs are hard cells; everything else is a formula referencing them. Satisfies FAST "Flexible".
- **Mandatory recalculation step:** because neither lib has a calc engine, pipe generated workbooks through **LibreOffice headless** (or a pycel/formulas evaluator) to populate/verify cached values before delivery or PDF render. Closes the "blank cached value" correctness hole.

## REJECT
- **pandas to_excel for model-building** — it dumps values/tables, destroying the live-formula FAST structure. Fine for raw-data tabs only.
- **Storing computed numbers as dead values in the model body** — violates "live formulas" and FAST "Flexible"; an instant audit-gate fail.

## BUILD IMPLICATION
`financial_model_builder` = XlsxWriter writer + a FAST style layer + a LibreOffice-headless recalc/verify post-step; `spreadsheet_audit_gate` = openpyxl reader running `fast_lint` + Panko error-class checks. Recalc-verify feeds a determinism test (same inputs to identical cached outputs across runs, exact to the unit — CLAUDE §3.11).
