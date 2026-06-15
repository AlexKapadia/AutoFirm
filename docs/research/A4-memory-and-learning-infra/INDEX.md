# A4 — Memory & Learning Infrastructure (Layer 1) — Source Index

Owner: A4 Research Analyst. Status: AMBER->GREEN hardening pass applied (4 primary sources added to
close the AMBER gaps: VF source-strength, context-limit corroboration, RL-on-memory coverage).

| Q | Folder | Source | Venue (tier) |
|---|---|---|---|
| A4.1 | 01-storage-to-experience-survey | Storage to Experience memory survey | ACL 2026 Findings (Mod-High) |
| A4.1 | 02-coala-cognitive-architectures | CoALA | TMLR 2024 (High) |
| A4.1/2/3 | 03-a-mem-agentic-memory | A-MEM | NeurIPS 2025 (High) |
| A4.1/2/3 | 04-generative-agents | Generative Agents | UIST 2023 (High) |
| A4.2 | 05-rag-lewis-2020 | RAG (Lewis et al.) | NeurIPS 2020 (High) |
| A4.2 | 06-rag-survey-gao | RAG: A Survey | arXiv 2023-24 (Mod) |
| A4.2 | 07-dense-passage-retrieval | DPR | EMNLP 2020 (High) |
| A4.2 | 08-lost-in-the-middle | Lost in the Middle | TACL 2024 (High) |
| A4.1/2 | 09-memgpt-os | MemGPT | arXiv 2023 (Mod) |
| A4.3 | 10-reflexion | Reflexion | NeurIPS 2023 (High) |
| A4.3 | 11-expel-experiential-learning | ExpeL | AAAI 2024 (High) |
| A4.4 | 12-ltm-security-survey | LTM Memory Security Survey | arXiv 2026 (Mod) |
| A4.4 | 13-agentpoison | AgentPoison | NeurIPS 2024 (High) |
| A4.4 | 14-machine-unlearning-verification | Unlearning Verification survey | arXiv 2025 (Mod) |
| A4.3 | 18-voyager-skill-library | Voyager (skill-library lifelong learning) | TMLR 2024 (High) |
| A4.2 | 17-ruler-real-context-size | RULER | COLM 2024 (High) |
| A4.4 | 15-sisa-machine-unlearning | Machine Unlearning (SISA) | IEEE S&P 2021 (High) |
| A4.4 | 16-cao-yang-unlearning-and-rtbf | Cao & Yang + GDPR Art. 17 / CCPA | IEEE S&P 2015 + EU/US law (High) |

Synthesis: SYNTHESIS.md (surveyed space + recommendation per sub-question + cross-branch joins).

QA notes:
- A4.4 safety/correctness-critical VF claim now has >=3 independent PRIMARIES (SISA 15 — IEEE S&P
  2021; Cao-Yang 16A — IEEE S&P 2015; GDPR Art. 17 / CCPA 16B — primary law), plus surveys 12, 14 and
  primary attack work AgentPoison 13. No critical claim rests on a survey alone (AMBER fix).
- A4.3 no-fine-tune learning now has 3 independent peer-reviewed primaries (Reflexion 10, ExpeL 11,
  Voyager 18 — TMLR 2024); RL-on-memory family is cited, not silently omitted (AMBER fix).
- A4.2 context-limit axiom now has 2 independent primaries (Lost-in-the-Middle 08, RULER 17 — COLM
  2024) with distinct failure signatures (AMBER fix).
- Exact formulae transcribed: A-Mem note/link/evolution/retrieval (03); Generative Agents
  recency 0.995 / relevance / importance, alpha=1, reflection threshold 150 (04); DPR dot-product (07);
  RAG-Sequence marginalization (05).
- Numbers: A-Mem LoCoMo F1 (03); Reflexion 91.0/80.1, 130/134, 20% (10); DPR +9-19% top-20 (07);
  AgentPoison >80% ASR / <0.1% poison / <1% benign (13).
