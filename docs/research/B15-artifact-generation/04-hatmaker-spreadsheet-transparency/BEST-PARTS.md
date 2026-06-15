# BEST-PARTS — Hatmaker Spreadsheet Transparency

## ADOPT
- **Make "transparency" a numeric gate, not a vibe.** Hatmaker's thesis legitimises encoding FAST's "Transparent" principle as *computable metrics* on the generated workbook. → `transparency_score` in the audit gate: e.g. proportion of formulas under a complexity threshold, proportion of constants living in the labelled input block, label-coverage of named blocks.
- **Transparency is auditor-facing:** the metric exists so an external auditor (a KKR-grade reviewer, CLAUDE §3.2) can verify compliance automatically — exactly AutoFirm's institution-grade bar.

## REJECT / DEFER
- **Do not reproduce a specific Hatmaker formula we could not verify.** Defer the exact metric definitions to the L2 build, where we will define our own auditable transparency metrics grounded in FAST rules (verifiable, not borrowed-uncited).

## BUILD IMPLICATION
Adds a `transparency_score` output to `spreadsheet_audit_gate` (component-level), reported in `evidence/` as a quantitative quality KPI per generated model — converting the qualitative "Transparent" FAST principle into a chartable number with a pass threshold.
