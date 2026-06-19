# W1 — Gateway Default & Configuration (no throwaway branch — research settled it)

> Companion note to **ADR-003** (the binding CLI-vs-programmatic egress split) and the
> **B1** research library (`docs/research/B1-multi-model-egress/`). This records the
> *recommended gateway implementation* and how it is configured. Per CLAUDE.md §3.4 a
> bake-off branch is only run where the choice is genuinely open; here the B1 research
> already settled it, so this is documented rather than re-litigated on a branch.

## Recommended egress: self-hosted LiteLLM (OpenAI-compatible)

The recommended model-egress gateway is a **self-hosted LiteLLM proxy** —
OpenAI-compatible, with per-session **virtual keys**, built-in **failover**, and an
**open per-token price map** (`docs/research/B1-multi-model-egress/litellm-proxy-gateway`).
It is the *boundary of record* (ADR-003): self-hosted so every prompt/response stays
inside our trust boundary, and its catalog price map lets the cost ledger compute
`price_map_computed` costs deterministically.

**OpenRouter** is used only as a `provider_reported` **cost source** where a hosted
surface returns an authoritative `usage.cost`
(`docs/research/B1-multi-model-egress/openrouter-gateway`) — never as the audited
boundary (ADR-003 "Alternatives considered" rejects a third-party router as the PEP).

## The code here is provider-agnostic

`src/autofirm/modelgateway/openai_compatible_gateway_client.py` targets the
**OpenAI-compatible** chat-completions surface and is agnostic to *which* gateway
serves it (LiteLLM, or any OpenAI-compatible proxy). Swapping the gateway is a config
change (the base URL), not a code change — there is no LiteLLM/OpenRouter-specific code
in the runtime path.

## Configuration — env / secret-manager only (no secrets in repo)

| Setting | Source | Notes |
|---------|--------|-------|
| Gateway base URL | env / secret-manager | Non-secret; injected into the CLI child env as `ANTHROPIC_BASE_URL` and passed to `OpenAiCompatibleGatewayClient(gateway_base_url=...)`. Never a literal in code. |
| Per-session virtual key | `CredentialBroker` → resolver, **point-of-use** | The SECRET. Resolved per call/session and injected as `ANTHROPIC_AUTH_TOKEN` (CLI lane) or the `Authorization: Bearer` header (programmatic lane). Never stored, logged, or placed on argv/URL. |
| Gateway model discovery | constant | `CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY=1` (CLI lane, Gate-1 verified). |

No gateway URL, key, or provider secret is ever committed to the repo — the secret
scan (`make secretscan`) and the env-only secret source enforce this fail-closed.

## The two fidelity-preserving lanes (ADR-003, binding)

- **CLI-substrate lane → Anthropic-family models ONLY.** Enforced in
  `cli_gateway_env_injection.build_cli_gateway_env` and `LaunchSpec.model` validation:
  a non-Anthropic model on the CLI lane is **refused fail-closed**
  (`NonAnthropicModelRefused`). Per-use-case selection still happens — across Claude
  variants (e.g. Haiku triage vs Opus reasoning).
- **Programmatic lane → ANY provider.** Code calling `ModelGatewayClient` directly
  (`OpenAiCompatibleGatewayClient`) may target any provider under the same
  `ModelSelector` policy (pinned / preferred-with-failover / ensemble-quorum). This is
  where "any model / hundreds of models / many-per-use-case" lives.
