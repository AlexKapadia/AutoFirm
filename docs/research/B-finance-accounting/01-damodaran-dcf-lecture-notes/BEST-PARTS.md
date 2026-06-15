# BEST-PARTS — Damodaran DCF lecture notes

## What AutoFirm ADOPTS (and the build implication)

1. **The intrinsic-value engine is `Value = Sum CFt/(1+r)^t`.** AutoFirm's B4 finance toolkit (`L2.B4`) implements a **deterministic DCF core** with this as the single source of truth. Build implication: a pure function `present_value(cashflows: list, rate) -> Decimal` plus typed `DCFInputs` contract. Determinism + zero-numerical-error is mandatory (CLAUDE §3.11) — use exact decimal arithmetic, not floats.

2. **Two explicit, type-separated valuation lanes: FCFF->WACC->EnterpriseValue and FCFE->CostOfEquity->EquityValue.** The matching rule (cashflow type MUST match discount-rate type) becomes a **fail-closed invariant**: a model that discounts FCFE at WACC is rejected at the contract boundary. Build implication: an enum-typed `CashflowKind {EQUITY, FIRM}` paired with `DiscountRateKind {COST_OF_EQUITY, WACC}`; a validator that refuses mismatched pairs. This is a high-value adversarial/property test (mismatch must always raise).

3. **Exact FCFF / FCFE bridge formulae** become tested deterministic transforms from the 3-statement outputs. Build implication: `fcff = ebit*(1-t) - (capex - depr) - delta_wc`; `fcfe = net_income - (capex-depr)*(1-DR) - delta_wc*(1-DR)`. Property test: when DR=0 and there is no net borrowing, FCFE should reconcile to FCFF minus after-tax interest (metamorphic relation).

4. **Terminal value = `CF_{n+1}/(r - g_n)` with the hard guardrail `g_n <= riskfree rate`.** Build implication: a fail-closed check rejects any `g_n >= r` (division blow-up / negative value) and any `g_n` above the long-run riskfree/economy growth — a classic overfit-to-optimism error. Boundary tests at g_n = r (must reject) and g_n = r - epsilon (must pass).

5. **CAPM cost of equity and after-tax cost of debt** as the discount-rate builders. Build implication: `cost_of_equity = rf + beta*(erp)`; `cost_of_debt = (rf + default_spread)*(1-t)`; WACC = market-value-weighted blend. These feed the discount-rate side of the engine.

6. **Riskfree-duration matching rule** ("match the duration of the analysis to the duration of the riskfree rate") -> a sourcing rule for the public-data layer (source 05): pull the long-term government bond yield, not the T-bill, for multi-year valuations.

## What AutoFirm REJECTS (and why)
- **Reject the dividend discount model as the default engine.** DDM is a special case and (source 02) is empirically the most error-prone DCF variant over a 10-year horizon (Penman & Sougiannis 1998). Use FCFF/FCFE as default; expose DDM only for cash-cow/dividend-mandated entities.
- **Reject intuitive "cash-flow haircuts" for risk** (source 02 §35 warns of opacity / double-counting). Risk must enter through the discount rate or explicit scenario weights, never an unlogged gut adjustment — this preserves the explain-every-decision requirement (CLAUDE §3.11).

## Generality check
The engine is parameterized by (cashflows, rate, growth, horizon) only — no company-specific constants. It works for any firm in any industry on the fixed industry panel; industry differences enter only through inputs (margins, capex intensity), never through code.
