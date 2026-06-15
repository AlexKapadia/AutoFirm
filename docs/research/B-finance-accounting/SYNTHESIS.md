# SYNTHESIS — Branch B (BFIN): Finance, Accounting & Valuation on Real Data

Covers Layer-1 questions **L1.B4.1** (financial-modeling foundations) and **L1.B4.4** (public-data
sourcing + PII boundary), with spillover into L1.B4.2 (CLV/unit economics). Feeds applied
question **L2.B4** (the real-data modeling toolkit). All claims are cited to the six source
folders in this branch.

## 1. The surveyed alternative space (DEPTH-RUBRIC §4)

### Valuation methods (Damodaran 2006, source 02 — the canonical four-approach menu)
| Approach | Variants | AutoFirm decision |
|---|---|---|
| **Discounted cash flow** | risk-adjusted-rate (FCFF/FCFE), APV, excess-return/residual-income, certainty-equivalent | **ADOPT** FCFF/FCFE as core; ADOPT residual-income as cross-check; DEFER APV to time-varying-leverage cases; REJECT cash-flow-haircut (opaque) |
| **Relative / multiples** | PE, EV/EBIT, EV/EBITDA, P/B, EV/Sales; comparables by industry +/- fundamentals | **ADOPT** as second lane; harmonic-mean aggregation; comparables by GICS/NAICS + fundamentals |
| **Asset / liquidation** | book value, liquidation value (discounted) | **ADOPT as a floor only** (liquidation 32-50% below going-concern) |
| **Contingent claim / real options** | option to delay/expand/abandon; equity-as-call | **DEFER** to high-optionality cases (early-stage, distressed, natural-resource) |

### Accounting foundation (sources 01, 03)
Three-statement articulation (income statement -> balance sheet -> cash-flow statement) under IAS 7
(IFRS) cross-checked by FASB ASC 230 (US GAAP). Cash-flow statement = Operating/Investing/Financing;
indirect method is the engineering default. The articulation invariants (A=L+E; net income -> retained
earnings; CFS total == delta cash) are the correctness backbone.

### Unit economics (source 04, Gupta et al. 2006)
CLV = customer-level DCF: general survival-weighted form for noncontractual (Pareto/NBD) and the
constant-parameter closed form `CLV = m*r/(1+i-r)` for contractual/subscription. Net of acquisition
cost -> LTV:CAC.

### Public-data sourcing (sources 05, 06)
SEC EDGAR JSON APIs (keyless, XBRL, authoritative) are the primary real-data source. Legality of
accessing public data rests on Van Buren (SCOTUS 2021, "gates-up-or-down") and hiQ v. LinkedIn
(9th Cir. 2022), bounded by ToS, copyright, privacy law, and a hard PII synthetic-only rule.

## 2. Concrete, cited recommendation for AutoFirm (the BFIN design)

**A deterministic, exact-arithmetic finance core with three layers:**

1. **Articulation engine (sources 01, 03).** A typed 3-statement model whose invariants are
   fail-closed checks (A=L+E and CFS-ties-to-cash-delta to the cent — CLAUDE §3.11 zero-numerical-
   error). One shared working-capital/D&A representation feeds both the CFS (indirect method) and the
   FCFF/FCFE bridge. **Highest-value adversarial/property test in the branch:** generate
   internally-consistent random transactions and assert both invariants hold.

2. **Valuation triangulation (sources 01, 02).** A single audited `present_value()` primitive
   powers (a) FCFF->WACC->enterprise value, (b) FCFE->cost-of-equity->equity value, and (c) the CLV
   engine (source 04). Fail-closed guards: discount-rate/cashflow-kind matching; terminal-value
   `g_n < r <= riskfree`; CLV `r < 1+i`. Output is a **range across DCF + relative (harmonic-mean
   multiples) + residual-income**, with a divergence explanation — never a single point (the empirical
   accuracy evidence, source 02, makes a single number indefensible). Efficacy benchmark for
   `evidence/`: ~70% R^2 vs realized prices (Berkman et al. 2000); CLV ranking must beat an RFM
   baseline by the documented uplift (33% / 10-50%, source 04).

3. **Real-data + policy layer (sources 05, 06).** An EDGAR client enforcing the Fair-Access policy
   (descriptive User-Agent + <=10 req/s token bucket, fail-closed) maps XBRL `us-gaap` concepts into
   the typed contract, recording the SEC accession number as audit-log provenance. A
   `public_data_policy` gate runs three independent checks before any fetch — (i) gate-up / no auth
   (Van Buren/hiQ), (ii) ToS/contract, (iii) no PII / synthetic-only-for-sensitive — and **refuses on
   any ambiguity** (CLAUDE §5.6, §3.12).

**Why this wins (evidence, not taste):** no single valuation method is empirically dominant
(source 02), so triangulation + reported spread is the institution-grade posture; the articulation
invariants give the deterministic, zero-error guarantee BFIN demands; EDGAR + the legal gate give a
defensible real-public-data path with a hard PII boundary.

## 3. Generality (CLAUDE §3.9 / B12 panel)
Every engine is parameterized (cashflows, rate, growth, margins, retention) with no company-specific
constants. Contractual rows (SaaS/fintech/marketplace) use the closed-form CLV; noncontractual rows
(e-commerce/restaurant/retail) use Pareto/NBD. EDGAR covers all SEC filers; other registries plug into
the same contract via adapters. Documented boundaries: case law is US/9th-Cir. (local review needed
elsewhere); non-US/private firms need non-EDGAR adapters.

## 4. Open items handed to Layer 2 (L2.B4)
- Choose the residual-income vs APV cross-check engine on a golden set of real filings (branch-per-
  experiment, CLAUDE §3.4).
- Build the non-EDGAR public-registry adapters (Companies House etc.) for non-US panel rows.
- Calibrate the PII classifier feeding the fail-closed policy gate.

## Source index
01 Damodaran DCF lecture notes (FCFF/FCFE/TV/CAPM formulae) · 02 Damodaran 2006 valuation survey
(method taxonomy + empirical accuracy) · 03 IAS 7 + FASB ASC 230 (cash-flow standard) · 04 Gupta
et al. 2006 JSR (CLV) · 05 SEC EDGAR APIs (public data) · 06 Van Buren / hiQ (access legality).
