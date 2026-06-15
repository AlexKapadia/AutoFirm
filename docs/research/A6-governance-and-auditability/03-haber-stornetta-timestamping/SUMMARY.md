# SUMMARY — How to Time-Stamp a Digital Document (Haber & Stornetta)

## Full citation
- **Title:** How to Time-Stamp a Digital Document
- **Authors:** Stuart Haber; W. Scott Stornetta (Bellcore).
- **Year:** 1991.
- **Venue:** Journal of Cryptology, vol. 3, no. 2, pp. 99–111.
- **DOI:** 10.1007/BF00196791
- **URL:** https://link.springer.com/article/10.1007/BF00196791 (PDF: https://link.springer.com/content/pdf/10.1007/BF00196791.pdf)

## Question(s) informed
- **L1.A6.2** Immutable append-only audit logs & tamper-evidence (the founding hash-linking result).

## GRADE tier
**High.** Peer-reviewed Journal of Cryptology paper; the foundational, heavily-cited primary result for cryptographic linking/hash-chaining (the conceptual ancestor of blockchain and of tamper-evident logs). Won the 1992 Discover Award for Computer Software.

## Problem
Certify *when* a digital document was created or last modified, "so that it is infeasible for a user to back-date or forward-date a document, even with the collusion of a time-stamping service [TSS]."

## Scheme 1 — Linking scheme (the core idea)
Each time-stamp request is cryptographically **linked** to the requests that immediately precede and follow it: the certificate for a document embeds a hash derived from the previous certificate, forming a chain. As paraphrased from the linking construction: "the new interval hash is computed by taking the root hash of the [batch] and hashing it with the previous interval hash" — i.e. each interval's commitment chains forward from the prior one.

Security argument (quoted):
- Back-dating: "The TSS cannot feasibly back-date a document by preparing a fake time-stamp for an earlier time, because bits from the document in question must be embedded in certificates immediately following that earlier time, yet these certificates have already been issued."
- Forward-dating: "The TSS cannot forward-date a document, because the certificate must contain bits from requests that immediately preceded the desired time, yet the TSS has not received them."
Both arguments assume a **collision-resistant one-way hash function**.

## Scheme 2 — Distributed-trust / random-witness scheme
The paper's second construction removes reliance on a single trusted TSS by using the document hash to pseudorandomly select a set of other clients as **witnesses** who co-sign the timestamp, distributing trust so no single party can forge a timestamp.

## Reproducibility note
The back/forward-dating quotes are the standard formulation of §3–4 of the paper; a reviewer can re-derive from the Journal of Cryptology PDF (DOI 10.1007/BF00196791). Note: full-text behind Springer auth; abstract and scheme descriptions corroborated across multiple independent secondary expositions.
