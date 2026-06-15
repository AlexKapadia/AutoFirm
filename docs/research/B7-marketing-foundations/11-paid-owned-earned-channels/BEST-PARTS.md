# BEST-PARTS — Paid/Owned/Earned channels

## ADOPT
- **POE as AutoFirm's channel taxonomy** — every channel a plan touches is tagged Paid / Owned / Earned with its control/trust/speed profile. **Build implication:** a `Channel` contract { id, poe_type, control_level, trust_level, cost_model (CPC/CPM/organic), latency }; the channel-selection stage reasons over this typed inventory rather than ad-hoc lists.
- **Channel-role mapping to the funnel:** paid -> reach/acquisition, owned -> conversion/retention, earned -> trust/credibility. **Build implication:** the playbook assigns channels to STP-targeted segments and to brand-vs-activation pools (folder 10): brand-building leans paid-reach + earned; activation leans paid-performance + owned email/CRM.
- **IMC integration principle as a design rule** — plans must coordinate POE, not silo them. **Build implication:** a QA check flags plans that fund paid with no owned-conversion or earned-trust support (incoherent mix).

## REJECT
- **Reject POE as a measurement/credit model** — it classifies channels, it does NOT measure their causal contribution. Credit comes from attribution + MMM + experiments (folders 05-08). Keeping this boundary clean prevents the common conflation of "channel type" with "channel value."
- Reject the analyst "multiplier effect" as a hard number — treat it as a hypothesis to test per client via MMM/incrementality, not a baked-in constant (anti-overfit).

## Why
POE gives AutoFirm a stable, industry-general, trust/control-aware channel taxonomy that feeds both the STP/segment routing and the brand/activation budget split, while cleanly separating channel CLASSIFICATION from channel MEASUREMENT (kept in the attribution/MMM/experiment stack).
