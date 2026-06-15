# SUMMARY — SaaS Operating-Model Metrics (Rule of 40, NRR, CAC payback, Magic Number)

## Full citation(s)
- **Rule of 40 — origin:** popularized 2015; commonly attributed to **Fred Wilson** ("What's a good
  ratio... growth rate + profit > 40%", AVC blog, Feb 2015) and **Brad Feld** ("The Rule of 40% For
  a Healthy SaaS Company", feld.com, 2015). Formula reference: Wall Street Prep, "The Rule of 40."
  https://www.wallstreetprep.com/knowledge/rule-of-40/
- **Magic Number — origin:** introduced by **Lars Leckie / Scale Venture Partners** (~2008).
- **Benchmark data:** Bessemer Venture Partners *Cloud Index / State of the Cloud*; OpenView SaaS
  Benchmarks; KeyBanc Capital Markets SaaS Survey; Benchmarkit 2025 SaaS Performance Metrics
  (https://www.benchmarkit.ai/2025benchmarks).
- **DOI:** n/a (VC/practitioner-primary metrics + benchmark surveys)

## Ontology questions informed
- **L1.B1.2** (operating-model archetype for **B2B SaaS** — panel row 1; the canonical
  recurring-revenue operating model).
- Feeds **L2.B4** (customer/financial modeling), **L2.B5** (pricing), **L1.B4.2** (CAC/LTV).

## GRADE tier
**Moderate** for the metric DEFINITIONS (VC-primary, stable, cross-consistent across BVP/OpenView/
KeyBanc) and the *direction* of benchmarks. **Low-to-Moderate** for any specific benchmark NUMBER
(year/sample-dependent; surveys differ). Down-rate: benchmark figures are time-varying and
survey-specific — AutoFirm must treat them as *configurable inputs*, not constants.

## Key metric definitions (formulae, exact)
- **Rule of 40:** `Revenue Growth Rate (%) + Profit Margin (%) >= 40%`. Profit margin = EBITDA
  margin **or** FCF margin (source-dependent; state which). >=40% signals a healthy growth/
  profitability balance.
- **Net Revenue Retention (NRR):** `(Starting MRR + expansion - contraction - churn) / Starting MRR`
  over a cohort, excluding new logos. >100% = expansion outweighs churn; top performers ~104-120%+.
- **CAC Payback Period (months):** `CAC / (new MRR * gross margin)`. Months to recover acquisition
  cost. Lengthens with scale/enterprise (early ~12 mo; large ARR ~20-21 mo per 2025 surveys).
- **SaaS Magic Number:** `(net new ARR in quarter) / (S&M spend in prior quarter)`. >0.75 ~ efficient
  growth; <0.5 ~ inefficient.
- **Burn Multiple:** `Net cash burned / Net new ARR`. Lower = more capital-efficient (early ~3.x,
  scaled ~1.x).
- **LTV/CAC:** lifetime gross-margin value / acquisition cost; ~3x a common health heuristic.

## Reproducibility note
Definitions are reproduced consistently across BVP, OpenView, KeyBanc, and Wall Street Prep.
**Benchmark numbers carry their survey + year inline** and are flagged time-varying; any number
AutoFirm relies on must cite the specific survey edition (DEPTH-RUBRIC §3.3).
