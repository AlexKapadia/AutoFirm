# SUMMARY — AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents

## Full citation
- **Title:** AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents.
- **Authors:** Edoardo Debenedetti, Jie Zhang, Mislav Balunovic, Luca Beurer-Kellner, Marc Fischer, Florian Tramer (ETH Zurich / SPY Lab).
- **Year:** 2024.
- **Venue:** NeurIPS 2024, Datasets and Benchmarks Track (peer-reviewed).
- **URL:** https://arxiv.org/abs/2406.13352 · proceedings: https://proceedings.neurips.cc/paper_files/paper/2024/hash/97091a5177d8dc64b1da8bf3e1f6fb54-Abstract-Datasets_and_Benchmarks_Track.html · site: https://agentdojo.spylab.ai/ · code: https://github.com/ethz-spylab/agentdojo

## Questions informed
- **L1.A8.1** Untrusted-input handling — the measurement harness for prompt-injection robustness of tool-using agents (the metric AutoFirm's integration-layer defenses are graded against).

## GRADE tier
**High.** Peer-reviewed NeurIPS Datasets & Benchmarks paper with open code and data (reproducible).

## Key claims (with locators)
1. **Definition:** an evaluation framework for "agents that execute tools over untrusted data"; "not a static test suite, but an extensible environment for designing and evaluating new agent tasks, defenses, and adaptive attacks."
2. **Scale (exact):** populated with **97 realistic tasks** (email client, e-banking navigation, travel bookings) and **629 security test cases**, plus attack/defense paradigms from the literature.
3. **Threat model:** "AI agents are vulnerable to prompt injection attacks where data returned by external tools hijacks the agent to execute malicious tasks." AgentDojo measures adversarial robustness against these.
4. It is the benchmark on which CaMeL (#04) reports 77% tasks-solved-with-provable-security (vs 84% undefended; arXiv:2503.18813 v2 abstract).

## Up/down-rate reasoning
- Up-rated: peer-reviewed venue; open, extensible, reproducible; the de-facto standard agentic-injection benchmark.
- No material down-rate; note it measures a specific class (indirect prompt injection via tool outputs), so it is necessary but not sufficient evidence of total integration-layer security.

## Reproducibility note
97 tasks / 629 security cases stated in the abstract and on the project site; benchmark fully open-source (run locally to re-derive any defense score).
