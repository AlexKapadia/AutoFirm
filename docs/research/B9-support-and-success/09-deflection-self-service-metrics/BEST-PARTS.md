# BEST-PARTS — Deflection & self-service metrics

## ADOPT
- **Deflection rate AND the stricter containment rate as two distinct, deterministic AutoFirm metrics:**
  - `deflection_rate = self_service_resolved / total_issues`
  - `containment_rate = fully_auto_resolved_without_escalation / total_auto_conversations`
  - **Build implication (L2.B9):** because AutoFirm's support agents ARE the AI layer, **containment rate is the headline efficiency metric** (it measures end-to-end autonomous resolution). Track alongside CES so deflection is never gamed at the cost of effort/quality. Deterministic counters, unit-tested (a conversation escalated to HITL must NOT count as contained).
- **FCR as the primary quality gate on deflection** — a deflected/contained issue only "counts" if it does not recontact within a window (e.g. 7 days). Prevents the failure mode of "deflect now, recontact later."
- **Knowledge-gap mining** (failed-search/no-result queries) as the engine that auto-improves the KB → closes the loop that raises future deflection. Feeds AutoFirm's memory/learning loop.

## REJECT
- **REJECT the vendor benchmark percentages (20–30%, "80%+") as targets or constants.** Very-low tier, commercially biased; using them would overfit to vendor marketing (CLAUDE §3.9, DEPTH-RUBRIC §6). AutoFirm sets deflection/containment **targets per client from that client's own baseline**, not from a borrowed number.
- **REJECT deflection-rate maximisation in isolation** — must be jointly optimised with CES + FCR + recontact rate, else it degrades into harmful "wall-off the humans" behaviour (the exact effort-increasing anti-pattern source 06 warns against).

## Why (cited)
- Definitions are multi-vendor corroborated and industry-general; containment maps directly onto AutoFirm's autonomous-agent reality. The hard guardrail (joint optimisation with CES/FCR; no borrowed benchmark constants) is grounded in the peer-reviewed/large-sample effort evidence (sources 04, 06).
