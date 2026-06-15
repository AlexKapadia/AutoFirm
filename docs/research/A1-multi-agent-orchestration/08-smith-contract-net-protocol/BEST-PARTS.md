# BEST-PARTS — Smith 1980 (Contract Net Protocol)

## ADOPT (narrowly)
1. **CNP announce→bid→award as an OPTIONAL task-allocation mechanism** — where AutoFirm has multiple
   candidate agents/tools that *could* handle a subtask and suitability is uncertain, a lightweight
   bidding step lets the best-suited contractor self-select. *Build implication:* useful for the
   shared-resource dependency (source 06) when priority rules are insufficient — e.g. choosing among
   competing approaches in branch-per-experiment.
2. **Dynamic manager/contractor roles** — reinforces source 03's finding that roles should be
   assigned dynamically, here via negotiation rather than top-down design.

## REJECT as the primary topology
- **CNP / market-auction as AutoFirm's main coordination model** — REJECT: a decentralized bidding
  market (a) adds communication overhead (source 01 "high communication overheads"), (b) weakens the
  single accountable decision-owner AutoFirm requires for auditability (CLAUDE.md §2), and (c)
  introduces non-determinism into allocation that conflicts with the deterministic, fail-closed bar
  (§3.2/§5.6). AutoFirm's backbone stays **hierarchical orchestrator-worker** (sources 02, 03), with
  the orchestrator making allocation decisions directly.

## Why it is still in the library (coverage / DEPTH-RUBRIC §4)
- Market/auction is a named cell in the L1.A1.1 method space; including it with an explicit
  ADOPT-narrowly / REJECT-as-primary decision satisfies the "survey the FULL alternative space, then
  choose" requirement and documents *why* AutoFirm does not use a market as its core.

## Build implication (concrete)
- AutoFirm's default allocation is **orchestrator-directed** (hierarchical). CNP-style bidding is kept
  as an *optional, bounded sub-mechanism* for ambiguous allocation among interchangeable candidates,
  with the awarding decision still logged to the audit trail (A6) and owned by the orchestrator.
