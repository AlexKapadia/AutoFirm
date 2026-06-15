# BEST-PARTS — Reichheld (2003) NPS

## ADOPT
- **NPS as ONE of AutoFirm's standard relationship-loyalty metrics**, computed deterministically:
  `NPS = round(100 * (n_promoters − n_detractors) / n_respondents)` where promoter = response ∈ {9,10}, detractor ∈ {0..6}, passive ∈ {7,8}.
  - **Build implication (L2.B9):** the support/success playbook ships a `compute_nps(responses)` function with an **exact, unit-tested deterministic contract** (CLAUDE §3.11 zero-numerical-error). Property test: NPS is invariant to adding passives; boundary tests on 6/7 and 8/9 cutoffs; range constrained to [−100, +100].
- **Simplicity as a design value:** a single, comparable, cross-industry number is operationally cheap to collect and benchmark — useful for AutoFirm's cross-industry panel (B12) where one metric must work for SaaS, retail, fintech, etc.

## REJECT / GUARDRAIL
- **REJECT treating NPS as a validated growth predictor.** The "clear superiority"/growth-causation claim is **not** corroborated by peer-reviewed replication (Keiningham et al. 2007, *J. Marketing*). AutoFirm must NOT auto-generate "improve NPS → grow revenue" causal claims for client companies. NPS is a **tracking/benchmarking** signal, not a causal lever.
- **REJECT single-metric tunnel vision.** Pair NPS with CES (relational vs. transactional) and CSAT, and with operational metrics (FCR, SLA attainment). The metric chosen must match the question being asked (relationship vs. single-interaction).

## Why (cited)
- Definition is universal & deterministic → safe to encode exactly (CLAUDE §3.11).
- Predictive over-claim is a documented overfitting/bias risk → fail-closed on causal language (DEPTH-RUBRIC §6 overfit; CLAUDE §3.9 generality). Evidence: Keiningham et al. (2007), *Journal of Marketing* 71(3):39–51, DOI 10.1509/jmkg.71.3.039.
