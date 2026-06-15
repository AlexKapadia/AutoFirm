# BEST-PARTS — Gupta et al. 2006 (CLV)

## What AutoFirm ADOPTS (and the build implication)

1. **CLV is a DCF on a single customer/segment — reuse the same PV engine as source 01.** Build implication: `clv(margins, retention, discount, ac)` shares the `present_value` primitive with the firm-level DCF, with the addition of a survival weight `r_t`. One audited present-value function serves both firm valuation and unit economics -> less code, one place to test for numerical exactness.

2. **The general survival-weighted formula `CLV = Sum (p_t - c_t) r_t / (1+i)^t - AC` is the canonical contract.** Build implication: typed `CLVInputs { margins_or_(price,cost), retention_curve, discount, acquisition_cost, horizon }`. Acquisition cost is subtracted -> AutoFirm reports both gross CLV and net (CAC-adjusted) CLV, giving the LTV:CAC ratio that the pricing (L2.B5) and fundraising (L2.B6) playbooks consume.

3. **The constant-parameter closed form `CLV = m * r/(1+i-r)`** is the fast path for subscription/SaaS panel rows. Build implication: a deterministic function with a fail-closed guard `r < 1+i` (else the denominator goes non-positive -> infinite/negative CLV, the classic LTV blow-up). Boundary tests at r -> (1+i) must reject; this mirrors the terminal-value `g_n < r` guard in DCF (shared invariant pattern).

4. **Prefer survival-weighted long/infinite horizon over a fixed "expected lifetime" multiplier** (Gupta & Lehmann 2005: the lifetime-multiplier overestimates CLV). Build implication: AutoFirm's default LTV uses the retention-discounted series, NOT `margin * (1/churn)`, and flags the naive multiplier as an over-estimate when a user supplies it.

5. **CLV-based segmentation beats RFM — quantified** (33% higher revenue, top-30%; 10-50% higher profit, top-5%). Build implication: these are **efficacy benchmarks for `evidence/`** — AutoFirm's customer-value ranking should be validated to outperform an RFM baseline on a labelled cohort, reporting the uplift (CLAUDE §3.6 efficacy tests).

6. **Contractual vs noncontractual split:** for noncontractual (retail/e-commerce panel rows) adopt **Pareto/NBD** (Schmittlein-Morrison-Colombo 1987) + a spend model; for contractual (SaaS/subscription) use the retention-rate closed form. This is the full alternative-space coverage for the customer-modeling sub-question.

## What AutoFirm REJECTS (and why)
- **Reject the naive `LTV = ARPU / churn` shortcut as a default** — it is the un-discounted, fixed-lifetime form Gupta & Lehmann show overestimates value. Allow it only as a clearly-labelled approximation.
- **Reject ignoring acquisition cost** — gross CLV without AC is misleading for go/no-go decisions; AutoFirm always nets it.

## Generality check
Two engines (closed-form for contractual, Pareto/NBD for noncontractual) cover the full B12 panel: SaaS/fintech/marketplace subscription rows use the closed form; e-commerce/restaurant/retail noncontractual rows use Pareto/NBD. Parameters (m, r, i) are inputs, never hard-coded.
