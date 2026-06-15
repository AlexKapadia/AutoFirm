# BEST-PARTS — Service-Profit Chain

## What AutoFirm should ADOPT

### 1. The operations→employee→customer→profit causal model for SERVICE companies — ADOPT
Many B12-panel industries (consulting/professional services, healthcare, restaurants, marketplaces)
are service-dominant, where TPS/SCOR's product-centric framing is incomplete. The Service-Profit
Chain supplies the missing **service-operations causal model**, and it is **independently empirically
validated** (Kamakura 2002) — meeting the ≥2-source bar for an important playbook step. **Build
implication:** for service-type client companies, the operations playbook (L2.B11) instruments the
chain's measurable links (internal service quality, employee/agent productivity, customer-perceived
value, satisfaction, loyalty, profit) instead of only product-flow KPIs.

### 2. "Loyalty, not satisfaction, drives profit" → measure retention/repeat, not just CSAT — ADOPT
The finding that *very*-satisfied → loyal (and loyalty, not satisfaction, drives profit) tells
AutoFirm which KPI to optimize. **Build implication:** the support/success playbook (L2.B9) targets
retention/repeat/referral (loyalty proxies) as the profit-linked KPI, with CSAT/NPS as upstream
indicators — feeding numeric cohort/retention charts into `evidence/` (ties to B4.2 LTV/retention).

### 3. The chain as AutoFirm's OWN internal model — ADOPT (meta)
AutoFirm's "employees" are its agents; "internal service quality" is the substrate (good prompts,
tools, memory, gates). The chain predicts that investing in agent working-conditions (clear briefs,
non-flooded context, good tooling) propagates to client-delivered value. **Build implication:**
justifies the orchestration investments (progressive disclosure, context protection, A4 memory) as
*value drivers*, not overhead.

## What AutoFirm should REJECT / bound
- **REJECT applying the chain to pure-product/low-contact ops** where employee-customer contact is
  minimal (e.g. some discrete-manufacturing back-office). There, TPS/SCOR/TOC dominate; the
  Service-Profit Chain is for **service-dominant** value streams. Industry-parameterize (B12) which
  model leads.
- **REJECT treating the HBR article alone as proof of the quantitative magnitudes.** Use the
  *structure* (validated) and derive magnitudes from the client's own data; don't import HBR's
  illustrative numbers as ground truth.

## Concrete build implications
- **Component:** `operations/service_profit_chain` — a service-ops KPI graph (internal-quality →
  employee-productivity → customer-value → satisfaction → loyalty → profit).
- **Contract:** service-type client playbooks emit loyalty/retention as the profit-linked target KPI.
- **Test:** generalization test — the chain instantiates correctly for service panel rows
  (consulting, healthcare, restaurant, marketplace) and is correctly *not* the lead model for pure
  manufacturing (anti-overfit, CLAUDE §3.9).
