# 02 — RFC 6962 hash-chained / append-only tamper-evident log

> Workstream B4. This source makes the W4 event log **tamper-evident**: the
> `CapabilityRegistryEvent` log is hash-chained so any reordering, insertion,
> deletion, or backdating of a growth event is cryptographically detectable.
> The repo already holds the full transcription of RFC 6962 under
> `A6-governance-and-auditability/06-rfc6962-certificate-transparency` — this
> folder is the **B4-specific application note** and cross-link, not a duplicate.

## Full citation

- **B. Laurie, A. Langley, E. Kasper, "Certificate Transparency"**, **RFC 6962**,
  IETF, **June 2013**. <https://www.rfc-editor.org/rfc/rfc6962>
- Foundational primary sources (already in repo):
  - **S. Haber, W. S. Stornetta, "How to Time-Stamp a Digital Document"**, *J.
    Cryptology*, **1991** — the hash-chain / linking scheme.
    (`A6-governance-and-auditability/03-haber-stornetta-timestamping`)
  - **S. A. Crosby, D. S. Wallach, "Efficient Data Structures for Tamper-Evident
    Logging"**, USENIX Security, **2009** — the history tree.
    (`A6-governance-and-auditability/04-crosby-wallach-history-tree`)

## Faithful structured summary (algorithms reproduced exactly)

**Merkle Tree Hash (MTH)** over an ordered list `D[n] = {d(0), …, d(n-1)}`,
reproduced from RFC 6962 §2.1 (`||` is concatenation, `0x00`/`0x01` are domain
separators preventing second-preimage / collision between leaves and internal nodes):

```
MTH({})        = SHA-256()                          # hash of empty string
MTH({d(0)})    = SHA-256(0x00 || d(0))              # leaf hash
MTH(D[n])      = SHA-256(0x01 || MTH(D[0:k]) || MTH(D[k:n]))
                 where k is the largest power of two < n
```

**Append-only / consistency proof (RFC 6962 §2.1.2).** A *consistency proof*
proves that an old tree head (root at size `m`) is a strict prefix of a new tree
head (root at size `n ≥ m`): the new log **only appended** `[m … n)` and **never
modified or removed** anything in `[0 … m)`. **Audit (inclusion) proofs** (§2.1.1)
prove a given entry is present at a given position. Together these give:
*append-only growth that is publicly, cheaply verifiable.*

**Hash-chain (linear) variant — what W4 actually needs.** For an event log we do
not need the full Merkle tree if a linear hash chain suffices for tamper-evidence:

```
entry_hash(e_0)  = H(domain || serialize(e_0))                 # genesis
entry_hash(e_i)  = H(domain || entry_hash(e_{i-1}) || serialize(e_i))   # i > 0
```

Each event commits to **all prior events** via the previous hash. Any mutation,
reorder, insertion, or deletion at position `j` invalidates `entry_hash` for every
`i ≥ j` — detectable by a single recompute pass. The **head hash** (`entry_hash` of
the last event) is a compact, publishable commitment to the entire growth history.
(This is the Haber–Stornetta linking scheme; the Merkle tree of RFC 6962 adds
*efficient* O(log n) proofs on top, which W4 can graduate to at thousands of events.)

**Key RFC 6962 design rules to preserve:**
- **Domain separation** between leaf and internal hashes (the `0x00` / `0x01`
  prefixes) — without it the structure is vulnerable to forged proofs.
- **Gapless, ordered entries** — the chain/tree is over a defined sequence; gaps or
  reordering break verification. (W4's existing `OrgAuditTrail` already enforces
  *gapless monotonic seq*; the hash chain layers tamper-evidence on top.)
- **The head is the only thing you must trust/publish** — verifiers reconstruct
  everything else from the log + the head.

## Best parts to take (mapped to the W4 design)

1. **Hash-chain every `CapabilityRegistryEvent`.** Add `prev_hash` + `entry_hash`
   to each event, computed exactly as the linear chain above with domain
   separation. *Maps to:* W4 "append-only RFC-6962 hash-chained CapabilityRegistryEvent".
2. **Gapless seq + hash chain together.** Reuse the existing `OrgAuditTrail`
   invariant (`event.seq == len(events)`, fail-closed on non-consecutive seq) and
   bind it to the hash chain so *both* a missing seq *and* a content tamper are
   detected. *Maps to:* "gapless seq; current set = pure replay".
3. **Publishable head hash = the registry commitment.** Expose the head hash in the
   evidence/showcase and in audit exports; a single value attests the entire
   capability-growth history. *Maps to:* W4 evidence/showcase + auditability.
4. **Consistency-proof verifier as a fail-closed gate.** On every load/replay,
   verify the chain end-to-end; **refuse to serve the live registry if the chain
   does not verify** (fail closed — never replay a tampered log). *Maps to:*
   CLAUDE.md §5.6 fail-closed + W4 security controls.
5. **Graduate to a Merkle history tree at scale.** When the log reaches thousands
   of events, the RFC 6962 tree gives O(log n) inclusion/consistency proofs so a
   viewer can verify one capability's provenance without rehashing the whole log.
   *Maps to:* W4 "thousands of capabilities, no ceiling".

## Cross-links

- **01 (Event Sourcing)** — provides the append-only stream this chain protects.
- Repo: `A6-governance-and-auditability/{03-haber-stornetta,04-crosby-wallach,05-ma-tsudik,06-rfc6962}`.
