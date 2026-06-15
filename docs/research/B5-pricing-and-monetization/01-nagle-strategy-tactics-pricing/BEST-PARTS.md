# BEST PARTS — Nagle, Hogan & Zale, Strategy and Tactics of Pricing

## ADOPT
- **The three-orientation taxonomy as AutoFirm's pricing-strategy decision root.** The pricing
  playbook (L2.B5) should branch first on orientation: cost-plus (floor only), competition-based
  (anchor), value-based (target). Build implication: a `PricingStrategy` enum + a decision module
  that selects/blends orientations per company, with cost-plus only ever the **floor**, never the
  default target. Rationale: cost does not determine WTP (claim 1-2).
- **The value cascade as the playbook's ordered pipeline.** AutoFirm's pricing function runs in the
  cascade order: quantify value -> communicate value -> design price structure -> set level ->
  manage realization. Build implication: pipeline stages map to ordered modules; "set price level"
  is a *late* stage that consumes a quantified value model, never stage one.
- **Segmentation + fences as a first-class output.** The playbook must emit segment-specific
  price/value metrics and self-selection fences, not a single list price. This is the bridge to
  second-degree price discrimination (source 03) and tiered SaaS (source 11).
- **Value communication as a required deliverable.** A price recommendation is incomplete without a
  value-justification artifact (ties to B15 artifact generation). Build implication: pricing output
  schema includes a `value_communication` field with the EVC drivers (source 02) that justify it.

## REJECT / DEFER
- **Reject cost-plus as a default target.** Useful only as a margin floor and sanity check; never
  the recommended price. (Corroborated by Simon-Kucher, source 12: cost-plus leaves money on the
  table.)
- **Defer** verbatim negotiation/"manage price" tactics (claim 3 stage v) -> these are sales-motion
  details that belong in B8 (sales), not the pricing-level engine.

## Build implication (concrete)
Drives the **L2.B5 pricing playbook's top-level control flow** and its output contract:
`{strategy, segment, value_model (EVC), price_structure, price_level, value_communication}`. The
cascade ordering becomes an invariant the playbook's tests assert (value model must exist before a
level is emitted -- a "level without value model" is a defect).
