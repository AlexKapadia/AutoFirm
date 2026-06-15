# BEST-PARTS — GICS Methodology 2024

## ADOPT
1. **Hold GICS as the DEMAND-SIDE parameterization alongside NAICS (supply-side).** Adopt a
   two-key `IndustryProfile`: NAICS keys operations/production playbooks (B11/B4.3); GICS (or its
   sector lens) keys investor-/market-facing playbooks - fundraising (B6), pricing posture (B5),
   and capital-markets framing. Rationale: GICS classifies by principal revenue activity + market
   perception (claim 3), which is exactly the lens fundraising/pricing playbooks need, and which
   NAICS's production principle explicitly does NOT capture.
2. **Single-classification-per-tier discipline.** GICS assigns exactly one code per tier - adopt
   the same "one canonical industry assignment per dimension" rule for AutoFirm company profiles to
   keep playbook resolution deterministic (no ambiguous multi-membership).
3. **11-sector coarse layer as a human-legible default.** GICS's 11 sectors are a compact,
   widely-understood top layer; AutoFirm can use the GICS sector as the coarsest fallback for
   market-facing playbooks (mirrors the NAICS 2-digit fallback for ops).

## REJECT
1. **REJECT GICS for operations/supply playbooks.** GICS is finance-oriented and revenue-based; it
   poorly distinguishes *how* a thing is produced (a SaaS firm and a hardware firm can share a
   sector). Use NAICS there. (This is the affirmative reason to keep BOTH, not pick one.)
2. **REJECT GICS as the universal key.** It was built for equity-index construction, not for
   running private/small companies; many AutoFirm clients won't be public. Treat GICS as an
   *optional* enrichment on the profile, NAICS as the always-present key.

## Build implication
`IndustryProfile.gics_code` optional; playbook resolver routes ops/delivery parameters by NAICS and
market/finance-facing parameters (fundraising stage norms, pricing posture) by GICS sector when
present, else falls back to the business-model axes. Test: the fintech and SaaS fixed-panel rows
resolve DIFFERENT fundraising/pricing parameters via GICS sector, proving the demand-side axis adds
signal beyond NAICS.
