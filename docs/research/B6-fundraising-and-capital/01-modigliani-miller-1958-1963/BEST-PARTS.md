# BEST-PARTS — Modigliani & Miller (1958/1963)

## ADOPT

- **Use MM as AutoFirm's capital-structure baseline / sanity check.** The fundraising playbook's
  capital-structure module should start from "financing is value-neutral in a frictionless world",
  then add each friction explicitly. This forces every recommendation ("raise equity here", "take
  venture debt there") to be **justified by a named friction**, not by taste — exactly the
  evidence-driven discipline CLAUDE.md §3.4 demands.
- **Encode the tax-shield formula `V_L = V_U + T_C·D` as a deterministic, unit-exact computation**
  in the capital-structure analyzer. This is a deterministic financial path (CLAUDE.md §3.11) —
  zero numerical error required — and is directly testable with boundary cases (T_C = 0 ⇒ no shield;
  D = 0 ⇒ V_L = V_U).
- **Encode Prop. II `r_E = r_0 + (D/E)(r_0 − r_D)(1 − T_C)`** so the engine can show WHY adding debt
  raises the cost of equity — a self-justifying explanation per output (CLAUDE.md §3.11).

## REJECT (for the playbook's *recommendations*, not the theory)

- **Do not treat MM as a financing recommendation.** Its frictionless conclusion ("structure does
  not matter") is *false in practice* for AutoFirm's clients (startups face huge information
  asymmetry, no taxable profits early, real distress costs). Reject any logic that recommends
  ignoring instrument choice. MM is the *frame*, not the *answer*.
- **Reject the naive tax-shield maximization** (1963 implies ~100% debt). The bankruptcy-cost
  counterweight from source 02 must always be applied; never let the engine recommend max leverage.

## Concrete build implication

- **Component:** `capital_structure_analyzer` — a deterministic module exposing
  `tax_shield(tax_rate, debt)` and `levered_cost_of_equity(r0, r_d, debt, equity, tax_rate)`.
- **Contract:** inputs are floats with explicit units (currency, decimal rates); outputs annotated
  with the formula + source that produced them (explainability contract).
- **Test:** property-based test that WACC is invariant under leverage in the no-tax case (MM Prop.
  I/II), and boundary tests (T_C=0, D=0, D/E→∞) — a tautology-free, teeth-having check
  (CLAUDE.md §3.6). This is industry-agnostic (works for any panel row in B12).
