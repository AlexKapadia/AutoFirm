# BEST-PARTS — Kaplan & Stromberg (2003)

## ADOPT

- **Adopt the five-rights model as the data contract for any equity raise AutoFirm structures or
  evaluates:** cash-flow rights, board rights, voting rights, liquidation rights, other control
  rights — modeled as separate, explicit fields, not collapsed into "% sold". A raise is a structured
  instrument, and the playbook must surface every dimension.
- **Adopt convertible-preferred mechanics as the default equity instrument to model** (liquidation
  preference, participation, anti-dilution, vesting), since it is empirically the dominant security.
- **Adopt state-contingent control as an explainability obligation:** when the engine evaluates a
  term sheet, it must flag *who gets control under which performance states* (downside -> investor
  control; upside -> founder control), so founders understand the real cost of the raise beyond
  dilution.

## REJECT

- **Reject reducing fundraising advice to a valuation/dilution number.** Two offers at the same
  valuation can differ enormously in liquidation preference, participation, and board control. Any
  engine that compares offers on price alone is rejected as incomplete and misleading.

## Concrete build implication

- **Component:** `term_sheet_model` — a typed structure capturing the five rights bundles + preferred-
  stock economics; and `term_sheet_explainer` that translates them into founder-facing plain language
  and an effective-cost estimate (e.g. liquidation-preference drag on founder proceeds in a low-exit
  scenario).
- **Test:** scenario tests across exit values — assert that adding a 1x participating preference vs.
  1x non-participating changes founder proceeds correctly at each exit value (a deterministic,
  unit-exact financial path, CLAUDE.md §3.11), and that two same-valuation offers with different
  preferences are ranked differently. Industry-agnostic (applies to any equity-raising client).
