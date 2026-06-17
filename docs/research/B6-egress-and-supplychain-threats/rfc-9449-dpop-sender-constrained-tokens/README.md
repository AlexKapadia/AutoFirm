# RFC 9449 — DPoP: Sender-Constrained OAuth Tokens ("useless if leaked")

## 1. Full citation

- **Title:** *RFC 9449 — OAuth 2.0 Demonstrating Proof of Possession (DPoP)*
- **Authors:** D. Fett, B. Campbell, J. Bradley, T. Lodderstedt, M. Jones, D. Waite
- **Org / Year:** IETF, **September 2023** (Proposed Standard)
- **URL:** https://www.rfc-editor.org/rfc/rfc9449.html

## 2. Faithful structured summary

**Abstract (load-bearing, exact):** DPoP describes *"a mechanism for sender-constraining OAuth 2.0 tokens via a proof-of-possession mechanism on the application level."* It enables *"detection of replay attacks with access and refresh tokens."*

**Token binding to a key pair.** The client proves possession of a public/private key pair by including a cryptographically signed JWT in the `DPoP` HTTP header. The authorization server binds the issued token to *"the public part of a client's key pair,"* constraining legitimate use to *"the sender that holds and proves possession of the private key."*

**The DPoP proof JWT — signed fresh per request.** Each HTTP request carries a unique proof JWT containing:
- the HTTP method and target URI (binds the proof to *this* request),
- `iat` timestamp,
- `jti` unique identifier (replay nonce),
- `ath` — a SHA-256 hash of the access token (when presenting one),
- optionally a server-supplied `nonce`.

**Why a stolen token is useless.** Without the corresponding **private key**, an attacker cannot generate a valid DPoP proof; the resource server verifies the proof signature and confirms the *"public key to which the access token is bound matches the public key of the DPoP proof."* A bearer token alone is inert — *a token plus a correctly-scoped, freshly-signed proof* is what grants access.

**Replay detection.** Servers track `jti` values within a time window and validate `iat`; optional server-issued nonces defeat pre-generated proofs.

## 3. Best parts to take → AutoFirm controls

- **This is the authoritative basis for "sender-constrained" in AutoFirm's credential promise.** The broker mints *sender-constrained* credentials; DPoP is the IETF mechanism that makes that real: each `claude` CLI session holds a private key, and every egress request to the gateway carries a fresh DPoP proof. A credential exfiltrated from session memory or logs is **useless without the private key** — exactly AutoFirm's "useless if leaked" goal.
- **Per-request proof = the strongest fit for an autonomous, high-volume platform.** Because AutoFirm runs unattended and makes many external calls, bearer tokens are a large theft surface. DPoP's per-request signed proof + `jti`/`nonce` replay defense means a captured request can't be replayed against the gateway — hardening the single egress chokepoint against credential-replay abuse.
- **Binds the token to method+URI** → grounds the gateway's audience/resource binding (with RFC 8693) at the wire level: a proof minted for one provider endpoint can't be retargeted.
- **Replay defense complements SPIFFE's X.509-SVID choice.** The SPIFFE docs warn JWT-SVIDs are replay-prone; DPoP is the answer where bearer-style tokens are unavoidable, giving replay resistance without full mTLS. Use mTLS (X.509-SVID) session→gateway, DPoP-style sender-constraint gateway→provider where the provider supports it.
- **Audit alignment.** The `jti` and key thumbprint are non-PII identifiers — log them (hashes-not-PII audit) to prove sender-constraint held on every external call, fail-closed if a proof is missing or stale.
