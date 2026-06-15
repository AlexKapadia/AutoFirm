# SUMMARY — How we built our multi-agent research system (Anthropic)

## Full citation
- **Title:** How we built our multi-agent research system
- **Authors/Org:** Anthropic (Engineering blog) — authored team incl. Jeremy Hadfield, Barry Zhang,
  Kenneth Lien, Florian Scholz, Jeremy Fox, Daniel Ford (as bylined).
- **Year:** 2025
- **Venue:** Anthropic Engineering blog (vendor primary engineering report).
- **URL:** https://www.anthropic.com/engineering/multi-agent-research-system

## Questions informed
- **L1.A1.1** (orchestrator-worker pattern) — PRIMARY exemplar.
- **L1.A1.2** (when multi-agent beats single agent) — PRIMARY quantitative evidence.
- **L1.A1.4** (coordination cost / token economics) — PRIMARY.
- L1.A1.3 (role/dynamic spawn) — supporting.

## GRADE tier
**Low–Moderate.** Vendor engineering report (down-rate: not peer-reviewed, vendor incentive,
internal eval not externally reproducible). UP-rated for being a **primary** account of a
production system with concrete numbers, and corroborated independently for the central
multi-beats-single claim by Cemri 2025 (04), the clinical-workload study, and Tian 2025 (09).
**Never used as a sole basis** for the critical multi-beats-single claim.

## Key claims (exact quotes + numbers)

### Architecture
- Orchestrator-worker: "a lead agent coordinates the process while delegating to specialized
  subagents that operate in parallel."
- Dynamic spawn by complexity: "Simple fact-finding requires just 1 agent with 3-10 tool calls,
  direct comparisons might need 2-4 subagents with 10-15 calls each, and complex research might use
  more than 10 subagents." Lead model = Claude Opus 4; subagents = Claude Sonnet 4.

### Performance (L1.A1.2)
- "a multi-agent system with Claude Opus 4 as the lead agent and Claude Sonnet 4 subagents
  outperformed single-agent Claude Opus 4 by **90.2%** on our internal research eval."

### Token economics (L1.A1.4) — the key explanatory finding
- "three factors explained **95%** of the performance variance in the BrowseComp evaluation … token
  usage by itself explains **80%** of the variance, with the number of tool calls and the model
  choice as the two other explanatory factors."
- Cost: "agents typically use about **4×** more tokens than chat interactions, and multi-agent
  systems use about **15×** more tokens than chats."

### When multi-agent EXCELS vs FAILS (L1.A1.2)
- EXCELS: "valuable tasks that involve heavy parallelization, information that exceeds single
  context windows, and interfacing with numerous complex tools"; "breadth-first queries that involve
  pursuing multiple independent directions simultaneously."
- POOR FIT: "domains that require all agents to share the same context or involve many dependencies
  between agents … most coding tasks involve fewer truly parallelizable tasks than research."

### Failure modes / engineering lessons (L1.A1.1)
- Early agents spawned "50 subagents for simple queries," scoured "the web endlessly for nonexistent
  sources," continued "when they already had sufficient results."
- Subagents "duplicate work, leave gaps, or fail to find necessary information" without detailed task
  descriptions. Wrong-tool-source: "an agent searching the web for context that only exists in Slack
  is doomed from the start."
- Synchronous bottleneck: "lead agents execute subagents synchronously, waiting for each set …
  creates bottlenecks."

## Reproducibility note
All numbers are exact quotes from the Anthropic engineering page (fetched via WebFetch). The 90.2%
and 80%/95% variance figures are internal-eval / BrowseComp figures and are tier-Low alone; they are
corroborated directionally by independent sources for the multi-beats-single conclusion.
