# INDEX — A2 Agent Communication & Workflow

Branch: `docs/research/A2-agent-communication-and-flow/`
Owner: Research Analyst, branch A2. Single-writer. Status: **seeded (Layer 1), pending QA**.

## Questions (Layer 1)
- **L1.A2.1** Agent communication protocols & message schemas (typed contracts, ACL lineage)
- **L1.A2.2** Workflow/DAG vs emergent coordination; reliability of each
- **L1.A2.3** Standardization-of-outputs as coordination (org-theory <-> MAS bridge)

## Sources (one folder each: SUMMARY.md + BEST-PARTS.md)
| # | Slug | Source | Tier | Informs |
|---|---|---|---|---|
| 01 | interop-protocols-survey | Ehtesham et al. 2025, arXiv:2505.02279 (MCP/ACP/A2A/ANP) | Moderate | A2.1, A2.2 |
| 02 | mast-failure-taxonomy | Cemri et al. 2025, NeurIPS D&B / arXiv:2503.13657 (MAST) | High | A2.2, A2.1 |
| 03 | semantic-view-protocols | Yuan et al. 2026, arXiv:2604.02369 | Moderate | A2.1, A2.3 |
| 04 | fipa-acl-standard | FIPA/IEEE SC00061G + SC00037J | High | A2.1, A2.3 |
| 05 | contract-net-protocol | Smith 1980, IEEE TC C-29(12), DOI 10.1109/TC.1980.1675516 | High | A2.2, A2.1 |
| 06 | mintzberg-coordination | Mintzberg 1979, The Structuring of Organizations | High | A2.3, A2.2 |
| 07 | anthropic-multi-agent-engineering | Anthropic Eng. 2025 (Claude research system) | Low-Mod | A2.2, A2.1 |
| 08 | deterministic-vs-dynamic-orchestration | Microsoft 2026 (Conductor) | Low-Mod | A2.2 |

## Synthesis
See `SYNTHESIS.md` — surveyed space + cited recommendation: typed/signed/intent-bearing message
envelope over a declared deterministic DAG (Contract-Net for dynamic allocation), coordinated by
standardization of typed stage outputs, audited end-to-end.
