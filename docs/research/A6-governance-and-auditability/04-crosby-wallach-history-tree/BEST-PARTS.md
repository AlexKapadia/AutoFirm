# BEST-PARTS — History Tree for AutoFirm

## ADOPT
1. **Adopt the history tree as the audit-log data structure, upgrading the plain hash chain.** It gives O(log n) **inclusion proofs** (this audit event happened) and O(log n) **consistency proofs** (the log is an append-only superset of what an auditor saw earlier). For a long-horizon autonomous run producing thousands of events, O(log n) (vs O(n)) is the difference between continuous auditability and an intractable verification cost. *Build implication:* L2.A6 audit store = append-only events + a history-tree index; the audit-agent (cf. source 09) verifies via incremental proofs, not full re-hashing.
2. **Adopt periodic published commitments Ci.** AutoFirm publishes the tree root at intervals (and at every gate, per CLAUDE.md §3.13). A later incremental proof Ci→Cj proves no historical record was rewritten — the cryptographic backbone of the "revertable, tamper-evident history" requirement.
3. **Adopt the untrusted-logger / auditor split as the trust model.** Treat the AutoFirm host running the agents as a *potentially-compromised logger*; a separate, least-privilege **audit agent** (source 09, CLAUDE.md §2 North Star) challenges it. This is fail-closed: governance does not assume the executor is honest.
4. **Reuse `edu.rice.historytree` as a reference** for the implementation contract / test oracle (do not necessarily depend on the Java lib; mirror its proof semantics).

## REJECT / DEFER
- **Reject building a bespoke crypto-accumulator beyond the history tree.** The history tree is sufficient and proven; more exotic structures add risk without an evidenced benefit for AutoFirm's scale.
- **Defer multi-party gossip/equivocation detection to source 06** (CT) where it is specified end-to-end.

## Why (cited)
This is the peer-reviewed primary source that makes tamper-evident logging *efficient enough to run continuously* at agent-system throughput — turning CLAUDE.md §5.6's append-only-audit requirement from aspiration into a measurable, proof-bearing control. Second of the ≥3 independent tamper-evidence primaries (with 03 and 06).
