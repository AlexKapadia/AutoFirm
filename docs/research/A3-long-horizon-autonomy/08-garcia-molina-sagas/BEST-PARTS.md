# BEST-PARTS — Sagas (Garcia-Molina & Salem)

## ADOPT (the foundational pattern for AutoFirm's long-horizon execution)
1. **Adopt the saga model as AutoFirm's unit of long-horizon, resumable work.**
   - *Why:* a long-horizon company-build is exactly a long-lived transaction — a sequence of sub-steps that must either all complete or be cleanly compensated. The saga gives a 38-year-proven, peer-reviewed structure for this.
   - *Build implication:* model each multi-gate AutoFirm workflow as a saga S = T1..Tn where each Ti is a checkpointed, locally-atomic phase/subtask with a defined **compensating action Ci**. On failure at step j, run Cj..C1 to leave the workspace in an acceptable state (ties to CLAUDE.md §3.8 always-clean main / no graveyard — compensation removes half-done work instead of leaving it).

2. **Adopt "semantic compensation, not physical rollback" as the cleanup contract.**
   - *Why:* AutoFirm side-effects (git pushes, created files, external API calls) often cannot be byte-for-byte undone. Garcia-Molina & Salem explicitly define compensation as restoring "an acceptable approximation" of the prior state — which is the realistic target.
   - *Build implication:* every side-effecting agent action ships with a declared compensating action (e.g. revert-commit, delete-branch, cancel-order). Test: a property test asserting every registered forward action has a registered compensator (fail-closed if missing).

3. **Adopt interleaving:** sagas are designed to interleave with other transactions => AutoFirm's parallel fan-out (§4.3) of independent sub-sagas is theoretically grounded, provided each sub-transaction is locally atomic.

## REJECT / DEFER
- **Reject** assuming full ACID isolation between concurrent sagas — the model deliberately relaxes isolation. AutoFirm must enforce isolation in the data layer where required (multi-tenant, branch A8.2), not assume the saga gives it.
- **Defer** the original DB-locking mechanics; AutoFirm operates on files/git/APIs, so the *pattern* transfers but the *implementation* is re-derived (see source 10 for the LLM-specific realization).
