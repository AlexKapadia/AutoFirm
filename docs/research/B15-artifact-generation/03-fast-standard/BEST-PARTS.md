# BEST-PARTS — FAST Standard

## ADOPT
- **FAST as the default style contract for every generated financial model.** It is openly published, governed, and machine-encodable. → The `financial_model_builder` emits FAST-conformant workbooks by construction.
- **Encodable FAST rules → automated lints** (each becomes a test with teeth):
  - one consistent formula per calculation row (no per-cell breaks);
  - no hard-coded numbers inside calculation formulas (constants only in the labelled inputs block);
  - consistent colour-coding (inputs blue / calculations black) as a machine-checkable style;
  - short, readable formulas (cap formula nesting depth) over mega-formulas;
  - consistent time-axis (one period per column, filled across).
- **"Flexible" → driver-based design:** change an assumption cell and the whole model recomputes correctly. → Determinism/recompute test: perturb each driver, assert downstream cells change and identities still hold.
- **"Transparent" → every block labelled + documented**, so a human auditor (and the explanation report, CLAUDE §3.11) can trace any output to its drivers.

## REJECT
- The certification/training apparatus (FAST Level 1 Certificate) — irrelevant to programmatic generation; we adopt the *rules*, not the human-credential pathway.
- Over-committing to FAST's exact colour palette / cosmetic conventions as immutable — keep the *principle* (consistent semantic colour-coding) but allow the brand layer (source 09 IBCS) to govern final visuals.

## BUILD IMPLICATION
A `fast_lint` ruleset (orphan-constant detector, row-consistency checker, colour-code validator, formula-complexity cap) runs in the `spreadsheet_audit_gate`. This is the concrete, testable encoding of "institutional model-build standard" for L2.B15. Pairs with Panko's audit gate (source 02) and the OOXML/library layer (sources 05, 12).
