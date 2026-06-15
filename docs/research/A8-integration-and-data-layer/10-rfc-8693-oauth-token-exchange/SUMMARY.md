# SUMMARY — RFC 8693: OAuth 2.0 Token Exchange (with RFC 6749 context)

## Full citation
- **Title:** OAuth 2.0 Token Exchange.
- **Authors:** M. Jones, A. Nadalin, B. Campbell (ed.), J. Bradley, C. Mortimore.
- **Year:** January 2020.
- **Venue/Publisher:** IETF, RFC 8693 (Proposed Standard).
- **URL:** https://www.rfc-editor.org/info/rfc8693/ · https://datatracker.ietf.org/doc/html/rfc8693
- **Base spec:** RFC 6749, *The OAuth 2.0 Authorization Framework*, D. Hardt (ed.), Oct 2012 — https://www.rfc-editor.org/rfc/rfc6749 (defines scopes + delegated authorization).

## Questions informed
- **L1.A8.3** Secrets & credential scoping for autonomous agents — standardized scope-narrowing and delegation chains.

## GRADE tier
**High.** Official IETF standards-track RFCs — authoritative source of record for OAuth scoping/delegation.

## Key claims (with locators)
1. **Scopes for least privilege (RFC 6749 §3.3):** the `scope` parameter expresses the granularity of access; tokens are issued with the minimum scopes the client requests/needs — the OAuth primitive for least-privilege third-party access. Tokens are revocable without rotating a password.
2. **Token Exchange (RFC 8693 §1, §2):** defines an STS protocol to exchange one security token for another, "including security tokens employing impersonation and delegation." Enables a service/gateway to swap a token for one with narrower scope and a specific audience before proxying downstream.
3. **Least-privilege propagation (§1.1):** exchanging for a token with fewer permissions/narrower audience limits blast radius if the downstream token is compromised.
4. **Delegation semantics (§4.1, the `act` claim):** the `act` (actor) claim expresses that a principal is acting on behalf of another; `act` claims nest to represent a delegation chain (who-acting-for-whom) — auditable delegation lineage.

## Up/down-rate reasoning
- Up-rated: IETF standards-track; directly on-point for scoped, delegated, revocable agent credentials and for representing the human->agent delegation chain (`act`).
- Indirectness: OAuth targets user-to-service delegation; for AutoFirm, an agent session is the "client" and token exchange narrows scope across the agent->tool hop — a direct application, but agent-identity specifics (non-human principals) are an active area beyond the RFC text.

## Reproducibility note
`scope` semantics in RFC 6749 §3.3; token-exchange STS + `act` delegation claim in RFC 8693 §1-2, §4.1. Both are stable published standards-track RFCs.
