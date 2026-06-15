# BEST-PARTS — RULER

## ADOPT
- **Treat advertised context length as untrustworthy; budget to *effective* length.** Build
  implication: AutoFirm's retrieval pipeline caps assembled-context size well below the model's
  nominal window and proves the cap with an internal RULER-style probe, rather than assuming a 200K
  window is 200K usable. This hardens the L1.A4.2 "retrieve+compress, keep it short" recommendation.
- **Don't certify long-context behavior with single-needle NIAH.** RULER shows NIAH passes while
  multi-hop/aggregation fails. Build implication: AutoFirm's memory eval harness (feeds A9) includes
  multi-hop and multi-needle retrieval tasks, not just single-fact recall — a tougher acceptance bar.
- **Second independent justification for external RAG over context-stuffing.** Reinforces the
  parametric+external split (folder 05): durable knowledge belongs in a retrievable index, surfaced a
  few high-value items at a time, never dumped into a long prompt.

## REJECT / DEFER
- **Reject "the model has a big context window, so just paste everything"** — empirically false past
  the effective length (this paper + Lost-in-the-Middle 08).

## Build implication (concrete)
Closes the A4.2 single-source risk on the context-limit axiom: it now has **two independent primaries
(08 + 17)**. Drives a concrete evidence chart (SYNTHESIS showcase #1): accuracy vs. context length
with the effective-length knee marked, proving short-retrieval beats context-stuffing.
