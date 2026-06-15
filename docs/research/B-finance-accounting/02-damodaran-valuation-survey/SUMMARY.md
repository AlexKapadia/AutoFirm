# SUMMARY — Valuation Approaches and Metrics: A Survey of the Theory and Evidence

## Full citation
- **Title:** Valuation Approaches and Metrics: A Survey of the Theory and Evidence
- **Author:** Aswath Damodaran, Stern School of Business, New York University
- **Year:** 2006 (November)
- **Venue:** *Foundations and Trends in Finance*, Vol. 1, No. 8 (2005), 693-784 (now Publishers, peer-reviewed monograph series); the linked PDF is the author manuscript.
- **URL:** https://pages.stern.nyu.edu/~adamodar/pdfiles/papers/valuesurvey.pdf

## Questions informed
- **L1.B4.1** Financial-modeling foundations — the full valuation-method alternative space + empirical evidence on accuracy.

## GRADE tier
- **High** for the taxonomy and for the cited empirical studies (each is a named, dated, peer-reviewed paper). The survey is a peer-reviewed monograph; the empirical claims below are attributed to independent primary studies (different authors/orgs), satisfying the >=3-independent-sources bar for the critical "which method is more accurate" claim.

## The full alternative space (the four approaches) — Section 1, p.1 (line 12 of extract)
> "In general terms, there are four approaches to valuation. The first, **discounted cashflow valuation**, relates the value of an asset to the present value of expected future cashflows... The second, **liquidation and accounting valuation**, is built around valuing the existing assets of a firm, with accounting estimates of value or book value... The third, **relative valuation**, estimates the value of an asset by looking at the pricing of 'comparable' assets relative to a common variable like earnings, cashflows, book value or sales. The final approach, **contingent claim valuation**, uses option pricing models to measure the value of assets that share option characteristics... real options."

### Sub-variants enumerated
- **DCF variants (4):** (a) risk-adjusted-discount-rate models (most common); (b) APV / adjusted present value; (c) excess-return models (EVA / residual income); (d) certainty-equivalent / cash-flow-haircut models. Excess-return value = capital invested + PV(excess returns).
- **Relative valuation:** earnings multiples (PE, EV/EBIT, EV/EBITDA), book multiples (P/B), revenue multiples (P/S, EV/Sales); comparables chosen by industry and/or by fundamentals.
- **Contingent claim:** real options (option to delay, expand, abandon); equity-as-call-option for distressed firms.

## Key empirical claims (exact, with the primary studies — all independent)

1. **Excess-return (residual-income) models beat plain DCF/DDM over long horizons.** "Penman and Sou[r]giannis (1998) compared the dividend discount model to excess return models and concluded that the valuation errors in a discounted cash flow model, with a ten-year horizon, significantly exceeded the errors in an excess return model... attributed... to GAAP accrual earnings being more informative than either cash flows or dividends. Francis, Olson and Oswald (1999) concurred." Counterpoint: "Courteau, Kao and Richardson (2001) argue [the] superiority... can be attributed entirely to differences in the terminal value calculation."
   - Penman, S. & Sougiannis, T. (1998), *Contemporary Accounting Research*; Francis, Olson & Oswald (1999); Courteau, Kao & Richardson (2001).

2. **DCF and relative valuation give similar values in LBO/transaction settings.** "Kaplan and Ruback (1995) examine the transactions prices paid for 51 companies in leveraged buyout deals and conclude that discounted cash flow valuations yield values very similar to relative valuations." Berkman, Bradbury & Ferguson (2000): PE and DCF "both... explain about 70% of the price variation and have similar accuracy" (45 NZX IPOs).
   - Kaplan, S.N. & Ruback, R.S. (1995), *Journal of Finance*, v50, 1059-1093.

3. **Multiples have only modest standalone predictive power for IPOs.** "Kim and Ritter (1998) value a group of IPOs using PE and price to book ratios and conclude that multiples have only modest predictive ability." Lee, Myers & Swaminathan (1999): for the Dow 30, "prices are more likely to converge on the [residual-income DCF model] in the long term."

4. **Comparable-firm selection matters.** Alford (1992): industry categorization "match[es] or slightly outperform[s]" fundamental categorization; Bhojraj & Lee (2002) and Cheng & McNamara (2000): combining industry + fundamentals (e.g. total assets) "yields more precise valuations."  **Beatty, Riffe & Thompson (1999): the harmonic mean of peer multiples gives better value estimates than the arithmetic mean.**

5. **Liquidation value < going-concern DCF**, often steeply: Kaplan (1989) cites a Merrill Lynch estimate of ~32% discount for a speedy sale (Federated); Holland (1990) > 50% for specialized machine-tool assets; Shleifer & Vishny (1992): deeper discounts when buyers are few/financially constrained.

6. **Direct bankruptcy costs are small (~5%, Warner 1977) but indirect distress costs are large (10-25% of firm value; Andrade & Kaplan 1998, 10-23%).** Relevant to APV/expected-bankruptcy-cost modeling.

## Reproducibility note
Extracted via `pdftotext`; all attributed studies carry author, year, and journal as printed in the survey's footnotes (footnotes 56-58, 64, 66, 91-94, 114-116, 122-125). A reviewer can re-fetch the PDF and locate each by footnote number.
