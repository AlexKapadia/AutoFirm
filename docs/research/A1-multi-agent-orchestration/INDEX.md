# INDEX — A1 Multi-Agent Orchestration & Coordination (Layer 1)

Branch owner: Research Analyst (A1). Status: SEEDED + DRAFTED + AMBER-GAPS-CLOSED (awaiting
re-review per RESEARCH-PROGRAM.md section 2/3; not yet CRO-marked "answered").

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
| 10 | hayes-roth-blackboard-architecture | Hayes-Roth 1985, A Blackboard Architecture for Control (Artificial Intelligence 26(3):251-321) | High | A1.1 (blackboard pattern, primary) |
| 11 | bonabeau-swarm-intelligence | Bonabeau, Dorigo & Theraulaz 1999, Swarm Intelligence: From Natural to Artificial Systems (Oxford/SFI) | High | A1.1 (swarm/stigmergic pattern, primary) |
| 12 | kim-liu-scaling-agent-systems | Kim et al. 2026 (20 authors incl. Y. Kim, X. Liu corresp.; Google Research / Google DeepMind / MIT), Towards a Science of Scaling Agent Systems (arXiv:2512.08296) | Moderate-High | A1.2 (multi-vs-single + cost corroboration) |

## Source-count check (DEPTH-RUBRIC section 1)
- Critical claim "multi-agent can beat a single strong agent": 02, 03, 05, 09, 12 (+ clinical study) = 5+ independent. PASS.
- Critical claim "failure is mostly inter-agent design, not model quality": 04 (peer-reviewed), 01, 02 = 3 independent. PASS.
- Critical claim "coordination cost scales with information-processing demand": 06, 07, 02, 12 = 4 independent. PASS.
- Important claim "multi-agent cost is token-dominated w/ diminishing returns": 02, 12 = 2 independent (12 is a controlled 3-model-family study, no longer single-weak-source). PASS.
- Architecture choice "hierarchical/role-based backbone": 02, 03, 01, 12 (coordinated > leaderless, 4.4x vs 17.2x per the Google Research blog) = 4. PASS.
- Full-method-space coverage (DEPTH-RUBRIC section 4): all 6 ontology patterns surveyed w/ a primary source -- blackboard (10), swarm (11) close the prior two gaps. PASS.

## AMBER gaps closed in this pass
1. Blackboard pattern was DEFERRED without a primary source -> added 10 (Hayes-Roth 1985, peer-reviewed primary).
2. Swarm/stigmergic pattern (named in L1.A1.1 enumeration) was absent -> added 11 (Bonabeau/Dorigo/Theraulaz 1999, canonical primary).
3. Cost/diminishing-returns + multi-vs-single leaned on the Low-Moderate Anthropic blog (02) -> added 12 (Google Research, 3 model families) as independent corroboration.

## See SYNTHESIS.md for the surveyed space, adopt/reject decisions, and the AutoFirm recommendation.
