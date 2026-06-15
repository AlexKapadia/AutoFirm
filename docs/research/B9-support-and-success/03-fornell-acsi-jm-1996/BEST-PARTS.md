# BEST-PARTS — Fornell et al. (1996) ACSI

## ADOPT
- **Multi-item, latent-construct CSAT over single-item CSAT** for AutoFirm's "rigorous satisfaction" reporting tier. Where statistical defensibility matters (e.g. investor-grade evidence per CLAUDE §3.10), measure satisfaction with ≥3 indicators (overall satisfaction, confirmation-of-expectations, performance-vs-ideal) and report on a **0–100 scale**.
  - **Build implication (L2.B9):** ship a `compute_csat_acsi(items)` deterministic function implementing `((sum_means − 3)/27)×100`, unit-tested at boundaries (all-1s → 0; all-10s → 100). Single-item transactional CSAT (% rating ≥4 on 1–5) remains available as the cheaper operational metric.
- **The driver→satisfaction→consequence causal chain** as the schema for AutoFirm's customer-experience data model: expectations/quality/value (inputs) → satisfaction → complaints/loyalty/retention (outputs). This typed contract lets the support playbook link operational levers to outcomes WITHOUT over-claiming (unlike raw NPS-growth claims).

## REJECT / DEFER
- **DEFER full PLS structural estimation** to the analysis/evidence layer only — runtime CSAT should stay deterministic and cheap. PLS is appropriate for the `evidence/` showcase (CLAUDE §3.10), not the hot path.
- **REJECT** conflating single-item CSAT with the ACSI index in reporting; label which is used.

## Why (cited)
- High-tier peer-reviewed foundation for satisfaction measurement; gives AutoFirm a defensible, general (cross-industry) CSAT method that is not tied to any one company (CLAUDE §3.9). Corroborates the satisfaction-loyalty link relied on in source 04.
