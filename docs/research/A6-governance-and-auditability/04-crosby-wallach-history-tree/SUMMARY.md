# SUMMARY — Efficient Data Structures for Tamper-Evident Logging (Crosby & Wallach)

## Full citation
- **Title:** Efficient Data Structures for Tamper-Evident Logging
- **Authors:** Scott A. Crosby; Dan S. Wallach (Rice University).
- **Year:** 2009.
- **Venue:** Proceedings of the 18th USENIX Security Symposium (USENIX Security '09), Montreal, pp. 317–334.
- **URL:** https://www.usenix.org/conference/usenixsecurity09/technical-sessions/presentation/efficient-data-structures-tamper-evident (PDF: https://static.usenix.org/event/sec09/tech/full_papers/crosby.pdf)
- **Reference implementation:** Java `edu.rice.historytree` — https://github.com/scrosby/fastsig

## Question(s) informed
- **L1.A6.2** Immutable append-only audit logs & tamper-evidence (efficient proofs).

## GRADE tier
**High.** Peer-reviewed top-tier security venue (USENIX Security); the canonical reference for *efficient* tamper-evident logging with a public reference implementation. Independent of Haber-Stornetta (different authors/org) and of RFC 6962.

## Threat model
Considers an **untrusted logger** serving **clients** who store events in the log, kept honest by **auditors** who challenge the logger to prove correct behaviour. The logger may attempt to tamper with, reorder, or omit/truncate entries.

## Core contribution — the History Tree
A Merkle-tree-based data structure (a "history tree") over the append-only log that supports:
- **Membership (inclusion) proofs:** prove a given event is in the log at a given index.
- **Incremental / consistency proofs:** prove that a later commitment is a superset (append-only extension) of an earlier commitment — i.e. nothing previously committed was altered or removed.

Both proof types are **logarithmic — O(log n)** in size and verification cost, improving on the prior **linear O(n)** hash-chain approach (Schneier-Kelsey / Haber-Stornetta linking), where verifying the whole chain or producing a proof scaled with the number of entries.

## Commitments
The logger periodically publishes a **commitment Ci** (the tree's root hash at log size i). Clients/auditors that have seen Ci can later demand an incremental proof from Ci to Cj (j>i) to confirm the log only grew and never rewrote history; mutually-comparing commitments across auditors detects a logger that forks/equivocates.

## Performance
The paper reports the construction scales to high throughput (thousands of events/sec) with small (logarithmic) proofs, making continuous auditing practical at production logging rates.

## Reproducibility note
Structure and O(log n) claims are from the USENIX '09 paper and the Rice tamper-evident-logging project page (tamperevident.cs.rice.edu/Logging.html). The PDF did not extract via automated fetch (binary stream); claims corroborated against the official USENIX abstract, the Rice project page, and the UIUC CS563 course slides covering the paper.
