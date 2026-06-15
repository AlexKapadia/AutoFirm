# SUMMARY — OWASP Application Security Verification Standard (ASVS) v4.0.3 — V4 Access Control

## Full citation
- **Title:** OWASP Application Security Verification Standard (ASVS), Version 4.0.3 — "V4: Access Control Verification Requirements".
- **Author/Org:** OWASP Foundation (Andrew van der Stock, Daniel Cuthbert, Jim Manico, Josh C. Grossman, Mark Burnett, eds.).
- **Year:** 2021 (v4.0.3; the v4.0 line first released 2019).
- **Venue/Publisher:** OWASP Foundation (community standard; de-facto application-security verification baseline used in procurement and assurance).
- **URL:** https://owasp.org/www-project-application-security-verification-standard/ · PDF: https://github.com/OWASP/ASVS/raw/v4.0.3/4.0/OWASP%20Application%20Security%20Verification%20Standard%204.0.3-en.pdf

## Questions informed
- **L1.A8.2** Multi-tenant data isolation — the **third independent** verification-standard source corroborating that tenant isolation must be enforced server-side and tested, not left to convention.
- **L1.A8.1** (supporting) — V5 input-validation / V13 API requirements reinforce untrusted-by-default handling.

## GRADE tier
**Moderate->High.** Community standard, but authored by a recognized expert panel, widely adopted as a verification contract, and explicitly framed as testable requirements. Independent of PostgreSQL [#08] and AWS [#07] (different org, different evidence base). Corroborates the *principle and testability* of tenant isolation, not Postgres-specific mechanics.

## Key claims (exact requirement IDs + locators)
1. **Server-side trusted enforcement (V4.1.1):** "Verify that the application enforces access control rules on a trusted service layer, especially if client-side access control is present and could be bypassed." -> isolation must live in a trusted layer (data/service layer), echoing CLAUDE.md §5.6 "not by convention."
2. **Fail securely / deny by default (V4.1.5):** "Verify that access controls fail securely including when an exception occurs." -> fail-closed default, corroborating Postgres default-deny [#08].
3. **Least privilege (V4.1.3):** "Verify that the principle of least privilege exists - users should only be able to access functions, data files, URLs, controllers, services, and other resources, for which they possess specific authorization." -> ties to A8.3 credential scoping.
4. **IDOR / cross-record protection (V4.2.1):** "Verify that sensitive data and APIs are protected against Insecure Direct Object Reference (IDOR) attacks targeting creation, reading, updating and deletion of records, such as creating or updating someone else's record, viewing everyone's records, or deleting all records." -> the canonical cross-tenant access test (read/update/delete of another tenant's row).
5. **Multi-tenant separation (V4.x context):** ASVS V4 covers multi-user/multi-tenant separation; combined with V4.2.1 this is the IDOR/BOLA-equivalent for tenants (aligns with, but is independent evidence from, OWASP API1:2023 BOLA and API10 [#01]).

## Up/down-rate reasoning
- Up-rated: named expert-panel authorship; framed as verifiable, testable requirements (directly drives our schema-audit + cross-tenant test). Independent corroboration of the isolation principle from a non-database, non-cloud-vendor source.
- Down-rated (scope/indirectness): technology-agnostic verification requirements, not the RLS mechanism itself. Corroborates the **must-enforce-and-test** principle; #08 remains primary for Postgres mechanics. Never a sole basis for a Postgres-specific claim.

## Reproducibility note
Requirement IDs (V4.1.1, V4.1.3, V4.1.5, V4.2.1) are stable in the v4.0.3 PDF, section "V4: Access Control Verification Requirements"; verbatim text reproducible from the linked release PDF.
