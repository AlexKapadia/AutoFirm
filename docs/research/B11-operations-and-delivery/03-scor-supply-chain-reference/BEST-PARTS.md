# BEST-PARTS — SCOR Model

## What AutoFirm should ADOPT

### 1. Plan/Source/Make/Deliver/Return/Enable as the operations process skeleton — ADOPT
SCOR gives AutoFirm a **cross-industry, standardized process reference** for the operations/supply
function of ANY client company — exactly the generality L2.B12 demands. **Build implication:** the
operations playbook decomposes any client's delivery into these six processes; "Enable" maps to the
governance/risk/compliance layer AutoFirm already mandates (CLAUDE §5.6), giving a clean home for
audit, business rules, and kill-switch in the operations model.

### 2. The five performance attributes as the operations KPI contract — ADOPT
Reliability / Responsiveness / Agility / Cost / Asset-efficiency is a **balanced, standardized KPI
set** that prevents optimizing one dimension (e.g. cost) at the expense of customers. **Build
implication:** every client operations model emits these five attribute-scores; the
customer-facing vs internal split tells the agent which KPIs to surface to the client vs the
operator. These become numeric columns in `evidence/` charts (CLAUDE §3.10).

### 3. Two canonical, exactly-defined metrics — ADOPT as defaults
- **Perfect Order Fulfillment** (Reliability) — % of orders delivered complete, on time, in full,
  with correct documentation and no damage. A composite, auditable correctness metric.
- **Cash-to-Cash Cycle Time** (Asset-efficiency) — days inventory + days receivable − days payable.
**Build implication:** these are the *first two* default ops KPIs the modeling toolkit (L2.B4)
computes from a client's public/operational data; both are deterministic formulas → testable to the
unit (CLAUDE §3.11 zero-numerical-error).

### 4. Hierarchical L1→L2→L3 decomposition — ADOPT as the drill-down pattern
Strategic (L1) → configuration (L2) → element (L3) mirrors AutoFirm's gate/phase decomposition.
Use it so operations claims can be drilled from a headline KPI to the underlying process element.

## What AutoFirm should REJECT / bound
- **REJECT requiring the proprietary SCORmark benchmark dataset.** AutoFirm uses **public data only**
  (CLAUDE §3.12); do not cite or depend on paywalled benchmark numbers. Use SCOR's *definitions* and
  derive values from the client's real public data instead.
- **REJECT importing all 150–250 KPIs.** Adopt the Level-1 strategic metrics by default and only
  drill to L2/L3 metrics a specific client process needs (simplicity, CLAUDE §5.2).
- **DEFER** physical-logistics-specific Source/Make detail to industry parameterization (a SaaS
  "Make" is a build pipeline, not a factory) — handled by L2.B12.

## Concrete build implications
- **Component:** `operations/scor_process_model` (6 processes) + `operations/scor_kpi` (5 attributes,
  Perfect-Order-Fulfillment & Cash-to-Cash as defaults).
- **Contract:** ops KPI output schema = {reliability, responsiveness, agility, cost, asset_efficiency}.
- **Test:** deterministic unit tests for Perfect-Order-Fulfillment and Cash-to-Cash against
  hand-computed synthetic ledgers (boundary-exact, on/just-over/just-under the definition).
