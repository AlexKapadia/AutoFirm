# SPIFFE / SPIRE — Workload Identity, SVIDs & Short-Lived Credentials

## 1. Full citation

- **Title:** "SPIFFE Concepts" + "SPIRE Concepts," *SPIFFE Project Official Documentation*
- **Author / Org:** The SPIFFE Project (a Cloud Native Computing Foundation / CNCF graduated project)
- **Year:** docs current as of 2024–2026 ("latest")
- **URLs:**
  - https://spiffe.io/docs/latest/spiffe-about/spiffe-concepts/
  - https://spiffe.io/docs/latest/spire-about/spire-concepts/
  - https://spiffe.io/docs/latest/deploying/svids/

## 2. Faithful structured summary

**SPIFFE ID.** A URI identifying a workload within a trust domain: `spiffe://<trust domain>/<workload identifier>`, e.g. `spiffe://acme.com/billing/payments`.

**SVID (SPIFFE Verifiable Identity Document).** *"The document with which a workload proves its identity to a resource or caller."* Two formats:
- **X.509-SVID:** an X.509 certificate with the SPIFFE ID encoded in the Subject Alternative Name (SAN). **Preferred** — establishes mTLS; the docs note JWT tokens *"are susceptible to replay attacks."*
- **JWT-SVID:** a JSON Web Token, with an `aud` (audience) claim, for cases where mTLS isn't feasible.

**Workload API.** Platform-agnostic; *"can identify running services at a process level as well as a kernel level."* It distributes X.509 certs + private keys (or JWTs) plus trust bundles *"without requiring that a calling workload have any knowledge of its own identity, or possess any authentication token."* — i.e. **no bootstrap secret to leak**.

**Trust domain.** *"The trust root of a system"* — *"all workloads identified in the same trust domain are issued identity documents that can be verified against the root keys of the trust domain."*

**Short-lived credentials (load-bearing, exact):** *"In order to minimize exposure from a key being leaked or compromised, all private keys (and corresponding certificates) are short lived, rotated frequently and automatically."* This **eliminates dependency on static secrets or API keys** — SVIDs often rotate hourly, shrinking the exfiltration risk window.

**SPIRE (the implementation).** The SPIRE Server is the trust anchor / CA for a domain. It holds a **Registration Entry registry** — policy rules mapping **workload-attestation attributes → SPIFFE IDs**. Issuance is gated by two-stage attestation: **node attestation** (proving which node a SPIRE Agent runs on) and **workload attestation** (the Agent verifies the calling process — e.g. by UID, path, k8s metadata — before handing it an SVID).

## 3. Best parts to take → AutoFirm controls

- **Direct blueprint for AutoFirm's credential broker.** AutoFirm states it "mints per-session, least-privilege, short-TTL, sender-constrained, audience-bound credentials (SPIFFE SVIDs)." SPIFFE is the authoritative standard behind every adjective:
  - **Short-TTL / no god-keys** ← *"all private keys … are short lived, rotated frequently and automatically"* and the explicit goal of replacing static secrets/API keys.
  - **Audience-bound** ← the JWT-SVID `aud` claim and trust-domain verification — a credential is only valid against its intended audience.
  - **Per-session identity** ← each `claude` CLI session is a "workload" with its own SPIFFE ID; the Workload API hands it credentials with **no pre-shared bootstrap token**, exactly matching AutoFirm's "no standing god-keys."
- **Attestation grounds "who gets a credential."** SPIRE's node + workload attestation is the auditable gate: AutoFirm's broker should attest a session (node + process identity) before minting an SVID, so a rogue or spoofed process cannot obtain credentials. Pairs with hashes-not-PII audit (log the SPIFFE ID + attestation result, not secrets).
- **Blast-radius containment.** Because SVIDs are short-lived and scoped to one workload, a leaked session credential expires fast and grants nothing beyond that session's audience — the core of AutoFirm's least-privilege, fail-closed posture.
- **Prefer X.509-SVID + mTLS at the egress gateway** (replay-resistant) over bearer tokens for session→gateway auth, per the docs' explicit replay warning.
