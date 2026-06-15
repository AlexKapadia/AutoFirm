# BEST-PARTS — Agentic-AI legal risk framework

## ADOPT
- **A1. The seven controls map 1:1 onto AutoFirm's existing safety doctrine — adopt them as the legal
  acceptance checklist.** Each SPB control already has a CLAUDE.md home; B10 makes them **legally
  load-bearing**, not just good practice:
  - human oversight / sign-off on material decisions → CLAUDE.md §2 HITL + source 06 authority_guard.
  - decision perimeters / guardrails-by-design → source 06 `authority_scope`; CLAUDE.md §3.5 hard core.
  - inferencing-layer decision logs → A6.2 immutable append-only audit log.
  - automated circuit breakers / kill-switch → CLAUDE.md §5.6 global kill-switch.
  - contestability process → a `contest_outcome` workflow (new, see below).
  - AI-governance officer role → maps to the org engine (L2.ORG): a standing **Compliance/Legal-Oversight
    agent role** with veto, mirroring the North Star/CCO veto under fail-closed.
- **A2. Build the legal RISK REGISTER as a first-class artifact** keyed on the five categories
  (regulatory, contractual, tortious, data-security, IP). Every client-company build emits a populated
  risk register; this is a concrete deliverable of L2.B10 and feeds the §3.10 evidence showcase.
- **A3. Contestability workflow.** Add a `contest_outcome` capability so an affected party can challenge
  an agent decision (legally recommended AND aligns with EU AI Act Art. 86 right to explanation).

## REJECT / DEFER
- **R1. REJECT relying on contractual liability disclaimers as a shield** (Jones Walker: courts expand
  accountability). AutoFirm's posture is **prevent harm via controls**, not **disclaim it via fine print.**
- **R2. DEFER AI-risk insurance procurement** to an operational recommendation in the risk register, not
  a platform component.

## Build implication (concrete)
- **Component:** `legal/risk/risk_register.py` (5-category register) + `legal/risk/contest_outcome.py`;
  a standing `compliance_oversight` agent role with veto in the org engine.
- **Contract:** `LegalRiskRegister{ regulatory[], contractual[], tortious[], data_security[], ip[],
  mitigations_per_item, residual_risk }`.
- **Test:** assert every deployed client company has a non-empty risk register across all 5 categories;
  assert the kill-switch + audit-log + HITL controls are wired (integration test) before any
  contract-executing capability is enabled (fail-closed enablement gate).
