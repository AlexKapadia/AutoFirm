# SUMMARY — Cihon et al. "Measuring AI agent autonomy: Towards a scalable approach with code inspection"

## Full citation
- **Title:** Measuring AI agent autonomy: Towards a scalable approach with code inspection
- **Authors:** Peter Cihon, Merlin Stein, Gagan Bansal, Sam Manning, Kevin Xu
- **Year:** 2025 (submitted 2025-02-21)
- **Venue:** NeurIPS Socially Responsible Language Modelling Research (SoLaR) Workshop 2024; arXiv:2502.15212
- **URL/DOI:** https://arxiv.org/abs/2502.15212

## Ontology questions informed
- **L1.A3.1** Levels-of-autonomy frameworks (primary; *measurement* method, not just a ladder).
- Supporting for **L1.A5.1/A5.3** (CLI orchestration code as the artifact to inspect) and **L2.A7**.

## GRADE tier
- **Moderate.** arXiv + NeurIPS workshop (lightly reviewed). Methods + worked example (AutoGen) present. Tiered Moderate per DEPTH-RUBRIC §2 (preprint/workshop). Up-rated by independence from sources 01/02 (a *measurement* approach, not a normative ladder) yet converging on the same two-axis structure (impact + oversight).

## Key claims (with exact phrasing)
- **Method:** assess autonomy by inspecting **"the orchestration code used to run an AI agent"** — a *static*, pre-runtime evaluation that "avoids the need to execute agents during evaluation," sidestepping "costs and risks associated with run-time evaluations."
- **Two scoring dimensions of the taxonomy:**
  1. **Impact** — the scope of effects an agent can produce.
  2. **Oversight** — mechanisms for human control and monitoring.
- **Demonstration:** applied to the **AutoGen** multi-agent framework.
- Framing quote: "AI agents are AI systems that can achieve complex goals autonomously."

## Reproducibility note
Re-fetch arXiv:2502.15212 abstract for the two-dimension (impact, oversight) framing and the AutoGen demonstration. The "inspect orchestration code, don't run the agent" thesis is the load-bearing, AutoFirm-relevant claim.
