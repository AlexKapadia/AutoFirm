# BEST-PARTS — Haber & Stornetta linking for AutoFirm

## ADOPT
1. **Adopt forward hash-linking as the baseline tamper-evidence primitive for the audit log.** Each AutoFirm audit record stores `H(record_i || hash_{i-1})`, so any insertion, deletion, or edit of a historical record breaks the chain and is detectable. This is the minimal, dependency-free mechanism realising CLAUDE.md §5.6 "immutable, append-only audit log." (Crosby-Wallach, source 04, then upgrades the *proof efficiency* to O(log n).)
2. **Adopt the explicit back-dating AND forward-dating threat framing** as named threats in the A6 threat model: an autonomous agent (or a compromised one) must not be able to fabricate a record at a fabricated time. Linking defends both directions.
3. **Adopt periodic external anchoring (the distributed-trust insight).** Publish the chain head (a single hash) to an independent witness on a schedule, so even a fully-compromised AutoFirm host cannot rewrite already-anchored history. This is the cheap version of Scheme 2 and pairs with source 06 (CT/gossip).

## REJECT / DEFER
- **Reject the literal random-witness multi-client protocol as the primary mechanism.** AutoFirm is not a public TSS with a client population; the witness set would be synthetic. **Adopt the principle (external anchoring), reject the literal protocol** — defer to a single trusted external anchor (e.g. a transparency log, source 06).
- **Reject relying on plain linking alone for truncation defence** — it does not stop tail-truncation (see source 05, Ma-Tsudik). Linking is necessary, not sufficient.

## Why (cited)
This is the primary, peer-reviewed origin of hash-chaining; basing the audit log on it gives a citable, institution-grade foundation rather than ad-hoc logging (CLAUDE.md §3.2/§3.3). It is the first of ≥3 independent primary sources backing the tamper-evidence claim (with sources 04 and 06).
