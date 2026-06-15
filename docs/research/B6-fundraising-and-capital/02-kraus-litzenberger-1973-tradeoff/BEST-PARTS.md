# BEST-PARTS — Kraus & Litzenberger (1973)

## ADOPT

- **Adopt the trade-off frame as the engine's debt-capacity ceiling.** When AutoFirm considers debt
  for a client, it must weigh the tax-shield benefit against rising expected distress cost and
  recommend a **target leverage band**, never max leverage. Implement as
  `optimal_leverage_band(tax_rate, asset_volatility, distress_cost_proxy)` returning a low/high range.
- **Adopt the dynamic-trade-off insight** (firms move toward a target with adjustment costs): the
  playbook should treat the recommended leverage as a **target to converge toward across rounds**,
  tolerating deviation rather than forcing instant rebalancing.

## REJECT

- **Reject static-trade-off as a universal model for early-stage clients.** Pre-revenue / pre-profit
  startups have **no taxable income to shield** and very high distress costs, so the trade-off
  optimum is ~zero debt. For those, defer to the pecking-order/growth-cycle logic (sources 03, 05).
  Do not apply tax-shield reasoning to firms with no profits.

## Concrete build implication

- **Component:** extend `capital_structure_analyzer` with a distress-cost term so it returns
  `V_L = V_U + PV(tax_shield) - PV(distress_costs)` and an interior optimal-leverage band.
- **Test:** boundary tests — at zero tax rate the optimum collapses toward zero debt; as distress
  cost -> 0 the optimum approaches the MM tax corner (a teeth-having check that the trade-off curve
  behaves, CLAUDE.md §3.6). Industry-parameterized: asset volatility / tangibility differ per B12 row
  (manufacturing tolerates more debt than SaaS), so the band must move with inputs, never be a
  constant.
