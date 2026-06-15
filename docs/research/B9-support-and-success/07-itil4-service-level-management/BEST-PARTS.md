# BEST-PARTS — ITIL Service Level Management

## ADOPT
- **The SLA / OLA / UC three-tier agreement model as AutoFirm's typed support-contract schema:**
  - **SLA** = customer-facing commitment (response time, resolution time, availability, service hours).
  - **OLA** = internal agreement between AutoFirm sub-agents/teams that underpins the SLA.
  - **UC** = contract with any external/third-party tool or vendor the support flow depends on.
  - **Build implication (L2.B9):** support tickets carry a typed `SLA{response_target, resolution_target, service_hours, priority}` contract; the engine computes **escalation points** deterministically from response/resolution targets + service-time profile (business-hours-aware clock). Unit-test the SLA clock at boundaries (pause outside service hours, breach detection exact to the second — CLAUDE §3.11 zero-numerical-error).
- **The tiered support model (Tier 1 desk → Tier 2/3 specialists) with explicit functional vs. hierarchical escalation** as the structure for AutoFirm's autonomous support org:
  - **Functional escalation** → route to a more-specialised agent (by skill/privilege).
  - **Hierarchical escalation** → notify a supervising/HITL agent on SLA-breach risk (ties to CLAUDE §2 HITL gates and fail-closed).
- **Priority = f(impact, urgency)** matrix to assign SLA targets deterministically per ticket.

## REJECT / ADAPT
- **ADAPT, don't adopt wholesale:** ITIL is IT-centric; AutoFirm must generalise the model to **any industry's** support (e.g. e-commerce returns, fintech disputes, restaurant complaints) — keep the SLA/OLA/escalation *abstraction*, parameterise the channels/priorities per industry panel (B12). Do NOT hard-code IT-incident vocabulary.
- **REJECT** treating ITIL as empirical proof of *efficacy* — it is a structural standard, so pair it with the metric evidence (CES/CSAT/FCR) for the quality bar.

## Why (cited)
- ITIL is the globally-adopted professional standard → the safe, general operating-model backbone for AutoFirm support across industries (CLAUDE §3.9). The SLA-clock determinism requirement directly drives a tests-with-teeth target.
