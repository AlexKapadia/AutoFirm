# BEST-PARTS — OWASP SAMM & DSOMM

## ADOPT
1. **DSOMM as the concrete pipeline-hardening checklist** for AutoFirm's client CI/CD. Where NIST SSDF says *what outcomes*, DSOMM says *which pipeline activities* and at what maturity (static analysis depth, dynamic-scan depth, dependency checks, secrets detection, infra hardening). AutoFirm should target a defined DSOMM maturity per client risk tier and auto-provision the activities for that tier.
2. **SAMM's risk-driven, leveled structure** to right-size security to the client. Not every client needs advanced maturity; SAMM's 3-level model lets AutoFirm scale security effort to the client's actual risk (a fintech client -> advanced; an internal tool -> foundational), satisfying generality across industries without over- or under-engineering.
3. **Verification function alignment**: SAMM's Verification practices (security testing, requirements-driven testing) reinforce the SAST/DAST/fuzz/review stack from sources 05/07/11.

## REJECT
- Reject a single fixed security level for all clients — SAMM's whole point is risk-tiering; a one-size policy either wastes effort or under-protects high-risk clients.

## Concrete artifact this drives
- A **risk-tier -> DSOMM-activity-set** mapping table in the client-delivery engine: client risk classification selects the mandatory pipeline security activities and the target SAMM maturity, recorded in the secure-sdlc-manifest (source 07).
