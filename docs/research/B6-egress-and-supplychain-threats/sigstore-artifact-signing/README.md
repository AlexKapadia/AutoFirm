# Sigstore — Artifact Signing & Verification (Cosign / Fulcio / Rekor)

## 1. Full Citation

- **Title:** Sigstore documentation — Cosign signing overview & Security Model
- **Author / Org:** Sigstore project (OpenSSF / Linux Foundation; contributors incl. Google, Red Hat, Chainguard)
- **Year:** current docs (2025)
- **Primary URLs:**
  - Cosign signing overview: https://docs.sigstore.dev/cosign/signing/overview/
  - Security model / trust root: https://docs.sigstore.dev/about/security/
  - Cosign quickstart: https://docs.sigstore.dev/quickstart/quickstart-cosign/
  - Source: https://github.com/sigstore/cosign

## 2. Faithful Structured Summary

Sigstore is an open framework for **signing, verifying, and proving the provenance of software artifacts** (containers, binaries, and other OCI artifacts). Its headline capability is **keyless signing**: associating **identities, not long-lived keys**, with a signature. Three core components:

- **Fulcio (Certificate Authority):** issues **short-lived, time-stamped code-signing certificates** binding an **ephemeral key to an OpenID Connect (OIDC) identity**. Cosign requests a cert; Fulcio confirms the identity via OIDC and grants the short-lived cert.
- **Rekor (Transparency Log):** an **append-only signature transparency log**. Signing events are entered as **timestamped, signed entries** that "witness" that the signing occurred. End users can request an entry and **cryptographically verify** that the artifact was signed **while the certificate was valid**.
- **Cosign (the tool):** requests the Fulcio cert (subject = the OIDC identity/email), stores the signature + certificate in **Rekor**, and uploads the signature to the OCI registry **alongside the artifact**.

**Trust root:** Fulcio's root CA cert and Rekor's public key are distributed via **The Update Framework (TUF)**.

**Verification (faithful):** because certificates are short-lived, verification relies on the Rekor entry's **signed timestamp** to prove the signature was made during the certificate's validity window — even after the cert expires. Verification confirms **who** signed (the OIDC identity) and **that the artifact is unmodified**.

## 3. Best Parts to Take → AutoFirm controls

| Sigstore finding | AutoFirm control it grounds |
| --- | --- |
| **Verify signature + identity (OIDC subject) before trusting an artifact** | The concrete mechanism behind AutoFirm's **signed-manifest verification before load**: a skill/MCP artifact must carry a valid Sigstore signature from an **allowlisted signing identity**, or loading is **refused (fail-closed)**. |
| **Rekor transparency log = tamper-evident, append-only record of every signing event** | Mirrors AutoFirm's **append-only audit log** requirement, and gives a verifiable answer to "who signed this skill and when" — supports detecting a silent post-audit swap ("rug pull"). |
| **Short-lived certs + identity binding (no long-lived god-keys)** | Reinforces **least-privilege / no shared god-keys**: each signer is a scoped identity, not a shared static key that can leak. |
| **Verification proves both authorship and integrity** | Pair with **version-pinning + digest check**: AutoFirm verifies (a) signature/identity via Sigstore and (b) the pinned digest matches — so an unverified *or* unpinned artifact never loads. |
| **TUF-distributed trust root** | Pattern for distributing AutoFirm's own allowlist of trusted signers without a single point of compromise. |
