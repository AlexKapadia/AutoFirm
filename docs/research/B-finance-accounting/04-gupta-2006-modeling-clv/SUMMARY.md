# SUMMARY — Gupta et al., Modeling Customer Lifetime Value

## Full citation
- **Title:** Modeling Customer Lifetime Value
- **Authors:** Sunil Gupta (Harvard), Dominique Hanssens (UCLA / MSI), Bruce Hardie (London Business School), William Kahn (Capital One), V. Kumar (Univ. of Connecticut), Nathaniel Lin (IBM), Nalini Ravishanker (UConn), S. Sriram (UConn)
- **Year:** 2006
- **Venue:** *Journal of Service Research*, Vol. 9, No. 2 (November 2006), pp. 139-155. **DOI: 10.1177/1094670506293810.** Publisher: Sage.
- **URL (author copy):** https://www.anderson.ucla.edu/sites/default/files/documents/areas/fac/marketing/JSR2006(0).pdf

## Questions informed
- **L1.B4.1** (unit economics / customer profitability as a modeling input) and **L1.B4.2** (customer modeling: CAC/LTV, retention/cohort). BFIN consumes the CLV result as a revenue-side driver of the financial model.

## GRADE tier
- **High.** Peer-reviewed journal article authored by the leading CLV researchers (Gupta, Hardie, Kumar). The core formula is the canonical present-value definition, independently reproduced across Gupta-Lehmann-Stuart (2004, *Journal of Marketing Research*), Reinartz & Kumar (2003), and Fader-Hardie-Lee (2005) -> satisfies multi-source corroboration for the relied-upon formula.

## Key claims with exact formulae (locators = paragraph markers in extract)

### 1. Definition (p.143)
> "CLV is generally defined as the present value of all future profits obtained from a customer over his or her life of relationship with a firm... CLV is similar to the discounted cash flow approach used in finance. However... CLV is typically defined and estimated at an individual customer or segment level... [and] explicitly incorporates the possibility that a customer may defect to competitors in the future."

### 2. General CLV formula (Eq. on p.143; attributed to Gupta, Lehmann & Stuart 2004; Reinartz & Kumar 2003)
> "CLV = Sum_{t=0..T} [ (p_t - c_t) * r_t / (1 + i)^t ] - AC"
where:
- `p_t` = price paid by the consumer at time t
- `c_t` = direct cost of servicing the customer at time t
- `i` = discount rate (cost of capital for the firm)
- `r_t` = probability of customer repeat-buying / being "alive" at time t
- `AC` = acquisition cost
- `T` = time horizon for estimating CLV

### 3. Horizon caveat (p.143)
> "Gupta and Lehmann (2005) showed that using an expected customer lifetime generally overestimates CLV, sometimes quite substantially." (Hence prefer the survival-weighted infinite/long horizon over a fixed "expected lifetime" multiplier.)

### 4. Constant-parameter simplification (text p.142, Gupta & Lehmann 2005)
With constant margin m, constant retention r, and constant discount i over an infinite horizon, the survival-weighted sum collapses to the closed form (the "margin multiple"):
> `CLV = m * [ r / (1 + i - r) ]`
(This is the algebraic limit of the Eq.2 series with p_t - c_t = m and r_t = r^t; it is the widely-used SaaS/subscription LTV formula.)

### 5. Empirical model comparison (pp.142-143)
- CLV-based customer selection beats RFM: Reinartz & Kumar (2003) — top-30% by CLV gave **33% higher revenue** than top-30% by RFM (catalog retailer, ~12,000 customers, 3 yrs). Venkatesan & Kumar (2004) — top-5% by CLV gave **10%-50% higher profit** than RFM/past-value (B2B, ~2,000 customers).
- Noncontractual settings: **Pareto/NBD** model (Schmittlein, Morrison & Colombo 1987) for transaction flow; spend models by Schmittlein & Peterson (1994), Fader-Hardie-Berger (2004).

## Reproducibility note
Extracted via `pdftotext`; the general formula appears in the "Fundamentals of CLV Modeling" section with variable glossary immediately following. DOI 10.1177/1094670506293810 resolves to the Sage record. The constant-parameter closed form is derivable from Eq.2 by geometric-series summation (m * sum_{t=1..inf} (r/(1+i))^t = m * r/(1+i-r)).
