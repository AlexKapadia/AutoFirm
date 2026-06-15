# SUMMARY — RFC 6962: Certificate Transparency (append-only Merkle log)

## Full citation
- **Title:** Certificate Transparency
- **Authors:** Ben Laurie; Adam Langley; Emilia Kasper (Google).
- **Year:** June 2013.
- **Venue:** IETF, RFC 6962 (Experimental). (Obsoleted by RFC 9162 / CT v2.0, 2021.)
- **URL:** https://www.rfc-editor.org/rfc/rfc6962.txt

## Question(s) informed
- **L1.A6.2** Immutable append-only audit logs & tamper-evidence (production-deployed verifiable log).

## GRADE tier
**High.** Published IETF standard, globally deployed (every web CA). Provides the concrete, normative definition of an append-only Merkle log with inclusion + consistency proofs and signed heads — the practical realisation of sources 03/04 at internet scale. Independent authorship/org.

## Merkle Tree Hash (MTH) — exact recursive definition (quoted)
- Empty list: `MTH({}) = SHA-256()`
- Single entry: `MTH({d(0)}) = SHA-256(0x00 || d(0))`
- For n>1, with k = the largest power of two smaller than n:
  `MTH(D[n]) = SHA-256(0x01 || MTH(D[0:k]) || MTH(D[k:n]))`
(The `0x00` leaf prefix and `0x01` internal-node prefix prevent second-preimage/collision across node types.)

## Proof types
- **Merkle audit path (inclusion proof):** "the shortest list of additional nodes in the Merkle Tree required to compute the Merkle Tree Hash for that tree" — proves a specific entry is in the log. O(log n).
- **Merkle consistency proof:** demonstrates a current tree version is "a superset of any particular previous version" — proves the log is **append-only** (no historical rewrite). O(log n).

## Signed Tree Head (STH)
A signed commitment over: **tree_size** ("the number of entries in the new tree"), **timestamp** ("the current time"), **sha256_root_hash** ("the root of the Merkle Hash Tree"), and a **signature** over those fields. Clients gossip STHs; if a log shows different STHs to different parties (equivocation/fork), comparing roots + consistency proofs detects it.

## Reproducibility note
MTH definition and STH fields quoted verbatim from RFC 6962 §2.1 (Merkle Hash Trees) and §3.5 (STH). A reviewer can re-derive directly from the RFC text at the URL.
