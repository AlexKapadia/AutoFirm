# BEST-PARTS — Anthropic multi-agent research system

## ADOPT
1. **Orchestrator-worker as AutoFirm's primary topology** — a lead agent plans, spawns N specialized
   subagents in parallel, and synthesizes. This *is* CLAUDE.md §2/§4.1. Cite for L2.A1.
2. **Dynamic, complexity-scaled spawn** — "1 agent for simple fact-finding … >10 for complex
   research." *Build implication:* AutoFirm's org engine (L2.ORG) sizes the agent team to task
   complexity rather than a fixed roster; the orchestrator decides fan-out (matches CLAUDE.md §4.3
   "fan out, then fan in").
3. **Token usage is the dominant performance lever (80% of variance)** — *Build implication:* the
   A9 evaluation harness must **log and report token usage per run** as a first-class metric, and the
   evidence/ showcase must chart performance-vs-token-budget. This reframes "protect your context
   window" (CLAUDE.md §3.1) as the *empirically dominant* design constraint, not a style preference.
4. **The breadth-first-vs-shared-context rule** — adopt as the **routing predicate** for when
   AutoFirm parallelizes: parallelize independent breadth-first subtasks; serialize / single-agent
   tasks with heavy inter-dependencies or shared mutable context. Directly drives L2.A1 routing logic.

## REJECT / mitigate
- **Synchronous subagent execution** — REJECT as the long-run default: it "creates bottlenecks."
  AutoFirm should prefer asynchronous fan-out with a join barrier (still reconciled by the orchestrator).
- **Naive spawn heuristics** — REJECT: "50 subagents for simple queries" is a real failure. AutoFirm
  needs a **span cap** (CLAUDE.md L2.ORG span caps) and an effort-scaling rule encoded as policy.

## Build implication (concrete)
- L2.A1 routing predicate (parallelize iff breadth-first & low-dependency & exceeds one context),
  a **span cap** + effort heuristic in the org engine, and a **token-budget metric** wired into the
  A9 harness and the evidence/ showcase. The 15× cost multiplier sets the economic bar: multi-agent
  is justified only when the quality gain clears that cost (ties to A9 cost-accuracy reporting).
