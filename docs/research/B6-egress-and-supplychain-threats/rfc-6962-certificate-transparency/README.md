# RFC 6962 — Certificate Transparency (Merkle tree, leaf-hash domain separation, STH, audit/consistency proofs)

> Research note for AutoFirm component **C9 — Cost-Data Integrity & Tamper-Evident Cost Logging**.
> This source grounds the *append-only, hash-chained, verifiable* substrate that the cost ledger is written into.

---

## 1. Full citation

- **Title:** *Certificate Transparency* (RFC 6962)
- **Authors:** B. Laurie, A. Langley, E. Kasper (Google)
- **Publisher / Year:** Internet Engineering Task Force (IETF), Experimental, **June 2013**
- **URL:** https://www.rfc-editor.org/rfc/rfc6962.html (datatracker mirror: https://datatracker.ietf.org/doc/html/rfc6962)
- **Successor (informative):** *Certificate Transparency Version 2.0*, draft-ietf-trans-rfc6962-bis — https://datatracker.ietf.org/doc/html/draft-ietf-trans-rfc6962-bis-35

---

## 2. Faithful structured summary

RFC 6962 defines an **append-only, publicly auditable log** built on a Merkle hash tree. Its purpose is to make it impossible for a log operator to **silently insert, remove, or alter** entries after the fact, or to **show different views to different observers**, without detection. These are exactly the properties AutoFirm's cost ledger needs: an entry, once committed, is permanent and provable; the log cannot be rewound or forked.

### 2.1 Merkle Hash Tree with leaf/node domain separation (Section 2.1)

The hash algorithm is **SHA-256** (FIPS 180-4), 32-byte output. The Merkle Tree Hash (`MTH`) of an ordered list of `n` inputs `D[n] = {d(0), d(1), ..., d(n-1)}` is defined recursively. **Exact definitions (verbatim):**

```
The hash of an empty list is the hash of an empty string:
        MTH({}) = SHA-256().

The hash of a list with one entry (also known as a leaf hash) is:
        MTH({d(0)}) = SHA-256(0x00 || d(0)).

For n > 1, let k be the largest power of two smaller than n
(i.e., k < n <= 2k).  The Merkle Tree Hash of an n-element list
D[n] is then defined recursively as

        MTH(D[n]) = SHA-256(0x01 || MTH(D[0:k]) || MTH(D[k:n])),

where || is concatenation and D[k1:k2] denotes the list
{d(k1), d(k1+1),..., d(k2-1)} of length (k2 - k1).
```

> **Domain separation (load-bearing).** The RFC states: *"Note that the hash calculations for leaves and nodes differ. This domain separation is required to give second preimage resistance."* The single prefix byte — **`0x00` for a leaf, `0x01` for an interior node** — is what stops an attacker from re-interpreting an interior node's hash as a leaf (or vice-versa) to forge a different tree with the same root. Without it, the tree's collision resistance breaks.

### 2.2 Merkle audit / inclusion paths (Section 2.1.1)

A **Merkle audit path** for leaf `m` is *"the shortest list of additional nodes in the Merkle Tree required to compute the Merkle Tree Hash for that tree."* It proves a specific entry is included in the tree committed to by a given root. **Exact recursion (verbatim):**

```
For a tree with a single leaf:
        PATH(0, {d(0)}) = {}

For n > 1, let k be the largest power of two smaller than n:
        PATH(m, D[n]) = PATH(m, D[0:k]) : MTH(D[k:n])  for m < k; and
        PATH(m, D[n]) = PATH(m - k, D[k:n]) : MTH(D[0:k]) for m >= k
```

Audit-path size is **O(log n)**; a verifier recomputes the root from the leaf and the path and compares against the signed root.

### 2.3 Merkle consistency proofs — the append-only property (Section 2.1.2)

A **consistency proof** proves that one tree (size `m`) is a **prefix** of a later tree (size `n`, `m < n`) — i.e. the log was only **appended to**, never rewritten or truncated. **Exact definition (verbatim):**

```
        PROOF(m, D[n]) = SUBPROOF(m, D[n], true)
```

with the recursive `SUBPROOF` establishing that all `m` earlier entries are unchanged in the larger tree. Proof size is bounded by **`ceil(log2(n)) + 1`** nodes. This is the cryptographic mechanism behind "you cannot quietly delete or edit history."

### 2.4 Signed Tree Head — STH (Section 3.5)

The log periodically signs its current root. The `TreeHeadSignature` covers:

- **version** (v1)
- **signature_type** = `tree_hash`
- **timestamp** (must be at least as recent as the most recent SCT)
- **tree_size** (number of entries)
- **sha256_root_hash** (32-byte Merkle root)

> *"Each log MUST produce on demand a Signed Tree Head that is no older than the Maximum Merge Delay."*

The STH is the **portable, signed commitment** to the entire log state at a point in time. Auditors compare STHs (and verify consistency proofs between them) to detect equivocation or rollback.

---

## 3. Best parts to take → mapped to the AutoFirm C9 control

| RFC 6962 mechanism | AutoFirm C9 control it grounds |
| --- | --- |
| **Leaf/node domain separation `0x00`/`0x01`** | Every cost-ledger entry is hashed as a leaf with the `0x00` prefix; internal aggregation nodes use `0x01`. AutoFirm's audit log already cites RFC-6962 — C9 inherits the **same domain separation** so a forged cost entry cannot masquerade as an aggregation node (second-preimage resistance on the *money* path). |
| **`MTH` Merkle root + Signed Tree Head** | The cost ledger emits a **signed cost-tree head** (tree_size = number of cost events, root = `MTH` over all attested cost records). Reconciliation and budget-cap checks read the **signed root**, never a self-reported running total. |
| **Inclusion proof `PATH(m, D[n])`, O(log n)** | Any single charge ("agent X spent $Y at time T against price-snapshot V") can be proven present in the ledger with a logarithmic proof — supports cheap, regulator-grade *"show me this exact spend is in the record of cost"*. |
| **Consistency proof `PROOF(m, D[n])`, append-only** | This is the **anti-truncation / anti-edit** guarantee for cost. A rogue agent cannot **hide spend** by rewriting or rolling back the ledger: any inconsistency between an earlier STH and a later one is mathematically detectable. Directly defeats the *silent under-reporting to slip past caps* attack at the storage layer. |
| **STH gossip / comparison between observers** | C9's reconciliation engine and the North-Star overseer each hold independently-fetched STHs; divergence ⇒ stop-and-fail-closed. |

**Key C9 framing this source supports:** cost is written into an RFC-6962-style verifiable log so that *what is in the record of cost is provable and unrewindable*. RFC 6962 secures **the container**; it does **not** by itself decide *what number goes in* — that is the job of the deterministic `attested_usage × versioned_price` computation plus provider reconciliation (see sibling notes). The container's append-only/consistency guarantee is what makes "hide spend by editing history" infeasible.
