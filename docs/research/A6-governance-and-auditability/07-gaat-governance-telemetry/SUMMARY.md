# SUMMARY — Governance-Aware Agent Telemetry (GAAT) for Closed-Loop Enforcement

## Full citation
- **Title:** Governance-Aware Agent Telemetry for Closed-Loop Enforcement in Multi-Agent AI Systems
- **Authors:** Anshul Pathak; Nishant Jain.
- **Year:** 2026 (submitted 6 April 2026).
- **Venue:** arXiv preprint, arXiv:2604.05119 [cs.MA].
- **URL:** https://arxiv.org/abs/2604.05119

## Question(s) informed
- **L1.A6.3** Governance-aware telemetry & closed-loop enforcement (the central source).
- Feeds L2.A6 (audit + enforcement) and L2.A7 (safety/control stack).

## GRADE tier
**Moderate.** arXiv preprint (not yet peer-reviewed) with a full methods + empirical section. Up-rated for: a formal model with proven properties, an empirical evaluation on 12,000 production traces, and baseline comparisons; down-rated one step for non-peer-reviewed status. Quantitative claims are flagged for re-verification before AutoFirm relies on the exact numbers.

## Core problem — the "observe-but-do-not-act gap" (quoted)
Existing observability tools (OpenTelemetry, Langfuse) "collect telemetry but treat governance as a downstream analytics concern, not a real-time enforcement target," so "policy violations [are] detected only after damage occurs."

## Five-layer reference architecture (four named components)
1. **Governance Telemetry Schema (GTS):** extends OpenTelemetry spans with governance-specific attributes.
2. **Real-time policy violation detection engine:** OPA-compatible declarative rules, sub-200 ms latency.
3. **Governance Enforcement Bus (GEB):** graduated interventions (escalating responses, not binary allow/deny).
4. **Trusted Telemetry plane:** cryptographic provenance tracking of the telemetry itself.

## Reported quantitative results (flagged: preprint — re-verify before relying)
- Violation Prevention Rate (VPR): **98.3% (±0.7%)** on 5,000 synthetic flows; **99.7%** on 12,000 empirical production traces.
- Detection latency: **8.4 ms median (P50)**.
- End-to-end enforcement latency: **127 ms median (P50), 192 ms (P99)** — i.e. under the 200 ms target.
- False positive rate: **0.9%**. Omission detection: **92.3%**. Replay prevention: **99.1%**.
- Baselines: GAAT VPR exceeds NeMo Guardrails (78.8%, +19.5 pp), centralized gateways (89.4%), Cedar (76.8%), dashboard-only (27.1%); reported 97.6% reduction in violation escape rate.

## Reproducibility note
Abstract, component list, and the metrics above are from the arXiv:2604.05119 abstract + HTML body (verified to resolve and report these numbers, 2026-06-15). Numbers are preprint-stage and must be independently reproduced before AutoFirm cites them as evidence.
