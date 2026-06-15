# SUMMARY — Damodaran, Discounted Cash Flow Valuation (lecture notes)

## Full citation
- **Title:** Discounted Cash Flow Valuation (equity notes / overheads deck, `dcfallOld.pdf`)
- **Author:** Aswath Damodaran, Stern School of Business, New York University
- **Year:** n.d. (maintained course materials; companion to *Investment Valuation*, 2nd ed., Wiley 2002; 3rd ed. 2012)
- **Venue / Publisher:** NYU Stern faculty pages (primary, author-published teaching materials)
- **URL:** https://pages.stern.nyu.edu/~adamodar/pdfiles/eqnotes/dcfallOld.pdf

## Questions informed
- **L1.B4.1** Financial-modeling foundations — DCF/intrinsic valuation (FCFF/FCFE, terminal value, discount rates).

## GRADE tier
- **Moderate-to-High.** Author-published teaching notes by the most-cited authority on corporate valuation; formulae are textbook-canonical and independently corroborated by the peer-reviewed survey (source 02) and by the academic studies it cites. Down-rated one notch from High because the deck itself is teaching material, not a peer-reviewed venue; up-rated because the formulae are canonical and cross-checked. Note: source 02 shares the same author, so for the *formula* claim it is partial corroboration; the articulation identities are additionally anchored by IAS 7 (source 03) and standard CFA-curriculum identities.

## Key claims with exact formulae (locators = slide markers in extracted deck)

### 1. Core intrinsic-value identity ("Basis for Approach")
> "Value = Sum_{t=1..n} CFt / (1 + r)^t — where CFt is the cash flow in period t, r is the discount rate appropriate given the riskiness of the cash flow and t is the life of the asset."

### 2. Equity vs Firm valuation (slides 3-5)
- Equity: `Value of Equity = Sum_{t=1..n} [CF to Equity_t / (1 + k_e)^t]`, k_e = cost of equity. Dividend discount model is a special case (value = PV of expected dividends).
- Firm: `Value of Firm = Sum_{t=1..n} [CF to Firm_t / (1 + WACC)^t]`, WACC = weighted average cost of capital.
- Matching principle: cashflow-to-equity is discounted at cost of equity; cashflow-to-firm at WACC. Mismatching is the canonical DCF error.

### 3. Free-cash-flow definitions (slides 269, 305)
- FCFE: `Cashflow to Equity = Net Income - (Cap Ex - Depr)(1 - DR) - Change in WC(1 - DR) = FCFE`, DR = debt ratio (fraction of reinvestment funded with debt).
- FCFF: `Cashflow to Firm = EBIT(1 - t) - (Cap Ex - Depr) - Change in WC = FCFF`, t = marginal tax rate.

### 4. Terminal / stable-growth value (slides 239, 281, 314)
- DDM:  `Terminal Value = Dividend_{n+1} / (k_e - g_n)`
- FCFE: `Terminal Value = FCFE_{n+1} / (k_e - g_n)`
- FCFF: `Terminal Value = FCFF_{n+1} / (r - g_n)`  (r = WACC)
- g_n = stable (perpetual) growth rate; a firm in stable growth "grows at constant rate forever"; g_n cannot exceed the riskfree rate / economy growth.

### 5. Cost of equity - CAPM (slides 419-421)
> "Cost of Equity = Rf + Equity Beta * (E(Rm) - Rf), where Rf = Riskfree rate, E(Rm) = Expected Return on the Market Index (Diversified Portfolio)."
- Multifactor generalization: `E(R) = Rf + Sum_{j=1..N} beta_j (R_j - Rf)`.

### 6. Riskfree-rate discipline (slides 429-435)
- "For an investment to be riskfree ... the actual return is equal to the expected return [no variance]."
- Rule: "match the duration of the analysis (generally long term) to the duration of the riskfree rate (also long term)."

### 7. Cost of debt (slide 328)
- `Cost of Debt = (Riskfree Rate + Default Spread)(1 - t)` (after-tax).

## Reproducibility note
Formulae extracted via `pdftotext` from the author-published PDF, cross-checked slide-by-slide; each matches the standard form in Damodaran's *Investment Valuation* and the CFA curriculum. Re-derive by re-fetching the URL and running `pdftotext`.
