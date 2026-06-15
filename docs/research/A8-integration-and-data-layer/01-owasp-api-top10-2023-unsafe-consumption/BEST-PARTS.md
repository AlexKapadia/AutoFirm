# BEST-PARTS — OWASP API10:2023 Unsafe Consumption of APIs

## ADOPT
- **Untrusted-by-default boundary on ALL external data.** AutoFirm's integration layer must treat **every** external response (third-party SaaS APIs, MCP tool outputs, scraped pages, registry/filing data) as untrusted — the same bar as raw user input. → drives the `external_input` contract: every inbound payload passes a typed schema validator + sanitizer before any agent or DB sees it. (CLAUDE.md §3.2/§5.6 "validate input at every boundary, deny by default".)
- **TLS-only egress.** Reject any plaintext API interaction at the gateway. → a fail-closed egress policy: no `http://` calls; cert validation mandatory.
- **Redirect allowlist.** "Do not blindly follow redirects" → the egress proxy holds a per-tenant/per-tool allowlist of permitted hosts; cross-host redirects are returned, not auto-followed (mirrors the WebFetch tool's own behavior).
- **Resource limits + timeouts** on every third-party call → bounded response size, hard timeout, and a circuit-breaker, preventing a malicious/slow provider from DoS-ing an agent run.

## REJECT (for AutoFirm's purposes)
- **Provider-reputation as a trust shortcut** — the standard explicitly warns against trusting "well-known" providers more; AutoFirm must NOT relax validation for big-name APIs. Reject any "trusted vendor" exception.
- Using this document as a source of *quantitative* gates — it is normative, not measured; numbers come from measured sources.

## CONCRETE BUILD IMPLICATION
- **Contract:** `IntegrationInbound{ source, raw_bytes, content_type }` → validator → `ValidatedPayload`. Anything that fails → fail-closed reject + append-only audit entry (ties to A6.2).
- **Test it drives:** fuzz the inbound validator at the external boundary (CLAUDE.md §5.5 "fuzz every external-input boundary"); property test: *no raw external byte ever reaches a tool-call parameter or DB write un-validated*.
- **Generality:** the rule is industry-agnostic — it applies identically whether the integrated API is a fintech ledger, a healthcare FHIR endpoint, or a retail catalog feed (B12 panel-safe).
