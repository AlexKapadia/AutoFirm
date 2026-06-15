# SUMMARY — Core Web Vitals: Thresholds & Methodology

## Full citation
- **(A) Title:** Defining the Core Web Vitals metrics thresholds
  - **Author/Org:** Patrick Meenan & Brian Mcquade, Google / web.dev (Chrome team)
  - **URL:** https://web.dev/articles/defining-core-web-vitals-thresholds
- **(B) Title:** Understanding Core Web Vitals and Google Search results
  - **Author/Org:** Google Search Central
  - **URL:** https://developers.google.com/search/docs/appearance/core-web-vitals
- **(C) Title:** Web Vitals (LCP/INP/CLS metric definitions)
  - **Author/Org:** Google / web.dev · **URL:** https://web.dev/articles/vitals
- **Year:** thresholds defined 2020; INP replaced FID as a Core Web Vital **March 2024**
- **Venue/Publisher:** Google web.dev / Chrome team (primary platform authority)

## Questions it informs
- **L1.B13.4** (Core Web Vitals performance budgets — PRIMARY normative source for the numbers)

## GRADE tier: High
Primary source from the team that defines and measures the metrics (Chrome/CrUX). The thresholds
ARE the standard. No down-rate. Methodology is explicitly documented and reproducible from CrUX.

## Key claims (exact)

**The three Core Web Vitals and their thresholds (assessed at the 75th percentile of page loads):**

| Metric | Measures | Good | Needs improvement | Poor |
|---|---|---|---|---|
| **LCP** Largest Contentful Paint | Loading | **<= 2500 ms (2.5 s)** | 2500-4000 ms | **> 4000 ms** |
| **INP** Interaction to Next Paint | Responsiveness | **<= 200 ms** | 200-500 ms | **> 500 ms** |
| **CLS** Cumulative Layout Shift | Visual stability | **<= 0.1** | 0.1-0.25 | **> 0.25** |

**Assessment rule.** "A site passes the Core Web Vitals assessment if it meets the recommended
targets at the **75th percentile** for all three metrics" — i.e. at least 75% of (real-user) page
visits experience the "good" level. INP replaced First Input Delay (FID) as a Core Web Vital in
March 2024.

**Methodology (three criteria Google used to set the thresholds).**
1. **High-quality user experience** — thresholds reflect HCI/perception research. For LCP: Miller
   (1968) & Card et al. — user attention/focus is retained for roughly 0.3-3 s; 2.5 s sits within
   this. For INP: causality-perception research — feedback delays up to ~100 ms are perceived as
   instantaneous; 200 ms is the practical "good" compromise. For CLS: no prior research existed, so
   Google empirically evaluated real pages and found shifts of 0.1 and lower "noticeable but not
   excessively disruptive."
2. **Achievability** — a "good" threshold must be reachable: at least ~10% of origins already meet
   it in CrUX field data, so optimization is realistic.
3. **Percentile choice** — the 75th percentile "strikes a reasonable balance": most visits (3 of 4)
   meet the target while minimizing the influence of outliers.

## Reproducibility note
The 2500 ms / 200 ms / 0.1 "good" thresholds, the >4000/>500/>0.25 "poor" thresholds, and the 75th
percentile rule are stated verbatim at web.dev/articles/defining-core-web-vitals-thresholds and the
Search Central doc, and re-verifiable in CrUX/PageSpeed Insights.
