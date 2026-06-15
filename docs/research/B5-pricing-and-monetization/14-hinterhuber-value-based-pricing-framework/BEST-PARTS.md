# BEST-PARTS — Hinterhuber (2004, 2008) — what AutoFirm adopts

> Adopt/reject tied to cited evidence (DEPTH-RUBRIC §4-5). This folder hardens the value-based
> orientation already adopted in SYNTHESIS with peer-reviewed (IMM/Emerald) authority.

## ADOPT
- **A1. Value-based as default orientation, now peer-reviewed-anchored.** SYNTHESIS already adopts
  value-based pricing as the target; its authority moves from practitioner-only (01, 12) to
  **peer-reviewed Hinterhuber (2004) IMM 33(8)**. *Build implication:* orientation-selector module
  docstring cites Hinterhuber (2004); cost-plus stays floor-only, value-based stays target.
- **A2. The six-step method as the pricing-engine cascade.** Adopt Hinterhuber's sequence
  (objectives -> analyze elements -> economic-value analysis -> manage/communicate value -> range of
  profitable prices -> implement) as the **canonical ordering** of AutoFirm's pricing pipeline -
  an academic backbone for the SYNTHESIS architecture (orientation -> EVC -> segmentation ->
  WTP/optimizer -> output). *Build implication:* maps 1:1 onto pipeline stages; each stage's gate
  references the corresponding step.
- **A3. "Range of profitable prices", not a single point.** Hinterhuber's step (v) yields a price
  **range** bounded by cost floor and economic-value ceiling. *Build implication:* the engine emits
  an explainable [floor, EVC] band and selects within it (bounded by PSM, source 05) - reinforces
  invariant 2. Avoids false precision/overfitting (§3.9).
- **A4. Organizational barriers -> design requirements.** Hinterhuber (2008) names measurement,
  communication, and segmentation as the failure points. *Build implication:* AutoFirm hard-wires a
  value-communication artifact (source 01) and fence/segmentation checks (source 03) as REQUIRED
  pipeline outputs, not optional - because the literature says omitting them is why value-based
  pricing fails in practice.

## REJECT / DEFER
- **R1. REJECT one-shot price points without a value-analysis step.** Hinterhuber shows price level
  must follow economic-value analysis; the engine refuses to emit a price without a value model
  (SYNTHESIS invariant 1).
- **D1. DEFER detailed CVP (cost-volume-profit) modeling** to L1.B4.1 / L2.B4 (financial modeling);
  here it is only the cost floor input.

## Test / evidence hooks
- Pipeline-order test: stages execute in the Hinterhuber six-step order; out-of-order -> fail-closed.
- Output is a price **band** [floor, EVC] with the selected point inside it (range assertion).
- Citation test: orientation module references Hinterhuber (2004) DOI 10.1016/j.indmarman.2003.10.006.
