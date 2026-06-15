# SUMMARY — Saltzer & Schroeder: The Protection of Information in Computer Systems

## Full citation
- **Title:** The Protection of Information in Computer Systems
- **Authors:** Jerome H. Saltzer; Michael D. Schroeder
- **Year:** 1975
- **Venue:** Proceedings of the IEEE, Vol. 63, No. 9, pp. 1278-1308.
- **DOI/URL:** DOI 10.1109/PROC.1975.9939 ; mirror https://www.cs.virginia.edu/~evans/cs551/saltzer/

## Questions informed
- **L1.A7.3** (primary) — the foundational source for least-privilege and fail-safe (fail-closed) defaults; the canonical security-design principles AutoFirm's agent security inherits.

## GRADE tier
**High.** Seminal peer-reviewed primary work (Proceedings of the IEEE); the origin of "least privilege" and "fail-safe defaults" as named principles, still standard in security curricula. Primary anchor for L1.A7.3.

## Key claims (faithful, exact — the eight design principles)
1. **Economy of mechanism** — keep the design as simple and small as possible.
2. **Fail-safe defaults** — base access decisions on **permission rather than exclusion** (i.e. default deny; the absence of an explicit grant means no access). *This is the source of "fail-closed".*
3. **Complete mediation** — every access to every object must be checked for authority.
4. **Open design** — security must not depend on the secrecy of the design (rely on keys/passwords, not obscurity).
5. **Separation of privilege** — where feasible, require two separate keys/conditions to grant access (no single point of authority).
6. **Least privilege** — "every program and every user of the system should operate using the least set of privileges necessary to complete the job."
7. **Least common mechanism** — minimize mechanism shared by/depended on by more than one user.
8. **Psychological acceptability** — security must be easy to use or it will be bypassed.

## Verification note
The eight principles, with the verbatim least-privilege definition and the "permission rather than exclusion" fail-safe-defaults formulation, confirmed across the Wikipedia summary of the paper, the University of Virginia hosted copy of the original, and Shostack's principle breakdown — three independent surfaces agree, and all trace to the single 1975 primary work (counted as one primary source per DEPTH-RUBRIC independence rule, but it IS the primary). Venue/DOI (Proc. IEEE 63(9), 10.1109/PROC.1975.9939) is the standard citation of record.

## Reproducibility
Read the "Design Principles" section of the 1975 paper (UVa mirror is public); the eight principles are enumerated there.
