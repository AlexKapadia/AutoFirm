# BEST-PARTS — Graicunas (1933)

## What AutoFirm ADOPTS

1. **The Graicunas curve is the hard math behind AutoFirm's SPAN CAP — the single most important
   org-scaling rule for the orchestrator.** Because relationships grow near-geometrically in span,
   an orchestrator that directly manages too many subagents suffers a coordination explosion (the
   "context flooding" of CLAUDE.md §3.1 / A1.4). The fix is to **cap the orchestrator's direct span
   and introduce middle-line sub-orchestrators** (Mintzberg's middle line, source 04) when span
   exceeds the cap — i.e. go hierarchical instead of flat-and-overloaded.
   - **Build implication (deterministic, testable):** L2.ORG enforces a configurable
     `max_direct_reports` (a span cap). When pending child agents would exceed it, the engine
     spawns a sub-orchestrator layer rather than fanning out flat. The cap and the resulting
     hierarchy depth are logged to the audit trail.

2. **Use the formula as an explicit coordination-cost estimator.** `C(n) = n(2^(n-1) + n - 1)` is a
   deterministic, exact function AutoFirm can compute to *predict* coordination load before fanning
   out — feeding the "is this fan-out worth it?" decision (fan-out is the orchestrator's explicit
   choice, CLAUDE.md §4.3).

3. **Span is contingent, not a magic constant (consistency with §3.9).** Adopt the *shape* of the
   curve, NOT the literal "5-6" number. The right cap depends on coordination mode: with
   *standardized outputs* (Mintzberg) cross-relationships shrink, so the effective cap is higher;
   with *mutual adjustment* it must be lower. The cap is parameterized by coordination mechanism.

## What AutoFirm REJECTS / caution
- **Reject the literal 5-6 prescription as universal.** Graicunas's number is a 1933 judgement and
  is superseded by modern empirics (source 07) and by the fact that standardized-output coordination
  cuts the cross-relationship term. AutoFirm sets the cap from the coordination mode + evidence.
- **Reject Graicunas's hidden assumption** that all cross-relationships are active. For agents
  coordinating only via typed output contracts (no agent<->agent chatter), the `n(n-1)` cross term
  is largely *suppressed* — a key insight that lets AutoFirm safely run a higher span than human
  orgs. (This is exactly why "standardize outputs" scales, source 04.)

## Quantification for evidence/
- A **span-cap ablation chart:** measured coordination overhead / failure rate vs. orchestrator
  direct-report count, with and without standardized output contracts — empirically locating
  AutoFirm's optimal cap and demonstrating the contract suppresses the cross term.
- The exact `C(n)` curve plotted as the theoretical upper bound (PNG + HTML for evidence/).
