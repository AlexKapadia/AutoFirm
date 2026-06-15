# SUMMARY — Graicunas (1933): Span of Control & the Relationships Formula

## Full citation
- **Title:** "Relationship in Organization"
- **Author:** V. A. Graicunas
- **Year:** 1933 (March)
- **Venue:** *Bulletin of the International Management Institute* (Geneva).
- **Reprint of record:** Gulick, L. & Urwick, L.F. (eds.) (1937). *Papers on the Science of
  Administration*, Institute of Public Administration, Columbia University — Graicunas's paper is
  reprinted as a chapter.
- **DOI:** n/a (1933 article / 1937 reprint)
- **Verification sources consulted:** https://www.nickols.us/graicunas.htm ;
  https://kalyan-city.blogspot.com/2011/08/graicunas-theory-of-span-of-control.html ;
  Wikipedia "Span of control" (corroborating the three relationship types and historical context).

## Ontology questions informed
- **L1.B1.3** (span-of-control & hierarchy scaling — the SAFETY/CORRECTNESS-CRITICAL formula).
- Feeds **L2.ORG** (span caps for the dynamic agent org) and A1.4 (coordination-cost theory).

## GRADE tier
**High** for the formula (a deterministic mathematical identity, verifiable by arithmetic — see
reproduction below) and the 1933/1937 historical attribution (corroborated across >=3 independent
sources). The "reasonable span = 5-6" *recommendation* is **Moderate** (a 1933 judgement, not an
empirical study); modern empirics (source 07) supersede the prescriptive number.

## The formula (REPRODUCED EXACTLY, with verification)
Graicunas identified three relationship types a superior must manage with *n* subordinates:
1. **Direct single relationships** = `n`
2. **Cross relationships** (subordinate <-> subordinate, in both directions) = `n(n - 1)`
3. **Direct group relationships** (superior with subsets of subordinates) = `n(2^(n-1) - 1)`

**Total relationships:**

```
C(n) = n * ( 2^(n-1) + n - 1 )
```

equivalently  C(n) = n*2^(n-1) [group + direct] + n(n-1) [cross].

**Worked verification table (arithmetic checks the identity):**

| n | C(n) = n(2^(n-1) + n - 1) | check |
|---|---|---|
| 1 | 1(1 + 0) | **1** |
| 2 | 2(2 + 1) | **6** |
| 3 | 3(4 + 2) | **18** |
| 4 | 4(8 + 3) | **44** |
| 5 | 5(16 + 4) | **100** |
| 6 | 6(32 + 5) | **222** |

Key finding: as subordinates rise **arithmetically** (1,2,3,4,5,6), the relationships to manage rise
**near-geometrically** (1,6,18,44,100,222). Graicunas deduced a "reasonable span" of ~5-6.

> **CITATION-FIDELITY NOTE (down-rate flag):** some secondary pages render the exponent as
> `2^(n/2)` or print C(6)=244. Those are transcription artifacts: only the exponent `(n-1)` with
> cross-term `n(n-1)` reproduces the canonical 1,6,18,44,100 sequence (e.g. n=4: 4(8+3)=44; the
> `2^(n/2)` form gives 4(4+3)=28, which is wrong). C(6)=222 by this identity; the "244" variant is
> a known historical mis-print. AutoFirm uses the arithmetic-verified form above.

## Reproducibility note
The identity is self-verifying (any reviewer can recompute the table). Historical attribution
(1933 Bulletin; 1937 Gulick & Urwick reprint) is corroborated by >=3 independent sources.
