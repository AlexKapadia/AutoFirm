# INDEX — Branch A8: Integration & Data Layer

Layer-1 foundations. Status: **seeded + summarized (awaiting QA-PASS / CRO sign-off)**.

## Questions
- **L1.A8.1** External-tool/API integration patterns & untrusted-input handling.
- **L1.A8.2** Multi-tenant data isolation (data-layer enforcement, not convention).
- **L1.A8.3** Secrets & credential scoping for autonomous agents.

## Sources (one folder each: SUMMARY.md + BEST-PARTS.md)
| # | Source | Primary question(s) | Tier |
|---|---|---|---|
| 01 | OWASP API Security Top 10 (2023) — API10 Unsafe Consumption | A8.1 | Moderate |
| 02 | NIST SP 800-204 — Microservices Security Strategies | A8.1 (A8.3) | High |
| 03 | Beurer-Kellner et al. (2025) — Design Patterns for Securing LLM Agents | A8.1 | Moderate |
| 04 | Debenedetti et al. (2025) — CaMeL: Defeating Prompt Injections by Design (SaTML 2026) | A8.1, A8.3 | Moderate->High |
| 05 | Debenedetti et al. (2024) — AgentDojo (NeurIPS 2024 D&B) | A8.1 | High |
| 06 | OWASP LLM Prompt Injection Prevention Cheat Sheet (2025) | A8.1 (A8.3) | Moderate |
| 07 | AWS Database Blog — Multi-tenant isolation with PostgreSQL RLS | A8.2 | Low->Moderate |
| 08 | PostgreSQL Official Docs — Row Security Policies (ddl-rowsecurity) | A8.2 | High |
| 09 | NIST SP 800-207 — Zero Trust Architecture | A8.3 | High |
| 10 | IETF RFC 8693 — OAuth 2.0 Token Exchange (+ RFC 6749) | A8.3 | High |

## Synthesis
See `SYNTHESIS.md` — surveyed alternative space + cited recommendation for each sub-question, the
cross-cutting fail-closed enforcement spine, evidence/metric hooks, and open re-verify items.

## Coverage note
All three sub-questions covered. Safety/correctness-critical claims (untrusted-by-default;
RLS bypass/FORCE behavior; per-session least-privilege scoping) each carry >= 3 independent
primary/standards sources per DEPTH-RUBRIC §1.
