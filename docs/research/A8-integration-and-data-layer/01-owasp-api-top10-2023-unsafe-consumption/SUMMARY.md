# SUMMARY — OWASP API Security Top 10 (2023): API10 Unsafe Consumption of APIs

## Full citation
- **Title:** OWASP API Security Top 10 — 2023 edition; specifically *API10:2023 — Unsafe Consumption of APIs*.
- **Author/Org:** OWASP API Security Project (community standard).
- **Year:** 2023.
- **Venue/Publisher:** OWASP Foundation (official project edition).
- **URL:** https://owasp.org/API-Security/editions/2023/en/0xaa-unsafe-consumption-of-apis/

## Questions informed
- **L1.A8.1** External-tool/API integration patterns & untrusted-input handling.

## GRADE tier
**Moderate** (official standard; up-rated to high-confidence for the normative claim "treat third-party API responses as untrusted" because corroborated by NIST SP 800-204 and the LLM-agent injection literature — independent orgs).

## Key claims (with locators)
1. **Root cause (exact):** "Developers tend to trust data received from third-party APIs more than user input" and therefore "adopt weaker security standards … in regards to input validation and sanitization." (API10:2023 description.)
2. **Vulnerability indicators:** unencrypted channels; fails to validate/sanitize third-party data before processing; "blindly follows redirections"; lacks resource limits for processing third-party responses; omits timeouts for third-party interactions.
3. **Prevention (official guidance):**
   - "When evaluating service providers, assess their API security posture."
   - "Ensure all API interactions happen over a secure communication channel (TLS)."
   - "Always validate and properly sanitize data received from integrated APIs before using it."
   - "Maintain an allowlist of well-known locations integrated APIs may redirect yours to: do not blindly follow redirects."
4. Injection (SQLi/NoSQLi/command) lost its standalone 2019 category but is folded across 2023 categories; mitigation = parameterized queries + input validation + output encoding.

## Up/down-rate reasoning
- Up-rated: official standard; "untrusted third-party data" principle independently echoed by NIST SP 800-204 and the LLM-agent injection papers.
- Down-rated for empirical precision: gives no measured effect sizes (normative checklist, not a study); quantitative thresholds must come from measured sources.

## Reproducibility note
Re-fetch the official 2023 edition page; the four prevention bullets and five vulnerability indicators are stated on that single page, stable across the published 2023 edition.
