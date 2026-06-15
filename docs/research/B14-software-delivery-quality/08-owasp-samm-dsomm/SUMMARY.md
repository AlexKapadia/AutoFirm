# SUMMARY — OWASP SAMM and DSOMM (security maturity models)

## Full citation
- **Title (1):** OWASP SAMM - Software Assurance Maturity Model (v2)
- **Org:** OWASP Foundation
- **Venue/URL:** https://owaspsamm.org/model/ ; project https://owasp.org/www-project-samm/
- **Title (2):** OWASP DSOMM - DevSecOps Maturity Model
- **Org:** OWASP Foundation
- **URL:** https://dsomm.owasp.org/

## Questions it informs
- **L1.B14.3** (secure-SDLC: how to structure and measure a security program for delivered software).

## SAMM structure (exact)
- **5 business functions** -> **15 security practices** -> **30 streams**.
- The five functions: **Governance, Design, Implementation, Verification, Operations.**
- Each practice has **3 maturity levels** (foundational -> mature -> advanced) with successively stricter objectives, activities, and success metrics.
- Technology- and process-agnostic; risk-driven and evolutive; covers the full SDLC.

## DSOMM structure (exact)
- A **technical** companion to SAMM aimed at engineering teams: maps concrete DevSecOps **activities** (e.g. static analysis in pipeline, dynamic depth-of-scan, dependency checks, secrets detection, infra hardening) onto maturity levels and dimensions, giving a stepwise roadmap to harden a CI/CD pipeline.
- DSOMM dimensions include Build & Deployment, Culture & Organization, Implementation, Information Gathering, Test & Verification.

## SAMM vs DSOMM (exact distinction)
- **SAMM**: organization-wide assurance maturity (governance, compliance, risk) - written by/for security specialists, broad scope.
- **DSOMM**: technical, pipeline-level secure-DevOps implementation - written for engineering teams; more prescriptive about concrete activities.

## GRADE tier
**Moderate-High.** Recognised, widely adopted open community standards (OWASP) maintained by domain experts. Not peer-reviewed in the academic sense (down-rate slightly) but they are the de-facto professional references and corroborate NIST SSDF (source 07) on practices.

## Reproducibility note
Both models are public with stable structure. The 5/15/30 SAMM decomposition and the 3 maturity levels are taken directly from owaspsamm.org/model and corroborated by the OWASP Developer Guide and Codific/Xygeni summaries.
