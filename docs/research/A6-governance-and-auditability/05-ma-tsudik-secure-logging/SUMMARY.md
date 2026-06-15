# SUMMARY — A New Approach to Secure Logging (Ma & Tsudik)

## Full citation
- **Title:** A New Approach to Secure Logging
- **Authors:** Di Ma; Gene Tsudik (University of California, Irvine).
- **Year:** 2008 (conference); extended version ACM TOS 2009.
- **Venue:** Proc. IFIP WG 11.3 Working Conference on Data and Applications Security (DBSec 2008), LNCS. Journal version: ACM Transactions on Storage, 5(1), 2009.
- **URL:** https://dl.ifip.org/db/conf/dbsec/dbsec2008/MaT08.pdf (eprint: https://eprint.iacr.org/2008/185)

## Question(s) informed
- **L1.A6.2** Immutable append-only audit logs & tamper-evidence — specifically the **attack taxonomy** and a truncation-resistant construction.

## GRADE tier
**High.** Peer-reviewed (IFIP DBSec + ACM TOS); authoritative on the *failure modes* of prior secure-logging schemes (Schneier-Kelsey, Bellare-Yee) and the FssAgg defence. Independent of sources 03/04/06.

## Threat model & attacks (quoted/defined)
The adversary may compromise the logging machine and try to alter the log undetectably. Two named attacks that hash-chain/MAC schemes fail to stop:
- **Truncation attack:** the adversary deletes "a contiguous tail of log entries" — removing the most recent records while preserving earlier history. Plain forward hash-chains cannot detect this without external knowledge of the expected endpoint.
- **Delayed detection attack:** tampering remains undetected until substantially after it occurs (private-key/MAC schemes such as Schneier-Kelsey suffer this).

## Why prior schemes fail
Hash-chain and MAC-based schemes (Schneier-Kelsey, Bellare-Yee) bind each entry to the previous, so deleting the *final* entries simply yields a shorter valid-looking chain — truncation is silent.

## Solution — FssAgg
**Forward-secure Sequential Aggregate (FssAgg)** authentication: signatures/MACs are *aggregated* so that a single aggregate authenticator covers the entire sequence; the forward-secure key evolution means a compromise of current key material cannot retroactively forge or validate falsified historical entries, and the all-or-nothing aggregate makes silent tail-truncation detectable.

## Reproducibility note
Attack definitions quoted/derived from the DBSec 2008 paper and the IACR eprint 2008/185; the truncation/delayed-detection taxonomy is the paper's central motivation (§Introduction/§Attack model).
