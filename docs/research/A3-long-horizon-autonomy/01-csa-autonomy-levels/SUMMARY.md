# SUMMARY — CSA "Leveling Up Autonomy in Agentic AI"

## Full citation
- **Title:** Leveling Up Autonomy in Agentic AI (position piece introducing CSA's autonomy levels)
- **Author/Org:** Jim Reavis (Co-founder & CEO), Cloud Security Alliance (CSA)
- **Year:** 2026 (published 2026-01-28)
- **Venue/Publisher:** Cloud Security Alliance (industry standards body) blog
- **URL:** https://cloudsecurityalliance.org/blog/2026/01/28/levels-of-autonomy

## Ontology questions informed
- **L1.A3.1** Levels-of-autonomy frameworks (primary).
- Supporting for **L1.A3.2** (where oversight must sit) and **L2.A7** (HITL gate design).

## GRADE tier
- **Low–Moderate.** A recognized-body (CSA) position piece, not peer-reviewed. Tiered **Low** as a sole basis, **up-rated to Moderate** for this claim because it is *corroborated by two independent autonomy taxonomies* in this branch (sources 02 Interface/Ada Lovelace and 03 Cihon et al.) that converge on the same 5–6 level continuum and the same in/on/out-of-the-loop oversight axis. Down-rate note: vendor/community framing, no empirical study.

## Key claims (with exact phrasing)
CSA defines **six autonomy levels (0–5)** for agentic AI:

| Level | Name | Defining characteristic (quoted) |
|---|---|---|
| 0 | No Autonomy (Human Execution) | "The AI cannot execute any actions in the world; it can only inform human decision-making." |
| 1 | Assisted (Human Decision + AI Execution) | "The AI proposes what it wants to do, a human reviews the proposal, and only upon approval does the AI proceed." |
| 2 | Supervised (Human Approval + Batch Execution) | Humans approve a plan/batch; "the AI then executes autonomously within that approved scope." |
| 3 | Conditional (AI Decision within Boundaries) | "The AI makes decisions and takes actions autonomously within defined boundaries, escalating to humans only when it encounters situations that exceed those boundaries." |
| 4 | High Autonomy (Minimal Supervision) | "The AI operates autonomously across a broad scope, with human involvement shifting from decision approval to monitoring and exception handling." |
| 5 | Full Autonomy (Self-Directed) | "Full autonomy, including the ability to set goals and potentially modify its own behavior. The AI operates with only strategic oversight from humans." |

**Oversight axis.** Oversight progresses from **in-the-loop** (Levels 0–2, human approval gates) -> **on-the-loop** (Level 3, boundary-based escalation) -> **out-of-the-loop** (Level 4, monitoring-based intervention).

**Level-5 caution (load-bearing quote):** "I don't believe Level 5 is appropriate for enterprise deployment today...the control mechanisms required to safely operate at this level don't exist yet."

## Reproducibility note
Re-fetch the URL; the six level names and the Level-5 caution quote are verbatim from the page. Convergence with sources 02 and 03 is the corroboration basis.
