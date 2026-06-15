# BEST-PARTS — Service Blueprinting

## What AutoFirm should ADOPT

### 1. The blueprint as the service value-stream-map analogue — ADOPT
Where lean value-stream mapping (02-womack) suits product flows, the **service blueprint** is the
right artifact for service-dominant client companies because it explicitly models the front-stage /
back-stage split and the customer journey. **Build implication:** for service-type companies the
operations engine generates a service blueprint (the 8-element line structure) as the canonical
process artifact — and exports it as a B&W flow diagram into `evidence/` (CLAUDE §3.10 requires
exactly these per-component flow diagrams).

### 2. Line of visibility / line of interaction → maps onto AutoFirm's own architecture — ADOPT
The front-stage/back-stage distinction maps precisely onto AutoFirm's client-facing deliverable vs
the agent back-stage orchestration, and onto B13's UI states (what the user sees) vs back-end data
flows. **Build implication:** every client service is modeled with an explicit line of visibility, so
the agent knows which steps must be polished (front-stage) vs internally efficient (back-stage) — and
ensures "nothing static, every visible element works" (CLAUDE §3.14) is anchored in a real process map.

### 3. Fail-point identification + time/tolerance standards — ADOPT (ties to jidoka + SLAs)
Shostack's fail-point analysis is the service-ops twin of jidoka stop-points (01-ohno) and the source
of SLA targets (B9). **Build implication:** the blueprint generator tags **fail points** and assigns
**time/tolerance standards** per step; these become (a) the places to add fail-closed guards and
(b) the numeric SLA thresholds tested in the support/success playbook.

## What AutoFirm should REJECT / bound
- **REJECT blueprinting as merely decorative documentation.** It must be *operational* — each fail
  point wires to a real guard and each tolerance to a tested threshold, else it is a static mockup
  (CLAUDE §3.14 "nothing static").
- **REJECT over-detailing back-stage for low-contact ops.** For product/low-contact industries the
  lean value-stream map (02) leads and the blueprint is optional — industry-parameterize (B12).

## Concrete build implications
- **Component:** `operations/service_blueprint` — generates the 8-line blueprint + fail-point list +
  per-step time tolerances; exports B&W HTML+PNG flow diagram to `evidence/`.
- **Contract:** each fail point → a fail-closed guard; each time-tolerance → a tested SLA threshold (B9).
- **Test:** the blueprint generator produces a valid, navigable blueprint for service panel rows;
  every declared fail point has an associated guard (no orphan fail points).
