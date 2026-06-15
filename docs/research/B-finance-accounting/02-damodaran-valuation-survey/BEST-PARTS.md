# BEST-PARTS — Damodaran Valuation Survey (2006)

## What AutoFirm ADOPTS (and the build implication)

1. **A multi-method valuation ensemble, not a single DCF.** The survey's headline lesson is that no single approach dominates; accuracy is context-dependent (DCF vs relative converge in LBO settings; residual-income beats DDM over long horizons; multiples are weak standalone for IPOs). Build implication for `L2.B4`: AutoFirm produces a **valuation triangulation** — DCF (FCFF/FCFE), relative (peer multiples), and an excess-return/residual-income cross-check — and **reports the spread** with an explanation of divergence, rather than a single point estimate. This is the evidence-driven, multi-avenue posture CLAUDE §3.4 demands; the three lanes can even be the `experiment/*` branches measured on a golden set.

2. **Use the HARMONIC MEAN for peer-multiple aggregation** (Beatty, Riffe & Thompson 1999), not the arithmetic mean. Build implication: `peer_multiple = harmonic_mean(comparable_multiples)`. This is a concrete, testable design choice with a citation — a property test asserts harmonic <= arithmetic and that outliers are damped.

3. **Comparable selection = industry classification + fundamentals (growth, risk, total assets)** (Alford 1992; Bhojraj & Lee 2002). Build implication: the comparable-picker keys off GICS/NAICS industry (ties into L1.B12.2) PLUS quantitative similarity on growth/ROE/size — not industry alone. Feeds the cross-industry generalization layer.

4. **Quantified accuracy targets feed `evidence/`.** Adopt as benchmark thresholds: DCF and PE each explain ~70% of price variation in a clean cross-section (Berkman et al. 2000) -> AutoFirm's valuation module should report R^2 vs realized transaction/market prices and flag when it underperforms this peer-reviewed baseline. Distress haircut bands (liquidation 32-50% below going-concern; indirect distress cost 10-25% of firm value) become **scenario presets** for downside/recovery modeling.

5. **The four-approach taxonomy is the canonical menu** AutoFirm enumerates per valuation task (full-alternative-space coverage, DEPTH-RUBRIC §4): DCF / asset-liquidation / relative / contingent-claim(real-options). For most operating-company valuations: ADOPT DCF + relative; DEFER real-options to high-optionality cases (early-stage, natural-resource, distressed-equity-as-call); use asset/liquidation only as a floor.

## What AutoFirm REJECTS (and why)
- **Reject DDM as a primary engine** (empirically highest valuation error over long horizons; Penman & Sougiannis 1998).
- **Reject single-point valuation outputs** — the literature's mixed accuracy evidence makes a single number indefensible to an institutional reviewer (CLAUDE §3.2). Always a range + method-divergence note.
- **Reject the compressed-APV shortcut as a default** (Kaplan-Ruback) because it ignores expected bankruptcy costs and monotonically rewards leverage — a known bias. Use full APV only when leverage is genuinely time-varying.

## Generality check
Every adopted rule is method-level (harmonic mean, triangulation, comparable-selection criteria) and industry-agnostic; industry enters only as a parameter (peer set, multiple choice). No fit to any single company.
