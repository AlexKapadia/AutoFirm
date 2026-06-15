# BEST-PARTS — Eloundou et al. → AutoFirm

## ADOPT
- **The E0/E1/E2 exposure rubric as AutoFirm's CURRENT (LLM-era) automatability scorer — the layer
  that updates the 2003–2017 priors.** This is the most directly relevant source for an *LLM-agent*
  company-builder, because AutoFirm's automating engine literally IS "LLM + software on top of an
  LLM" — exactly the E1/E2 distinction. **Build implication:** `automatability/llm_exposure.py`
  scores each APQC Task as E0/E1/E2: E1 → a single agent call automates it; E2 → AutoFirm must
  *build tooling/MCP integration* around the LLM to automate it (this directly sizes AutoFirm's own
  build work per client); E0 → human/HITL.
- **The α/β/ζ triple as AutoFirm's automation-coverage REPORTING metric.** For any client, AutoFirm
  reports automatable-task share as a band: α (agent-only, conservative), β (= E1 + 0.5·E2, planning
  estimate), ζ (with full tooling, ambitious). This is the honest, citable way to quote automation
  coverage in the `evidence/` showcase — a band with a documented method, mirroring the
  9%–47% lesson from Arntz.
- **The most/least-exposed task profile** is AutoFirm's prioritization prior: writing, coding,
  data analysis, translation, math reasoning → automate first (high E1); science/critical-thinking,
  physical, manual → defer or delegate to humans/robots.
- **The "E2 = needs software built on the LLM" insight reframes AutoFirm's value proposition:** much
  business automation is *not* a raw model call but bespoke LLM-powered tooling. AutoFirm's
  differentiator is building the E2 layer (MCP tools, integrations, deterministic wrappers) that
  converts E2 tasks into automated ones — this is the through-line to A5/A8 (CLI substrate + integration).

## REJECT / use-with-care
- **Reject "exposure" as "should-automate" or "will-be-automated".** Exposure measures *technical
  time-saving potential*, explicitly not desirability, quality, safety, or compliance. AutoFirm
  must still gate every E1/E2 task through the business-case + compliance + bottleneck (social/
  creative) filters before auto-executing (fail-closed, CLAUDE §5.6).
- **Use-with-care: OpenAI-author conflict of interest + rapid capability drift.** Treat absolute
  numbers as a fast-moving estimate; AutoFirm should re-score against current agent capability
  rather than freeze the 2023 figures (the *rubric* is durable; the *scores* age fast).

## Concrete build implication
- Component: `automatability/llm_exposure.py` — scores each Task E0/E1/E2; E2 tasks emit a "tooling-to-build" backlog item (the per-client E2 build plan); reports α/β/ζ coverage band to `evidence/`.
- Test it drives: an efficacy test asserting (a) E1 tasks route to a single agent, (b) E2 tasks generate a concrete tooling backlog (not silent full-auto), (c) the reported coverage is the α/β/ζ band not a single number; plus a fail-closed test that a compliance-flagged E1 task is NOT auto-executed despite high exposure.
