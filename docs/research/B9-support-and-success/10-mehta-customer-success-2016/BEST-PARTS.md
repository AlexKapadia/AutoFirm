# BEST-PARTS — Mehta et al. (2016) Customer Success

## ADOPT
- **Separate "Customer SUCCESS" (proactive, retention/expansion) from "Customer SUPPORT" (reactive, issue resolution)** as two functions in AutoFirm's B9 playbook, with different metrics:
  - Support: CES, FCR, SLA attainment, deflection/containment (sources 05–09).
  - Success: **health score, churn rate, Net Revenue Retention (NRR), expansion rate.**
- **A composite Customer Health Score** as a deterministic, auditable model combining ≥4 signal classes: product usage, support/effort signals (CES, recontacts, SLA breaches from sources 05/06/07), relationship signals, and financial signals.
  - **Build implication (L2.B9):** ship `compute_health_score(signals)` AND a **trend/derivative** component — alert on **rate of decline**, not just low absolute score (the book's key insight). Health feeds an autonomous "at-risk → proactive outreach" workflow. Each score must be **explainable** (which signal drove the change) per CLAUDE §3.11.
- **NRR as the headline success KPI:** `NRR = (start_ARR + expansion − contraction − churn) / start_ARR`, deterministic and unit-tested.

## REJECT
- **REJECT the vendor outcome percentages** ("40–60% lower churn", "2x expansion") as facts — Very-low/biased; usable only as motivation, never as AutoFirm-emitted claims or constants (CLAUDE §3.9, DEPTH-RUBRIC §6).
- **REJECT a single-signal or absolute-only health score** — the rate-of-change insight is the load-bearing design point; an absolute-threshold-only model misses the highest-risk (rapidly-declining) accounts.

## Why (cited)
- Establishes the success-vs-support split and the health-score/NRR machinery that AutoFirm needs to run the *full* B9 lifecycle (not just ticket-closing). Industry-general for any recurring-revenue client; for transactional/one-off businesses, the success layer degrades gracefully to retention/repurchase metrics (parameterised per B12 panel).
