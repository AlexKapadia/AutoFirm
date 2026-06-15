# BEST-PARTS — AgentPoison

## ADOPT
- **The concrete poisoning threat as a binding red-team requirement.** Build implication: AutoFirm's
  memory layer MUST have an adversarial test that injects an optimized-trigger poisoned memory and
  asserts the retriever does NOT surface it to the wrong principal / does not let it hijack control
  flow. The >80% ASR at <0.1% poison rate proves this is not hypothetical — a single poisoned record
  is enough, so a single un-authorized write is a critical defect.
- **Quantified attack budget as test parameters.** Build implication: the evidence suite includes a
  poisoning-robustness chart: ASR vs poison rate, demonstrating AutoFirm's WA + PV + PS controls
  (folder 12) drive ASR toward zero where the undefended baseline exceeds 80%.
- **Validates Write-Authorization + Principal-Scoped Retrieval as the right defenses** — the attack
  works precisely because writes are unauthenticated and retrieval is not principal-scoped.

## REJECT / DEFER
- **Reject any memory design that ingests external/observed content as memory without sanitization +
  WA.** AgentPoison's environmental-observation vector means untrusted document/tool output must be
  treated as untrusted input (CLAUDE.md s5.6) before it can ever become a memory write.

## Build implication (concrete)
Supplies the **poisoning-robustness adversarial test + ASR-vs-poison-rate evidence chart** for L2.A4,
and is the primary evidence that **unauthenticated writes / unscoped retrieval = critical
vulnerability** — hardening the WA/PS primitives from folder 12.
