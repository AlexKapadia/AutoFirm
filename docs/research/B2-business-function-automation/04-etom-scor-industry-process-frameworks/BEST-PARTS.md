# BEST-PARTS — eTOM & SCOR → AutoFirm

## ADOPT
- **The "generic core + industry overlay" architectural pattern.** eTOM (telecom) and SCOR
  (supply chain) demonstrate that a *generic* process taxonomy is specialized per industry by a
  dedicated overlay — exactly the parameterization AutoFirm needs for the B12 "any industry"
  requirement. **Build implication:** AutoFirm's taxonomy is `APQC cross-industry core` +
  pluggable `IndustryOverlay` modules (telecom→eTOM, manufacturing/retail logistics→SCOR,
  banking/healthcare→APQC industry PCFs). The decomposition engine selects the overlay from the
  client's NAICS/GICS code (ties to L1.B12.2).
- **SCOR's built-in metric layer (reliability, responsiveness, agility, cost, asset efficiency)**
  is a reusable, industry-standard KPI scaffold AutoFirm can attach to *Deliver/Operations*
  activities — feeding B11 operations modeling and the `evidence/` showcase with real,
  citable operational KPIs rather than invented ones.
- **eTOM's FAB (Fulfillment, Assurance, Billing) end-to-end grouping** is a clean model for how
  AutoFirm should organize *customer-facing operational flows* into end-to-end agent pipelines
  rather than siloed steps (matches the horizontal-process principle from APQC).

## REJECT / use-with-care
- **Reject adopting eTOM or SCOR as the *primary* taxonomy.** Each is domain-bound (telecom /
  supply-chain) and would overfit AutoFirm to one industry — a direct §3.9/DEPTH-RUBRIC §6
  violation. They are *overlays*, never the spine.
- **Reject SCOR's "Return"/physical-logistics emphasis for digital-only clients** (SaaS,
  marketplace) — those processes are empty there. The overlay must be optional and degrade
  gracefully (consistent with the Porter "allow-empty-activities" rule in source 01).

## Concrete build implication
- Component: `function_decomposition/industry_overlays/` with `etom_overlay.py`, `scor_overlay.py`, plus a `select_overlay(naics_or_gics_code)` resolver.
- Test it drives: a generality test that the telecom and discrete-manufacturing B12 rows pick up their respective overlays while the B2B-SaaS row uses the bare APQC core (no physical-logistics processes) — proving the overlay mechanism is parameterized, not hard-coded.
