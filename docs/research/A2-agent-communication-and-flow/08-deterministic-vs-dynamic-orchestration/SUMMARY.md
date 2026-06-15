# SUMMARY — Conductor: Deterministic Orchestration for Multi-Agent AI Workflows

## Full citation
- **Title:** Conductor: Deterministic orchestration for multi-agent AI workflows
- **Author/Org:** Microsoft (Open Source Blog)
- **Year:** 2026 (14 May 2026)
- **Venue:** Microsoft Open Source Blog (vendor practitioner)
- **URL:** https://opensource.microsoft.com/blog/2026/05/14/conductor-deterministic-orchestration-for-multi-agent-ai-workflows/

## Questions it informs
- **L1.A2.2** (workflow/DAG vs emergent coordination; reliability of each — PRIMARY for the
  "DAG/declared topology" side of the comparison)

## GRADE tier: Low-Moderate (vendor practitioner)
Vendor engineering blog (tier Low per S2). Up-rated to Low-Moderate because its core claim
(deterministic routing reduces cost/latency/unpredictability) is corroborated by peer-reviewed
MAST (FC1 specification/design = 41.77%, source 02) and by independent practitioner analyses.
Not a sole basis for any safety-critical claim.

## Key claims (exact quotes)

- **Problem with LLM-as-orchestrator:** "dynamic orchestration adds cost, latency, and
  unpredictability that can work against you." Three accumulating costs when the orchestrator is
  an LLM: token consumption per routing decision, latency waiting for the plan, and
  "non-deterministic routing makes workflows harder to audit and control."

- **Recommended inversion:** "Orchestration should be deterministic and inspectable. Not an LLM
  making routing decisions." Conductor uses "deterministic routing" where "the orchestration
  layer consumes zero tokens," and the workflow topology is "declared, not discovered at
  runtime." The LLM "operates only within individual agent nodes," while "the routing graph
  remains fixed and human-readable."

- **When determinism fits (explicit tradeoff):** suits workflows "with known structure" — e.g.
  "code review pipelines, design document generation, research assistants." "Dynamic LLM
  orchestration remains appropriate for exploratory tasks requiring real-time restructuring."

## Cross-source corroboration (DAG vs emergent reliability)
- MAST (source 02): inter-agent misalignment (emergent-coordination failures) = 36.94%;
  specification/design = 41.77% — i.e. *both* under-specified flows and emergent chatter fail.
- Practitioner consensus (Augment Code; Kinde/Temporal-Dagster-LangGraph): "for workflows with
  known structure, dynamic orchestration adds cost, latency, and unpredictability"; a single
  strong agent can match multi-agent "within one context window." Use multi-agent when
  "boundaries of privileged information exist between agents."

## Reproducibility note
Quotes verbatim from the Microsoft post (fetched). The reliability direction (declared/
deterministic topology > LLM-routed for structured flows) is consistent across the vendor post
and the peer-reviewed MAST prevalence numbers, so the conclusion does not rest on the blog alone.
