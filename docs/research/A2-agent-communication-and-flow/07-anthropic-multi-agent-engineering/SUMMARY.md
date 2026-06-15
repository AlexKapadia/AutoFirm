# SUMMARY — How We Built Our Multi-Agent Research System (Anthropic)

## Full citation
- **Title:** How we built our multi-agent research system
- **Author/Org:** Anthropic (Engineering)
- **Year:** 2025
- **Venue:** Anthropic Engineering blog (vendor primary, practitioner)
- **URL:** https://www.anthropic.com/engineering/multi-agent-research-system

## Questions it informs
- **L1.A2.2** (workflow vs emergent coordination; reliability of orchestrator-worker — PRIMARY
  practitioner evidence, on the exact substrate AutoFirm uses: Claude)
- L1.A2.1 (delegation message content) and A3 (statefulness/resume) — supporting

## GRADE tier: Low-Moderate (vendor practitioner source)
Vendor blog (not peer-reviewed) -> tier Low by DEPTH-RUBRIC S2, but **directly about Claude**
(AutoFirm's runtime) and reports concrete quantitative results, so up-rated to Low-Moderate for
substrate-specific engineering claims. Its general reliability claims are corroborated by the
peer-reviewed MAST (source 02) and the deterministic-orchestration source (08). Not used as a
sole basis for any safety-critical claim.

## Key claims (exact quotes + numbers)

**Architecture:** orchestrator-worker — a lead agent plans and spins up subagents in parallel,
then synthesizes; a separate citation pass runs after.

**Delegation contract (the comms lesson):** "Each subagent needs an objective, an output format,
guidance on the tools and sources to use, and clear task boundaries." Without this detail,
"subagents misinterpreted the task or performed the exact same searches as other agent[s]."

**Compact-result / anti-telephone pattern:** to avoid the "'game of telephone'", "subagents call
tools to store their work in external systems, then pass lightweight references back." A separate
"CitationAgent ... processes the documents and research report to identify specific locations for
citations."

**Statefulness / resume:** "we can't just restart from the beginning: restarts are expensive and
frustrating for users. Instead, we built systems that can resume from where the agent was."
Context persistence: an agent can "save its plan to Memory to persist the context, since if the
context window exceeds 200,000 tokens it will be truncated."

**Quantitative results:**
- "token usage by itself explains **80% of the variance**" (in BrowseComp eval performance).
- Multi-agent system "outperformed single-agent Claude Opus 4 by **90.2%**" on the internal
  research eval.
- Parallelization "cut research time by up to **90%** for complex queries."
- Cost: "agents typically use about **4x** more tokens than chat interactions, and multi-agent
  systems use about **15x** more tokens."

## Reproducibility note
Quotes/numbers are verbatim from the Anthropic engineering post (fetched). These are vendor-
reported figures on an internal eval; treat as directional, corroborated by MAST for the
qualitative coordination lessons. Numbers re-verifiable at the source URL.
