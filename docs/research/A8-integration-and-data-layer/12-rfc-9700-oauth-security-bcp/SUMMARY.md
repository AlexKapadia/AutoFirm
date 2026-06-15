# SUMMARY — IETF RFC 9700 — Best Current Practice for OAuth 2.0 Security (BCP 240)

## Full citation
- **Title:** "Best Current Practice for OAuth 2.0 Security" (RFC 9700; BCP 240).
- **Author/Org:** T. Lodderstedt, J. Bradley, A. Labunets, D. Fett; IETF OAuth Working Group.
- **Year:** January 2025.
- **Venue/Publisher:** Internet Engineering Task Force (IETF), Best Current Practice (BCP) series.
- **URL / DOI:** https://www.rfc-editor.org/rfc/rfc9700 · DOI: 10.17487/RFC9700

## Questions informed
- **L1.A8.3** Secrets & credential scoping for autonomous agents — the **current** IETF security baseline that updates RFC 6749/8693 [#10] with concrete attacker-model-driven requirements (token leakage, audience restriction, sender-constraining), closing the "OAuth security for non-human/agent clients" open item.

## GRADE tier
**High.** IETF Best Current Practice — a primary standards-track-equivalent document with a stated attacker model and normative (MUST/SHOULD) requirements. Independent of NIST [#09] and complements the base RFCs [#10].

## Key claims (normative, with section locators)
1. **Sender-constrained / audience-restricted tokens (§2.2, §4.8):** RFC 9700 requires that access tokens "SHOULD be restricted to certain resource servers (audience restriction)... The resource server MUST verify ... whether the access token ... was meant to be used at that resource server." -> bearer tokens that work anywhere are rejected; each agent->tool hop's token is bound to its intended audience (reinforces RFC 8693 audience setting [#10]).
2. **Sender-constraining mechanisms (§2.2):** recommends sender-constrained access tokens via mutual-TLS (RFC 8705) or DPoP (RFC 9449) so a leaked token "cannot be used by an illegitimate party." -> a stolen leaf-agent token is useless without the binding key.
3. **No tokens in URLs / logs (§4.3.2):** access tokens "MUST NOT be ... transmitted in the query component" of URIs and must be protected from leakage. -> corroborates our "secrets never in prompts/logs" rule from an independent primary.
4. **Refresh-token protection (§4.14):** refresh tokens for public clients MUST be sender-constrained or rotated with replay detection. -> drives short-TTL + rotation for any standing agent credential.
5. **Attacker model (§3):** explicitly assumes attackers who can read network traffic, obtain leaked tokens, and operate malicious endpoints -> matches the autonomous-agent threat surface (a compromised tool/leaf agent).

## Up/down-rate reasoning
- Up-rated: it is the *current* (2025) consolidated security guidance; supersedes scattered advice; normative language is directly testable. Independent body (IETF) from NIST ZTA [#09].
- Down-rate (indirectness, minor): written for human-facing OAuth deployments; non-human agent identity is an *application* of it, so pair with SPIFFE [#13] for workload identity specifics. Not over-claimed beyond what the RFC states.

## Reproducibility note
Section numbers (§2.2 token replay/audience, §3 attacker model, §4.3.2 token leakage, §4.8 audience restriction, §4.14 refresh tokens) are stable in the published RFC 9700 text at rfc-editor.org.
