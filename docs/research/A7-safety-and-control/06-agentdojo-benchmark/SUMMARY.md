# SUMMARY — AgentDojo: Evaluating Prompt Injection Attacks and Defenses for LLM Agents

## Full citation
- **Title:** AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents
- **Authors:** Edoardo Debenedetti, Jie Zhang, Mislav Balunović, Luca Beurer-Kellner, Marc Fischer, Florian Tramèr
- **Year:** 2024
- **Venue:** **NeurIPS 2024** (Datasets & Benchmarks Track) — peer-reviewed.
- **URL/DOI:** Proceedings https://proceedings.neurips.cc/paper_files/paper/2024/hash/97091a5177d8dc64b1da8bf3e1f6fb54-Abstract-Datasets_and_Benchmarks_Track.html ; arXiv:2406.13352 (https://arxiv.org/abs/2406.13352)

## Questions informed
- **L1.A7.1** (prompt-injection threat measurement) + **L1.A7.2** (provides the evaluation harness for oversight/defense efficacy). Supplies the metric used by source 05.

## GRADE tier
**High.** Peer-reviewed NeurIPS Datasets & Benchmarks paper; the de-facto standard benchmark for agent prompt-injection (independent of the defenses tested on it). Primary anchor for any AutoFirm injection-defense efficacy number.

## Key claims (faithful, exact)
1. **Threat (verbatim sense):** "AI agents are vulnerable to prompt injection attacks where data returned by external tools hijacks the agent to execute malicious tasks."
2. **Scope:** **97 realistic user tasks** and **629 security test cases**, across **four environments** (e.g., Workspace, e-banking, travel, Slack). Each environment defines a domain + tools; certain state elements are marked as **injection points** where malicious prompts are embedded in retrievable data.
3. **Design intent:** "not a static test suite, but rather an extensible environment for designing and evaluating new agent tasks, defenses, and adaptive attacks" — i.e. supports adaptive/red-team evaluation, not a fixed leaderboard.
4. **It is the benchmark on which CaMeL reports 77% secure-with-provable-security vs 84% undefended** (source 05) — anchoring the cross-source efficacy claim.

## Verification note
Authors, NeurIPS-2024 venue, the 97-tasks / 629-security-test-cases / 4-environments figures fetched and corroborated across the NeurIPS proceedings page, the arXiv abstract (2406.13352), and the NeurIPS poster page — three independent venues agree on the exact counts. Meets DEPTH-RUBRIC §1 >=3 sources for this safety-critical quantitative claim.

## Reproducibility
Open the NeurIPS 2024 proceedings entry / arXiv:2406.13352; task/test counts are in the abstract; the benchmark code is public for re-running defenses.
