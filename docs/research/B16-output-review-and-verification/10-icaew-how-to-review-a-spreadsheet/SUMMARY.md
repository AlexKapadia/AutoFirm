# 10 — ICAEW, *How to Review a Spreadsheet* + *Twenty Principles for Good Spreadsheet Practice*

- **Author / org:** Institute of Chartered Accountants in England and Wales (ICAEW), Excel Community /
  Audit & Assurance Faculty.
- **Year:** *How to Review a Spreadsheet* (thought-leadership report); *Twenty Principles* (2024 ed.).
- **Link:** https://www.icaew.com/technical/technology/excel-community/how-to-review-a-spreadsheet ;
  https://www.icaew.com/technical/technology/excel-community/20-principles-for-good-spreadsheet-practice-2024-edition
- **Tier:** High — primary professional standard for *how a model is independently reviewed*.

## Faithful structured summary

ICAEW prescribes that a spreadsheet provided by a producer **should be reviewed by a third party**,
because **self-review only identifies 34%-69% of errors** (consistent with Panko 01). It defines a
**five-stage review protocol** (to satisfy ISA (UK) 500 on completeness/accuracy of information
produced by the entity, and to address misstatement risk from fraud or error):

1. **Initial review** — purpose, scope, provenance, version.
2. **Structural review** — separation of inputs/calculations/outputs; consistent layout.
3. **Data review** — input values reasonable, sources traced.
4. **Analytical review** — outputs sanity-checked against expectation / prior period.
5. **Detailed review** — cell-by-cell / formula-level checking (the most exhaustive).

The *Twenty Principles* supply the checkable structural rules (separate inputs/workings/outputs;
consistent formulae; no embedded constants; calculate-once-then-reference; documentation; integrity
checks) — i.e. the qualitative-error controls of the Panko-Halverson taxonomy (03).

## Best parts to take (for our gate) and why

1. **Independent third-party review is a professional *requirement*, not a nicety** (self-review
   34%-69%) — corroborates Panko (01) from a chartered-accountancy standards body, hardening the
   generator/evaluator mandate to >=3 independent sources (Panko 01 + Aurigemma/Panko 02 + ICAEW 10).
2. **The five stages map directly onto our deterministic checks**, giving the gate a professional
   provenance: structural -> `FAST_LINT`; data/round-trip -> `SPEC_ROUND_TRIP`; analytical ->
   `ACCOUNTING_IDENTITY` + sanity bounds; detailed -> `NUMERIC_RECOMPUTE`.
3. **Integrity-check rows + documentation/version** (Twenty Principles P7/P17/P19) are checkable and
   should be lint items — provenance is part of "ready for a human."
