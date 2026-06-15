# SYNTHESIS — B9 / L1.B9.1: Customer Support & Success Foundations

> Surveyed alternative space + cited recommendation for AutoFirm's support & success layer.
> Feeds L2.B9 (automated support & success playbook). All claims trace to the 10 source folders here.

## 1. The question
What is the proven foundation for customer **support** (tiers, SLAs, deflection) and customer
**success** (health, retention) that AutoFirm must encode so it can run the post-sale function for
**any** company in **any** industry (B12 panel: SaaS, services, manufacturing, e-commerce,
marketplace, fintech, healthcare, restaurant)?

## 2. Full alternative space surveyed (metrics + operating models)

### 2.1 Loyalty / experience metrics — survey & verdict
| Metric | What it measures | Primary source | Tier | Verdict |
|---|---|---|---|---|
| **NPS** (% promoters − % detractors; 9–10 / 7–8 / 0–6) | Relational advocacy | Reichheld 2003 (01) | Low–Mod (def High) | **ADOPT as tracking metric only** — growth-prediction claim REJECTED (Keiningham 2007, 02, High) |
| **CSAT (single-item)** | One-interaction satisfaction | operational convention | Low | **ADOPT** as cheap transactional metric |
| **CSAT (ACSI multi-item, 0–100, PLS)** | Rigorous latent satisfaction | Fornell et al. 1996 (03) | High | **ADOPT** for evidence-grade reporting; PLS deferred to analysis layer |
| **CES** | Effort to resolve (transactional) | Dixon/Toman 2010 (05) | Low–Mod | **ADOPT as primary transactional metric** |
| **FCR** | Resolved first contact | Dixon 2013 (06) | Low–Mod | **ADOPT as primary quality gate** |
| **Deflection rate** | % self-service resolved | vendors (09) | Low | **ADOPT** (definition) — benchmark numbers REJECTED |
| **Containment rate** | % auto-resolved end-to-end | vendors (09) | Low | **ADOPT as headline AI-efficiency metric** |
| **Health score / NRR / churn** | Proactive success | Mehta et al. 2016 (10) | Low | **ADOPT** structure; vendor outcome %s REJECTED |

### 2.2 Operating-model alternatives — survey & verdict
- **Tiered desk (Tier 1 → Tier 2/3) with functional + hierarchical escalation, SLA/OLA/UC contracts** (ITIL, 07) → **ADOPT** as the general support-org backbone (industry-parameterised).
- **SLA-feasibility via Erlang C queueing** (offered load A = lambda x AHT; SL(t) = 1 − P_wait x exp(−(c−A)t/AHT); 80/20 convention) (08) → **ADOPT** the math as a deterministic staffing/feasibility calculator; 80/20 is a prior, not a constant.
- **Reactive support vs. proactive customer success** (10) → **ADOPT both as distinct functions** with distinct metrics.

### 2.3 Strategy alternatives — survey & verdict
- **"Delight / exceed expectations"** vs **"reduce effort / reliably meet expectations."**
  → **ADOPT effort-reduction + expectation-management**; **REJECT delight-maximisation.** This is
  the strongest cross-source convergence: peer-reviewed disconfirmation theory (Anderson & Sullivan
  1993, 04, N=22,300, High) + two large CEB studies (05 N>75k, 06 N>97k) all agree exceeding
  expectations yields little loyalty gain over reliably meeting them.

### 2.4 Explicitly EXCLUDED (scope boundary)
- Specific helpdesk products (Zendesk/Intercom/etc. as tools) — an integration/build choice for
  L2/L3, not a foundation. Voice-of-customer text analytics / sentiment models — defer to A4
  (memory/learning) + L2. Human-agent labor-law/scheduling detail — B10/B11.

## 3. Recommendation for AutoFirm (concrete, general, build-relevant)

**A two-function B9 layer, fully deterministic and explainable, parameterised by industry/size:**

1. **SUPPORT (reactive).** Typed `SLA{response, resolution, service_hours, priority=f(impact,urgency)}`
   contract (07); deterministic, business-hours-aware **SLA clock + escalation engine** (functional →
   specialist, hierarchical → HITL on breach risk, CLAUDE sections 2/5.6 fail-closed). Capacity sized
   by **Erlang C** (08). Quality measured by **CES + FCR**, efficiency by **containment + deflection**
   (05/06/09). Effort-event instrumentation (transfers, channel-switches, repeats, recontacts) penalised.
2. **SUCCESS (proactive).** Composite **Customer Health Score** over >=4 signal classes WITH a
   **rate-of-change** alarm (10), driving autonomous at-risk outreach; headline KPI **NRR** and churn.
3. **METRICS DISCIPLINE.** Each metric is a deterministic, unit-tested function with exact boundary
   behaviour (CLAUDE 3.11): `compute_nps`, `compute_csat_acsi`, `compute_ces`, `fcr_rate`,
   `deflection_rate`, `containment_rate`, `compute_health_score(+trend)`, `nrr`, plus
   `erlang_c_agents` / `service_level`. NPS/health outputs carry **provenance caveats** (NPS is not a
   growth predictor — 02; vendor benchmark %s are not constants — 09/10).
4. **GENERALITY (B12).** The abstraction is industry-agnostic: SLA/escalation/health apply to fintech
   disputes, e-commerce returns, restaurant complaints, healthcare service, etc.; only channels,
   priorities, and target values are parameterised per client baseline — **never** borrowed constants.

## 4. Evidence/teeth hooks (for `evidence/` + tests-with-teeth, CLAUDE 3.6/3.10)
- Property tests: NPS invariant to passives; CES/CSAT monotone; SLA clock exact across service-hour
  boundaries; Erlang C matches textbook reference values and diverges (to infinity) when c <= A;
  containment excludes HITL-escalated conversations; health-score trend fires on decline even at high
  absolute score.
- Charts: CES vs recontact-rate, deflection vs CES (guard against gaming), SLA-attainment distribution,
  health-trend vs churn.

## 5. Source-count compliance (DEPTH-RUBRIC section 1)
- Safety/correctness-critical "do NOT assert NPS to growth": Reichheld 2003 (01) claim + Keiningham
  2007 (02, peer-reviewed) refutation + Anderson/Sullivan (04) on what actually drives loyalty = >=3 independent.
- "Effort-reduction beats delight": 04 (peer-reviewed, High) + 05 + 06 (two large independent studies) = >=2–3.
- SLA/OLA/UC + escalation: ITIL (07) + 2 independent professional references = >=2.
- Erlang C math: queueing-theory primary + >=2 independent professional references (math itself High).
- CSAT rigor: Fornell 1996 (03, High) + Anderson/Sullivan 1993 (04, High) = >=2.
