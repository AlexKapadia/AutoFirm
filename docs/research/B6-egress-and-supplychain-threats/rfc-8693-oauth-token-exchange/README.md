# RFC 8693 — OAuth 2.0 Token Exchange (per-hop scope/audience narrowing)

## 1. Full citation

- **Title:** *RFC 8693 — OAuth 2.0 Token Exchange*
- **Authors:** M. Jones, A. Nadalin, B. Campbell (Ed.), J. Bradley, C. Mortimore
- **Org / Year:** IETF, **January 2020** (Proposed Standard)
- **URL:** https://www.rfc-editor.org/rfc/rfc8693.html

## 2. Faithful structured summary

**Purpose (abstract).** Defines *"a protocol for an HTTP- and JSON-based Security Token Service (STS) by defining how to request and obtain security tokens from OAuth 2.0 authorization servers, including security tokens employing impersonation and delegation."* A client exchanges one token for another — typically a **narrower** one — across security domains.

**Core request inputs:**
- **`subject_token`** — the identity on whose behalf the request is made.
- **`actor_token`** — (optional) the party authorized to use the token (the acting party).

**Scope-control parameters (the downscoping levers):**
- **`scope`** — space-delimited list restricting the new token's access rights.
- **`resource`** — an absolute URI naming where the token will be used.
- **`audience`** — the logical name of the target service.

The **fundamental rule** (as reflected across implementers): the newly issued token **must not have broader privileges than the original** — it must be *downscoped*. Audience *"may never contain an audience which was not already present in either the subject_token or actor_token combined."* Using `resource`/`audience` to limit a token's destination *"minimize[s] the potential damage in the unlikely event the new token is leaked."*

**Delegation vs. impersonation:**
- **Impersonation:** *"A is B within the context of the rights authorized by the token"* — A becomes indistinguishable from B.
- **Delegation:** *"principal A still has its own identity separate from B … any actions taken are being taken by A representing B."*

**The `act` claim.** Expresses delegation inside a JWT; nested `act` claims form a delegation chain where *"the current actor is considered to include the entire authorization/delegation history."* The `scope` claim *"restricts the contexts in which the delegated rights can be exercised."*

## 3. Best parts to take → AutoFirm controls

- **Grounds per-hop scope narrowing through AutoFirm's chain.** AutoFirm is a chain of orchestrated sessions: orchestrator → manager → worker → egress gateway → external provider. RFC 8693 is the standard for ensuring **each hop hands down a strictly-narrower credential** (`scope`/`resource`/`audience` reduced), so a leaf worker session never holds the orchestrator's full authority. This is the protocol realization of AutoFirm's "least-privilege, no god-keys."
- **`audience`/`resource` binding = "useless beyond its destination."** Binding each minted token to exactly one target (the specific provider endpoint behind the gateway) means a leaked session token can't be redirected at another service — directly grounding AutoFirm's "audience-bound credentials" claim and blast-radius containment.
- **`act` claim = auditable delegation chain.** The nested-`act` delegation history maps onto AutoFirm's hashes-not-PII audit log: every external call records *which session, acting on behalf of which parent*, giving the regulator-grade "what, when, who" trail without embedding secrets.
- **"Downscope only" rule is a fail-closed invariant.** The broker must **refuse** to mint a token broader than its parent (and refuse if scope/audience is ambiguous), matching AutoFirm's deny-by-default posture.
- **Complements SPIFFE + DPoP.** SPIFFE issues the workload identity; RFC 8693 narrows authority per hop; DPoP (RFC 9449) sender-constrains the resulting token. Together they implement the full "short-TTL, sender-constrained, audience-bound, least-privilege" credential the broker promises.
