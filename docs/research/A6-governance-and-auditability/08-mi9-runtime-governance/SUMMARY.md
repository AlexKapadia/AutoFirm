# SUMMARY — MI9: An Integrated Runtime Governance Framework for Agentic AI

## Full citation
- **Title:** MI9 — Agent Intelligence Protocol: Runtime Governance for Agentic AI Systems (a.k.a. "MI9: An Integrated Runtime Governance Framework for Agentic AI")
- **Authors:** Charles L. Wang; Trisha Singhal; Ameya Kelkar; Jason Tuo.
- **Year:** 2025 (v4).
- **Venue:** arXiv preprint, arXiv:2508.03858 [cs.AI]. License CC BY 4.0.
- **URL:** https://arxiv.org/abs/2508.03858 (PDF: https://arxiv.org/pdf/2508.03858)

## Question(s) informed
- **L1.A6.3** Governance-aware telemetry & closed-loop enforcement (runtime-governance alternative).
- Feeds L2.A7 (safety/control stack) and L2.ORG (dynamic audited agent org).

## GRADE tier
**Moderate.** arXiv preprint with a worked framework; up-rated for completeness of the runtime-governance component model and alignment with independent work (GAAT, Verifiability-First); down-rated one step for non-peer-reviewed status. Used here for architectural patterns, not for quantitative claims.

## Core thesis
Addresses the gap between **training-time alignment** and **deployment-time (runtime) safety**: agents need real-time oversight mechanisms beyond initial training, with proportional (sliding-scale) interventions rather than binary allow/deny.

## Six runtime-governance components
1. **Agency-Risk Index scoring** — quantifies an agent's capability and potential harm vectors to inform containment decisions.
2. **Agent Semantic Telemetry** — captures execution traces (goals, actions, environmental state changes) for auditability.
3. **Continuous Authorization Monitoring** — dynamically re-evaluates agent permissions against current context and risk.
4. **FSM-based Conformance Engine** — finite-state machines enforce policy constraints on agent state transitions.
5. **Goal-Conditioned Drift Detection** — flags when agent behaviour diverges from declared objectives via semantic analysis.
6. **Graduated Containment** — proportional restrictions: capability reduction → isolation → termination, by detected risk.

## Reproducibility note
Component list from the arXiv:2508.03858 abstract + body (CC BY 4.0). A reviewer can re-derive from the PDF. Treated as a design-pattern source; no relied-upon quantitative claim is drawn from it.
