# SUMMARY — Modigliani & Miller (1958, 1963): Capital structure (ir)relevance

**Informs ontology question(s):** L1.B6.1 (fundraising & capital structure foundations) ->
feeds L2.B6 (automated fundraising & capital playbook).

## Full citations

- **Primary (1958):** Modigliani, F. & Miller, M. H. (1958). *The Cost of Capital, Corporation
  Finance and the Theory of Investment.* **The American Economic Review**, 48(3): 261-297.
  (American Economic Association.)
  Reference record: https://www.scirp.org/reference/referencespapers?referenceid=1609636 ·
  Semantic Scholar: https://www.semanticscholar.org/paper/7d9e0c7abfb8e9873156ecac691c59e1071243a9
- **Primary (1963 correction):** Modigliani, F. & Miller, M. H. (1963). *Corporate Income Taxes
  and the Cost of Capital: A Correction.* **The American Economic Review**, 53(3): 433-443.
- **Secondary pointer (formulae):** "Modigliani-Miller theorem", Wikipedia.
  https://en.wikipedia.org/wiki/Modigliani%E2%80%93Miller_theorem (pointer to the primary papers,
  not the citation of record).

## GRADE tier

**High** — both are peer-reviewed articles in a top economics journal (AER) by two later Nobel
laureates; founding theorems of capital-structure theory, cited tens of thousands of times. No
down-rate (theory is exact, not an empirical effect). The *real-world* relevance is bounded by
unrealistic assumptions (below) — an indirectness caveat for APPLYING the result, not for its
validity.

## Key claims & exact formulae

**Assumptions (frictionless markets):** no taxes (1958 base case), no transaction/bankruptcy costs,
no asymmetric information, individuals and firms borrow at the same risk-free rate, and investment
policy is fixed (financing does not change cash flows). The 1958 paper is noted as the first to use
**no-arbitrage (homemade leverage)** arguments to prove the propositions.

**Proposition I (no taxes):**
> V_U = V_L

The value of an unlevered firm equals the value of an otherwise-identical levered firm — capital
structure is irrelevant to firm value.

**Proposition II (no taxes):**
> r_E = r_0 + (D/E)(r_0 - r_D)

Cost of equity rises linearly with debt-to-equity (D/E); higher financial risk exactly offsets the
benefit of "cheaper" debt, leaving WACC constant. r_0 = unlevered cost of capital, r_D = cost of
debt, r_E = cost of equity, D = debt, E = equity.

**Proposition I (with corporate taxes, 1963 correction):**
> V_L = V_U + T_C * D

The levered firm is worth more by the present value of the interest tax shield = corporate tax rate
(T_C) times debt (D), because interest is tax-deductible.

**Proposition II (with corporate taxes):**
> r_E = r_0 + (D/E)(r_0 - r_D)(1 - T_C)

The financing premium on equity is dampened by the factor (1 - T_C).

## What it establishes / limits

- It is the **null hypothesis / baseline**: in a frictionless world, *how* you fund a firm does not
  change its value. Every real-world instrument preference must therefore be explained by a **market
  friction** — taxes, bankruptcy/distress costs, asymmetric information, agency costs. Later theories
  (sources 02, 03) are exactly these frictions reintroduced.
- The 1963 correction implies taxes alone would push firms to ~100% debt, which is empirically false
  — motivating the trade-off theory's countervailing bankruptcy cost (source 02).

## Reproducibility note

Re-derive Prop. I via the homemade-leverage no-arbitrage argument in the 1958 paper; WACC-invariance
follows from Prop. II. The tax-shield result V_L = V_U + T_C*D is the headline of the 1963
correction. Notation matches the formula pointer and standard corporate-finance texts.
