# SUMMARY — NIST SP 800-218: Secure Software Development Framework (SSDF) v1.1

## Full citation
- **Title:** Secure Software Development Framework (SSDF) Version 1.1: Recommendations for Mitigating the Risk of Software Vulnerabilities
- **Authors/Org:** Murugiah Souppaya, Karen Scarfone, Donna Dodson (NIST)
- **Year:** 2022
- **Venue:** NIST Special Publication 800-218. DOI: 10.6028/NIST.SP.800-218
- **URL:** https://nvlpubs.nist.gov/nistpubs/specialpublications/nist.sp.800-218.pdf ; project https://csrc.nist.gov/projects/ssdf
- **Companion:** NIST SP 800-218A (2024) - SSDF Community Profile for Generative AI and Dual-Use Foundation Models. https://csrc.nist.gov/pubs/sp/800/218/a/final

## Questions it informs
- **L1.B14.3** (secure-SDLC for delivered software).

## What it is
A non-prescriptive, outcome-focused framework of secure-development practices, integrable into any SDLC (Agile/DevOps/Waterfall). Produced in response to US Executive Order 14028. It is the de-facto reference for "secure SDLC" in US federal software acquisition (tied to attestation requirements).

## Structure (exact)
Four practice groups:
1. **PO - Prepare the Organization** (define security requirements, roles, toolchains, criteria).
2. **PS - Protect the Software** (protect code/integrity, provenance, archive releases).
3. **PW - Produce Well-Secured Software** (threat modelling, secure design, code review, **automated static + dynamic analysis**, test against security requirements, secure defaults, secure configuration).
4. **RV - Respond to Vulnerabilities** (identify, assess, remediate, root-cause to prevent recurrence; disclosure handling).

Each practice has tasks, notional implementation examples, and references to other standards (BSIMM, OWASP, SAMM, ISO 27034).

## Key practices AutoFirm-relevant (exact task IDs)
- **PW.7/PW.8:** review and analyse human-readable code (manual + tooling) and test executable code (SAST/DAST/fuzz) to find and fix vulnerabilities before release.
- **PW.4:** reuse well-secured software (vetted dependencies) - ties to SCA/dependency scanning.
- **PS.3:** archive and protect each release with provenance data (SBOM lineage).
- **PO.3:** implement supporting toolchains with security automation in CI/CD.

## GRADE tier
**High.** Official US government standard (NIST), widely adopted, peer-reviewed public-comment process. Authoritative for the "what practices constitute secure SDLC" claim.

## Reproducibility note
Public standard; practice IDs (PO/PS/PW/RV) are stable and citable. The four-group structure is corroborated by CISA, Black Duck, and the SSDF project page.
