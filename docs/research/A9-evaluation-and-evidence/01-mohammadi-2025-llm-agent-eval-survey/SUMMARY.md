# SUMMARY — Evaluation and Benchmarking of LLM Agents: A Survey

## Full citation
- **Title:** Evaluation and Benchmarking of LLM Agents: A Survey
- **Authors:** Mahmoud Mohammadi, Yipeng Li, Jane Lo, Wendy Yip
- **Year:** 2025
- **Venue:** Proceedings of the 31st ACM SIGKDD Conference on Knowledge Discovery and Data Mining V.2 (KDD '25), Aug 3-7, 2025, Toronto, ON, Canada
- **DOI/URL:** https://doi.org/10.1145/3711896.3736570 | arXiv:2507.21504 | https://arxiv.org/abs/2507.21504

## Questions informed
- **L1.A9.1** Agent-evaluation taxonomy (what vs. how) & reliability/reproducibility pitfalls (PRIMARY)
- Supporting context for L1.A9.2 (consistency / repeat-trial metrics).

## GRADE tier: Moderate
Peer-reviewed at a top venue (KDD '25) -- this would normally up-rate to High. Down-rated to
Moderate because it is a *survey* (secondary synthesis of others' benchmarks), not a primary
controlled study, and the load-bearing taxonomy is a conceptual framework rather than a measured
result. Up-rate factor: large, consistent coverage of the benchmark landscape (50+ benchmarks
catalogued) corroborated by the independent Cao et al. (source 02) survey.

## Key claims (exact, with locators)

### The two-dimensional evaluation taxonomy (the "what vs. how" answer to L1.A9.1)
Evaluation Objectives -- WHAT to evaluate:
- Agent Behavior: task completion, output quality, latency & cost.
- Agent Capabilities: tool use, planning and reasoning, memory and context retention,
  multi-agent collaboration.
- Reliability: consistency, robustness.
- Safety and Alignment: fairness, harm/toxicity/bias, compliance and privacy.

Evaluation Process -- HOW to evaluate:
- Interaction Mode: static & offline vs. dynamic & online evaluation.
- Evaluation Data: synthetic and real-world datasets, domain-specific benchmarks.
- Metrics Computation: code-based, LLM-as-a-Judge, human-in-the-loop.
- Evaluation Tooling: DeepEval, InspectAI, Phoenix, GALILEO, OpenAI Evals, Azure AI Foundry.
- Evaluation Contexts: controlled simulations -> open-world settings.

### Reliability / reproducibility pitfalls (named in the survey)
- Stochasticity overhead: "Because LLM-based agents are inherently stochastic, measuring
  consistency requires executing the same task multiple times and observing the variation in
  outcomes. This introduces significant evaluation overhead: running multiple trials per input
  can be computationally expensive."
- pass^k consistency metric: "a stricter measure of consistency is whether the agent
  succeeds in all k attempts. This is formalized in the tau-benchmark as the pass^k metric, which
  better captures the consistency requirements of mission-critical deployments." (Contrast with
  pass@k = success in *at least one* of k attempts -- source 05.)
- Coarse success-rate signal: task-completion metrics give "limited fine-grained insight
  into failures, especially when most models achieve low success rates."
- Semantic gaps in tool-call evaluation: AST-correctness checks "may miss semantic errors,
  such as incorrect or hallucinated parameter values."
- Enterprise blind spots: "predictable reliability, compliance with regulations, data
  security, and maintainability ... are usually overlooked during evaluation."

### Metric inventory (directly reusable)
Success Rate (SR), Task Success Rate, Pass Rate, pass@k, pass^k, Task Goal Completion
(TGC), Tool Selection Accuracy, Invocation Accuracy, Retrieval Accuracy, MRR, NDCG, Progress
Rate, Step Success Rate, Factual Recall Accuracy, Consistency Score.

### Benchmark inventory (relevant to a platform that builds software companies)
SWE-bench, ScienceAgentBench, CORE-Bench, PaperBench; WebArena, BrowserGym, WebCanvas,
VisualWebArena; TaskBench, FlowBench, ToolBench, API-Bank; LongEval, SocialBench (40+ turns),
LoCoMo (600+ turns); AgentHarm, AgentDojo, SafeAgentBench, CoSafe; tau-benchmark, HELM,
TheAgentCompany; Berkeley Function-Calling Leaderboard, Holistic Agent Leaderboard.

## Reproducibility note
Taxonomy and metric/benchmark lists extracted from the arXiv HTML (v1). The two-axis structure
and the pass^k / tau-benchmark definition are reproducible from the "Evaluation Objectives" and
"Reliability" sections. No private data involved.
