# INDEX — A1 Multi-Agent Orchestration & Coordination (Layer 1)

Branch owner: Research Analyst (A1). Status: SEEDED + DRAFTED (awaiting senior review + independent QA
per RESEARCH-PROGRAM.md section 2/3; not yet CRO-marked "answered").

## Questions covered
- L1.A1.1 Taxonomy of MAS coordination (patterns, strengths, failure modes)
- L1.A1.2 When does multi-agent beat a single strong agent (evidence)
- L1.A1.3 Hierarchical/role-based orchestration (HALO-style) and dynamic role assignment
- L1.A1.4 Coordination-cost / context-flooding (information-processing view)

## Sources (one folder each: SUMMARY.md + BEST-PARTS.md)
| # | Slug | Source | Tier | Primary for |
|---|---|---|---|---|
| 01 | tran-collaboration-mechanisms-survey | Tran et al. 2025, Multi-Agent Collaboration Mechanisms: A Survey of LLMs (arXiv:2501.06322) | Moderate | A1.1, A1.4 |
| 02 | anthropic-multi-agent-research-system | Anthropic 2025, How we built our multi-agent research system | Low-Moderate | A1.1, A1.2, A1.4 |
| 03 | halo-hierarchical-orchestration | Hou, Tang, Wang 2025, HALO (arXiv:2505.13516) | Moderate | A1.3, A1.1 |
| 04 | cemri-mast-failure-taxonomy | Cemri et al. 2025, Why Do Multi-Agent LLM Systems Fail? (arXiv:2503.13657; OpenReview) | High | A1.1, A1.2 |
| 05 | du-multiagent-debate | Du, Li, Torralba, Tenenbaum, Mordatch 2023/2024, Multiagent Debate (ICML 2024; arXiv:2305.14325) | High | A1.1, A1.2 |
| 06 | malone-crowston-coordination-theory | Malone & Crowston 1994, The Interdisciplinary Study of Coordination (ACM Comput. Surv. 26(1):87-119) | High | A1.4, A1.1 |
| 07 | galbraith-information-processing-view | Galbraith 1974, Organization Design: An Information Processing View (Interfaces 4(3):28-36) | High | A1.4 |
| 08 | smith-contract-net-protocol | Smith 1980, The Contract Net Protocol (IEEE Trans. Computers C-29(12):1104-1113) | High | A1.1 |
| 09 | tian-orchestration-vs-single-llm | Tian et al. 2025, Beyond the Strongest LLM (arXiv:2509.23537) | Moderate | A1.2 |

## Source-count check (DEPTH-RUBRIC section 1)
- Critical claim "multi-agent can beat a single strong agent": 02, 03, 05, 09 (+ clinical study) = 4+ independent. PASS.
- Critical claim "failure is mostly inter-agent design, not model quality": 04 (peer-reviewed), 01, 02 = 3 independent. PASS.
- Critical claim "coordination cost scales with information-processing demand": 06, 07, 02 = 3 independent. PASS.
- Architecture choice "hierarchical/role-based backbone": 02, 03, 01 = 3. PASS.

## See SYNTHESIS.md for the surveyed space, adopt/reject decisions, and the AutoFirm recommendation.
