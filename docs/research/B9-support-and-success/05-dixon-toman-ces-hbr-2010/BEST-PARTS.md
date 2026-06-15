# BEST-PARTS — Dixon, Freeman & Toman (2010) CES

## ADOPT
- **CES as AutoFirm's primary TRANSACTIONAL (post-interaction) support metric**, distinct from relational NPS and satisfaction CSAT. Question pattern: "How much effort did you personally have to put forth to handle your request?" (e.g. 1–7 Likert; report mean or % low-effort).
  - **Build implication (L2.B9):** the support playbook attaches CES to every resolved ticket; deterministic `compute_ces(responses)` (mean, and %≤threshold). Map CES into the customer-health model (source 10) as a leading churn signal.
- **The five tactics as concrete playbook rules** AutoFirm's autonomous support agents enforce:
  - **Next-issue avoidance** → after resolving, proactively address likely downstream issues (reduces repeat contacts).
  - **Channel-stickiness** → do NOT bounce a customer across channels; resolve in-channel where possible.
  - **Resolution over speed** → optimise FCR, not just AHT (anti-pattern: closing fast but unresolved).
- **"Meet expectations reliably, don't chase delight"** → sets the SLA-design philosophy: predictable, consistently-met SLAs beat heroics. Converges with source 04.

## REJECT
- **REJECT optimising Average Handle Time (AHT) as a primary quality target** — the source explicitly warns speed-focus harms resolution. AHT is a cost/capacity metric (feeds Erlang staffing, source 08), NOT a quality metric.
- **REJECT delight-maximisation** as the support strategy.

## Why (cited)
- Large-sample practitioner evidence whose *direction* is corroborated by peer-reviewed disconfirmation theory (source 04) — meets the ≥2-source bar for the "effort > delight" design choice. Industry-general (any support function), satisfying CLAUDE §3.9.
