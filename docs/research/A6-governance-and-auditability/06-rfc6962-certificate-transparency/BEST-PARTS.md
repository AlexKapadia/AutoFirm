# BEST-PARTS — Certificate Transparency model for AutoFirm

## ADOPT
1. **Adopt the CT-style append-only Merkle log with Signed Tree Heads as AutoFirm's audit-log reference design.** It is the production-proven, IETF-standardised instantiation of the history-tree idea (source 04): leaves = audit events, STH = the periodic signed commitment, consistency proofs = append-only guarantee. *Build implication:* L2.A6 audit store emits an STH at every gate; the audit/North-Star agent (CLAUDE.md §2) verifies consistency STH→STH.
2. **Adopt the leaf/node domain-separation prefixes (`0x00` / `0x01`).** This is a concrete, must-not-skip correctness detail: prefixing leaf vs internal hashes prevents an attacker from passing an internal node off as a leaf. AutoFirm's MTH implementation MUST use distinct prefixes (a CLAUDE.md §3.11 zero-numerical-error / §5.6 fail-closed detail; a prime mutation-testing target per §3.6).
3. **Adopt STH gossip / external publication for equivocation detection.** Publishing the STH to an independent location (a second store, a public note) means a compromised AutoFirm host that tries to show two different histories is caught by mismatched roots — realising Haber-Stornetta's distributed-trust insight (source 03) cheaply.
4. **Adopt the exact SHA-256 MTH recurrence as the test oracle.** Property/known-answer tests assert AutoFirm's tree matches RFC 6962's recurrence for the empty, single, and n>1 cases — turning the spec into tests-with-teeth.

## REJECT / DEFER
- **Reject the full X.509/SCT certificate machinery.** AutoFirm logs agent actions, not TLS certs; take the log structure, drop the PKI-specific payloads.
- **Defer to RFC 9162 (CT v2.0)** for any production hardening (it obsoletes 6962); 6962 is the clearest pedagogical spec and the deployed baseline.

## Why (cited)
CT proves an append-only, externally-verifiable audit log works at internet scale with O(log n) proofs — the strongest evidence that AutoFirm's tamper-evident-log requirement (CLAUDE.md §5.6) is achievable, not aspirational. Third independent primary for the tamper-evidence claim (with 03, 04).
