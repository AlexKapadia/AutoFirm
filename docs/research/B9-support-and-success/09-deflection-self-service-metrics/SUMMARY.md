# SUMMARY — Ticket deflection & self-service metrics (deflection rate, containment, FCR)

## Full citation (professional/industry references — no single peer-reviewed primary; multiple independent vendors corroborate the definitions)
- Zendesk, *Getting started with self-service — Part 6: Tracking essential self-service metrics*, https://support.zendesk.com/hc/en-us/articles/4408894139930
- Zendesk, *Ticket deflection: the currency of self-service*, https://www.zendesk.com/blog/ticket-deflection-currency-self-service/
- Decagon, *What is deflection rate?*, https://decagon.ai/glossary/deflection-rate
- Cobbai, *Measure Self-Service: Deflection, Search Success, and Knowledge Gaps*, https://cobbai.com/blog/self-service-metrics
- (Channel-switching evidence is independently corroborated by source 06, Dixon et al. 2013, N>97,000.)

## Ontology question informed
- **L1.B9.1** — the deflection / self-service measurement layer.

## What the sources claim (faithful)
- **Deflection rate (self-service score):** the percentage of support issues resolved via self-service without a human agent.
  `Deflection rate = (issues resolved via self-service / total issues submitted) × 100`.
  An alternative operational proxy: `help-centre users ÷ (help-centre users + ticket creators)`.
- **Containment rate** (stricter than deflection): the share of conversations an automated/AI agent handles **end-to-end without escalation**, including follow-ups — a "contained" conversation must be **fully resolved**, not merely redirected.
- **First Contact Resolution (FCR):** the share of issues resolved in a single interaction (no recontact). A core quality metric (corroborated by sources 05/06 as a primary loyalty driver).
- **Benchmarks (industry, treated as directional priors, NOT universal constants):** vendors report typical teams deflect ~**20–30%** of tickets, with top performers reportedly **80%+** — these are vendor-reported ranges, not peer-reviewed.
- **Knowledge-gap signals:** search-success rate and failed-search/no-result queries identify missing KB content that drives avoidable tickets.

## Source-quality grade (GRADE-adapted)
- **Tier: Low (definitions) / Very-low (benchmark numbers).** These are **vendor/practitioner** sources with commercial interest in selling deflection tooling.
- **The metric DEFINITIONS (deflection, containment, FCR) are corroborated across multiple independent vendors** → acceptable as Low-confidence definitional content.
- **The benchmark percentages (20–30%, 80%+) are Very-low** and must NEVER be a sole basis for a relied-upon claim (DEPTH-RUBRIC §1/§2) — used only as directional priors, never as targets baked into AutoFirm.

## Reproducibility note
The deflection and containment formulae are reproducible and consistent across the independent vendor references. The benchmark percentages are explicitly flagged Very-low and excluded from any deterministic AutoFirm constant; the *channel-switching* rationale for deflection is grounded in the larger-sample source 06.
