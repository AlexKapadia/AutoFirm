# BEST-PARTS — Cao & Yang unlearning + right-to-erasure

## ADOPT
- **VF is legally mandatory, not optional polish.** GDPR Art. 17 + CCPA §1798.105 make verifiable
  erasure a hard compliance control. Build implication: AutoFirm's memory layer treats a delete that
  cannot emit a non-recoverability proof as a **fail-closed defect** (CLAUDE.md §5.6) — refusing to
  report "deleted" until the proof is produced and written to the A6 audit log.
- **Two-lineage corroboration for "deletion-in-weights is hard."** Cao–Yang (summation/SQ form) and
  SISA (sharded retraining, folder 15) reach the same conclusion by *independent* mechanisms: exact
  in-weight forgetting requires special training-time structure AutoFirm cannot impose on a hosted
  model. This independence is what lifts VF to a properly corroborated ≥3-primary claim.
- **Borrow the "lineage" framing for provenance.** Cao–Yang forget a sample's *lineage*; AutoFirm's
  PV primitive (folder 12) already tracks write-lineage — so a delete can walk the lineage and purge
  every derived record (reflections/insights distilled from the deleted source), not just the row.

## REJECT / DEFER
- **Reject summation/SQ-form unlearning as AutoFirm's path** — like SISA it needs control over the
  learner's internals; infeasible for a hosted Claude model. Adopt external-store exact deletion
  instead. Cao–Yang's role here is *evidentiary*, establishing the problem these primitives solve.

## Build implication (concrete)
Closes the A4.4 source-count gap: VF now rests on **three independent primaries** —
SISA (15, IEEE S&P 2021), Cao–Yang (16A, IEEE S&P 2015), and GDPR Art. 17 (16B, primary law) —
plus the two surveys (12, 14). Drives a concrete VF test: delete → assert exact + near-duplicate
unreachable → assert lineage-derived records purged → assert audit proof emitted.
