# B6 — Egress & Supply-Chain Threats (Cross-Cutting Threat Set) — Research Library

Deep, primary-sourced research for the **cross-cutting threat model** spanning multi-model egress,
dynamically-loaded capabilities, and the audit/billing ledger — the STRIDE "delta" set that the
per-workstream designs (B1/B4/B5) must defend against. Institution-grade, **fail-closed** bar;
research gates building (CLAUDE.md §2 CRO, §3.3, §4.6, §5.6). One folder per source.

## Sources (one folder per source — §4.6)

| Folder | Source | One-line takeaway |
|--------|--------|-------------------|
| `owasp-llm-top-10-2025` | OWASP Top 10 for LLM Applications (2025) | Canonical LLM threat taxonomy (prompt injection, supply chain, excessive agency, …). |
| `owasp-api4-resource-consumption` | OWASP API Security Top 10 — API4:2023 | **Unrestricted resource consumption** — cost/DoS via uncapped egress; rate/budget limits. |
| `camel-defeating-prompt-injection-by-design` | CaMeL — "Defeating Prompt Injections by Design" | **Control-flow integrity** so untrusted data cannot seize control (does NOT certify content trustworthy). |
| `dual-llm-pattern-willison` | Willison — Dual LLM pattern (2023) | Quarantined LLM handles untrusted text; privileged LLM never sees it — CaMeL precursor. |
| `mcp-tool-poisoning-rug-pull` | Invariant Labs — MCP tool poisoning / rug-pull | Tool descriptions can carry hidden instructions; definitions can mutate post-approval. |
| `crosby-wallach-tamper-evident-logging` | Crosby & Wallach (USENIX Security 2009) | **History trees**: why naive hash chains fail (truncation/equivocation); O(log n) incremental proofs. |
| `rfc-6962-certificate-transparency` | RFC 6962 (IETF, 2013) | Merkle leaf/node domain separation (`0x00`/`0x01`), STH, audit & consistency proofs. |
| `nist-sp-800-92-log-management` | NIST SP 800-92 (Kent & Souppaya, 2006) | Log integrity (digests/signatures), write-once storage, access restriction, separation of duties. |
| `billing-reconciliation-internal-control` | FinOps Invoicing/Chargeback + FOCUS; COSO | Usage/billing reconciliation as an **internal control**; zero-drift target. |
| `slsa-supply-chain-framework` | SLSA (OpenSSF / Linux Foundation) | **Supply-chain assurance levels** L0–L3 for build provenance and artifact integrity. |
| `sigstore-artifact-signing` | Sigstore (Cosign / Fulcio / Rekor) | **Keyless artifact signing** + transparency log (Rekor) for verify-before-load. |
| `spiffe-spire-workload-identity` | SPIFFE / SPIRE | **Workload identity (SVIDs)** + short-lived credentials — no shared god-keys. |
| `rfc-8693-oauth-token-exchange` | RFC 8693 (IETF, 2020) | **Per-hop scope/audience narrowing** via token exchange (downscope-only). |
| `rfc-9449-dpop-sender-constrained-tokens` | RFC 9449 (IETF, 2023) | **DPoP sender-constrained tokens** — "useless if leaked" without the private key. |
| `erlang-otp-supervision-trees` | Erlang/OTP supervisor behaviour | **"Let it crash" + supervision trees** — bounded, isolated restart of failed workers. |
| `google-sre-cascading-failures` | Google SRE Book, Ch. 22 | Preventing **cascading failures** (load shedding, jittered retry, bounded queues). |
| `safely-interruptible-agents` | Orseau & Armstrong (2016) | Formal **kill-switch / safe-interruptibility** foundation for a global halt control. |

## Threat-model synthesis
- `stride-deltas-draft.md` — the STRIDE delta set: the new threats introduced by multi-model
  egress + dynamic capabilities + the cost ledger, mapped to the defences above, with the
  "most dangerous attack" (shared-knowledge poisoning) called out as outside CaMeL's guarantee.

## Faithfulness status (CRO Gate-0)
RFC-6962 hashing reproduced here was **verified verbatim 2026-06-17 against rfc-editor.org §2.1**.
**Crosby–Wallach (2009)** and **NIST SP 800-92** are faithful *conceptual* summaries — their
canonical PDFs returned 403 / non-text streams at fetch time, so the files carry an explicit
**"re-verify exact wording against the canonical PDF before regulator-facing verbatim quotation"**
marker. No verbatim quote from those two is presented as PDF-confirmed. No overclaims found.
