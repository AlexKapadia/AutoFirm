# BEST-PARTS — AIDA / funnel origin

## ADOPT
- **Adopt the funnel as AutoFirm's default pipeline SCHEMA (a shared vocabulary), not as a law.**
  AIDA's Attention→Interest→Desire→Action (and CRM's lead→MQL→SQL→opportunity→close descendants)
  give a stable, century-proven stage taxonomy that every CRM, every sales rep, and every metric
  already speaks. AutoFirm's `sales` playbook should expose a configurable **pipeline-stage
  contract** seeded with these canonical stages so its output integrates with real CRMs.
  *Build implication:* a typed `PipelineStage` enum + per-stage entry/exit criteria in the L2.B8
  sales playbook; default = AIDA-derived stages, overridable per company/industry.
- **Adopt the historical-honesty stance as a design value.** Because even AIDA's *origin* was
  mis-cited for a century, AutoFirm must treat funnel stages as **conventions that need
  per-deal evidence**, never as guaranteed buyer states. This directly motivates pairing the funnel
  with the empirically-grounded, non-linear models (sources 06 Gartner, 07 McKinsey).

## REJECT
- **Reject treating the funnel as a literal, strictly-sequential model of how buyers decide.**
  Iwamoto shows it is a century-old convention; source 02 (Vakratsas & Ambler) shows the strict
  temporal hierarchy lacks empirical support. AutoFirm must NOT hard-code an assumption that buyers
  pass through stages once, in order. Pipelines model *the seller's tracking*, not *the buyer's
  brain*.

## Why this matters for generality
A stage taxonomy is industry-neutral: it parameterizes cleanly (a DTC e-commerce funnel and an
enterprise-SaaS pipeline are the *same schema* with different stage counts/criteria), satisfying
the B12 "any company" bar without overfitting to one motion.
