# BEST-PARTS — Spreadsheet Engineering Methodologies

## ADOPT
- **Treat every generated financial model as engineered software, not a one-off worksheet.** The artifact-generation engine (L2.B15) must apply a *named methodology*, not ad-hoc cell-filling. → Drives a `spreadsheet_model_builder` component that enforces a fixed structural contract.
- **The convergent three-zone layout: Inputs → Calculations → Outputs, separated** (own sheets/regions, colour-coded inputs). This is the single most-corroborated rule across FAST, Operis, SSRB. → Test: every generated workbook must have a distinct, labelled assumptions block whose cells are the *only* hard-coded numbers.
- **Row-consistent formulas (copy-coherence):** one formula logic per row, filled across all periods; no per-cell exceptions. → Property test: for any calculation row, the relative formula is structurally identical across the time axis (a mutation that breaks one cell must be caught).
- **No embedded constants in calculation formulas** — every number traces to a labelled input cell. → Determinism/audit test feeding `evidence/`.

## REJECT (for now)
- **Picking one single methodology as the only option.** The paper shows three valid convergent standards; AutoFirm should adopt the convergent *principles* (layout, separation, consistency) which all three share, rather than over-committing to one brand's idiosyncrasies (e.g. Operis's heavy named-range style, which can hurt machine-generation readability). Defer brand choice to the L2 experiment.

## BUILD IMPLICATION
Component: `financial_model_builder` with a **structural contract** — (1) assumptions sheet (only source of constants), (2) calculation sheets (row-consistent live formulas referencing assumptions), (3) output/statement sheets. Contract is enforced by adversarial tests (no orphan constants; row-formula consistency; live-formula not dead-value). Ties model logic to L1.B4.1 (3-statement/DCF).
