# SUMMARY — SPIFFE: Secure Production Identity Framework For Everyone (workload identity)

## Full citation
- **Title:** "The SPIFFE Standards" — SPIFFE ID, SVID (X.509-SVID and JWT-SVID), and the Workload API specifications; plus the SPIFFE/SPIRE concepts overview.
- **Author/Org:** SPIFFE project, a graduated project of the Cloud Native Computing Foundation (CNCF).
- **Year:** specifications maintained current; SPIFFE/SPIRE reached CNCF graduation in 2022.
- **Venue/Publisher:** CNCF / SPIFFE project (spiffe.io), open specifications on GitHub (spiffe/spiffe).
- **URL:** https://spiffe.io/docs/latest/spiffe-about/spiffe-concepts/ · Specs: https://github.com/spiffe/spiffe/tree/main/standards (SPIFFE-ID.md, X509-SVID.md, JWT-SVID.md, SPIFFE_Workload_API.md)

## Questions informed
- **L1.A8.3** Secrets & credential scoping for autonomous agents — directly closes the open item "non-human agent identity for OAuth: evolving area." SPIFFE provides a standard, cryptographically-verifiable **identity for non-human workloads/agents** that underpins per-session, least-privilege credential issuance.

## GRADE tier
**Moderate->High.** Open specification from a CNCF graduated project (a maturity bar requiring broad adoption, security audit, and governance). Independent of NIST [#09] and IETF [#10][#12]; provides the *workload-identity primitive* those token systems then scope.

## Key claims (specification facts + locators)
1. **SPIFFE ID = a URI naming a workload (SPIFFE-ID.md):** identity is a URI of the form `spiffe://trust-domain/path` (e.g. `spiffe://autofirm.example/agent/reader/session-123`) — a stable, parseable name for a non-human caller. -> gives each agent/session a first-class identity to scope credentials and audit lineage to.
2. **SVID = a verifiable identity document (X509-SVID.md / JWT-SVID.md):** the SPIFFE ID is carried in a short-lived **X.509 certificate** (SAN URI) or signed **JWT**, cryptographically attesting the workload's identity. -> the binding key that enables sender-constrained tokens (RFC 9700 §2.2 [#12]).
3. **Workload API delivers identity with no secrets to manage (SPIFFE_Workload_API.md):** a workload fetches its SVID at runtime from a local Workload API endpoint after **attestation**, "without the need ... to handle ... secrets" -> no long-lived key on disk/in prompt; rotation is automatic. Corroborates "credentials runtime-injected, never standing" [#09].
4. **Short-lived, auto-rotated credentials (SPIRE concepts):** SVIDs are issued with short TTLs and automatically rotated by the SPIRE agent -> matches the per-session, short-TTL, auto-revoke ZTA design [#09].
5. **Trust-domain boundary:** the `trust-domain` portion of the SPIFFE ID is the isolation boundary for identities -> a clean primitive for keeping one tenant's/company's agent identities separate from another's (ties to A8.2 isolation).

## Up/down-rate reasoning
- Up-rated: CNCF graduation implies independent security review + wide production use; the spec is the primary source-of-record; directly addresses the non-human-identity gap the other A8.3 sources only imply.
- Down-rate (scope): SPIFFE supplies *identity + attestation*, not authorization scope by itself — it is the foundation that OAuth scoping [#10] and RFC 9700 sender-constraining [#12] build on. Cited only for the identity/attestation/rotation primitive.

## Reproducibility note
Spec facts (SPIFFE ID URI format, X.509-SVID SAN-URI encoding, JWT-SVID, Workload API attestation, short-lived auto-rotation) are stable in the spiffe/spiffe standards repo and spiffe.io concepts docs.
