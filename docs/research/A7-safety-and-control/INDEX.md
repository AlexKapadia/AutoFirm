# INDEX — A7 Safety & Control of Autonomous Agents

Branch root for QUESTION-ONTOLOGY L1.A7. Status legend: SEEDED (written, not yet QA-PASSED).
Single-writer: this branch is owned by the A7 Research Analyst.

## Sub-questions
- **L1.A7.1** Threat models for agentic AI (TRiSM; prompt injection; tool misuse) — SEEDED
- **L1.A7.2** Oversight architectures (verifiability-first, audit agents, kill-switch, HITL) — SEEDED
- **L1.A7.3** Fail-closed design patterns & least-privilege for agents — SEEDED

## Sources (one folder each)
| # | Folder | Primary Q | Tier | Citation of record |
|---|---|---|---|---|
| 01 | 01-trism-agentic-ai | A7.1 | Mod->High | Raza et al. 2025/26, ScienceDirect PII S2666651026000069 / arXiv:2506.04133 |
| 02 | 02-owasp-llm01-prompt-injection | A7.1 | High | OWASP Gen AI Security Project, LLM01:2025 |
| 03 | 03-sok-attack-surface-agentic-ai | A7.1 | Mod | Dehghantanha & Homayoun 2026, arXiv:2603.22928 |
| 04 | 04-nist-ai-600-1-genai-profile | A7.1 | High | NIST AI 100-1 (2023) + AI 600-1 (2024) |
| 05 | 05-camel-defeating-prompt-injection-by-design | A7.3 | Mod->High | Debenedetti et al. 2025, arXiv:2503.18813 |
| 06 | 06-agentdojo-benchmark | A7.1/A7.2 | High | Debenedetti et al., NeurIPS 2024, arXiv:2406.13352 |
| 07 | 07-verifiability-first-agents | A7.2 | Mod | Gupta 2025, arXiv:2512.17259 |
| 08 | 08-ai-kill-switch-autoguard | A7.2 | Mod | Lee & Park 2025, arXiv:2511.13725 |
| 09 | 09-saltzer-schroeder-protection-principles | A7.3 | High | Saltzer & Schroeder 1975, Proc. IEEE 63(9), DOI 10.1109/PROC.1975.9939 |
| 10 | 10-formal-mcp-security-framework | A7.3 | Mod | Acharya & Gupta 2026, arXiv:2604.05969 |

## Synthesis
- SYNTHESIS.md — surveyed space + integrated 3-layer (PREVENT/DETECT/CONTAIN) fail-closed
  recommendation feeding L2.A7; cross-branch edges; source-count compliance.

## Outstanding (for QA)
- TRiSM exact journal name/volume unresolved (ScienceDirect 403); arXiv DOI used as record.
- TRiSM CSS/TUE formulae + Verifiability-First OPERA numbers deferred (need full PDFs) — flagged,
  not fabricated.
