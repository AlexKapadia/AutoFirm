# ADR-003 — Single Model-Egress Gateway & the Provider-Abstraction Boundary (Gate-1)

> **Status: ACCEPTED (binding, Gate-1 ratification).** Decided by the CTO, grounded in the ratified
> `evolution-plan.md` (Part A — the reconciling architecture), the Gate-1 verification of Claude Code's
> gateway-env honouring (`gate1-decisions.md` item 1), and the B1 multi-model-egress + B5 exact-cost
> research digests. Determinism and fail-closed security are defaults (CLAUDE.md §3.2, §5.6). Consistent
> with ADR-001 (Python stack, mutation gate), ADR-002 (public/private boundary), and the Gate-2
> `data-contracts.md` / `threat-model.md`. Supersedes nothing; introduces the new `modelgateway/` package.

---

## Context

AutoFirm's execution substrate is the **`claude` CLI in its bare headless JSON form** (`substrate.md` §1;
ADR-001 §1). Today the platform has **no provider abstraction**: an agent is a CLI session, and the only
model that session can reach is whatever the CLI is configured to call. The user requirement is broader —
**"any model, many models per use-case, hundreds of models, exact cross-model cost"** (`evolution-plan.md`
goals W1/W5). That pulls in two directions at once:

1. **CLI-substrate fidelity.** The CLI gives full-fidelity Claude behaviour — tool-use, extended thinking,
   prompt-caching, `--bare` ambient-config stripping, the JSON envelope (`session_id`, `total_cost_usd`).
   This fidelity is the substrate AutoFirm's orchestration, audit, and resume machinery is built on.
2. **Provider breadth.** "Any/many models" means GPT, Gemini, Llama, local/self-hosted, and Claude
   variants — selected *per use-case*, sometimes *several per use-case* (ensemble/quorum). The CLI alone
   cannot deliver that breadth without losing (1).

There is no single audited boundary through which model traffic flows today, which is also a security gap:
the Gate-2 threat model has a generic API-gateway PEP (C5) but **no model-egress chokepoint** and **no
cost-data-integrity component** (`threat-model.md`; the B6 STRIDE deltas flagged both as missed surfaces).

### The linchpin verification (Gate-1 item 1)

The keystone of the whole reconciliation is whether the CLI can be **pointed at a gateway**. Verified live:
Claude Code **honours `ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN`, and `CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY`**
(gateway model discovery, v2.1.129+), so a `claude -p --bare --model <name>` run egresses through a local
OpenAI-compatible proxy using the injected base-URL/token and selects a non-default model. **However**, routing
the CLI to **non-Anthropic** models through that channel is **uncertified**: tool-use, extended-thinking,
prompt-caching, and `--bare` fidelity **degrade or break** when the bytes on the wire are not an Anthropic-family
model behind an Anthropic-shaped API. The env-honouring holds; full-fidelity *cross-provider* CLI routing does not.

This is the fork the architecture must resolve without either (a) giving up CLI fidelity or (b) giving up
provider breadth.

---

## Decision

**Introduce a single, self-hosted, OpenAI-compatible model-egress gateway as the one audited boundary for all
model traffic, and split egress by capability so each path keeps full fidelity:**

1. **New `src/autofirm/modelgateway/` package** is the provider-abstraction boundary (`evolution-plan.md` §A.2,
   §A.4). It lands first and is **provider-agnostic**: the request/response/selector contracts
   (`model_invocation_contract.py`, ratified in `data-contracts.md`) name a *selection policy*, never a
   hard-coded model string. The single impure seam is `model_egress_client_protocol.py` (a `ModelGatewayClient`
   Protocol + a deterministic `FakeModelGatewayClient` double); the only file touching HTTP is
   `openai_compatible_gateway_client.py`.

2. **CLI-substrate agents → gateway → ANTHROPIC-FAMILY models ONLY.** The CLI is pointed at the gateway via the
   injected `ANTHROPIC_BASE_URL` / `ANTHROPIC_AUTH_TOKEN` / discovery env map
   (`cli_gateway_env_injection.py`). Because only Anthropic-family models traverse this path, **full fidelity is
   preserved** (tool-use, extended thinking, prompt-caching, `--bare`). Per-use-case selection still happens —
   but **across Claude variants** (e.g. a cheaper Haiku for triage, Opus for hard reasoning), never across
   providers on the CLI path.

3. **PROGRAMMATIC / non-CLI agents → gateway → ANY provider.** Code paths that call the gateway directly through
   `ModelGatewayClient` (not via a CLI session) may target **any provider** — GPT, Gemini, Llama, local — under
   the same OpenAI-compatible API and the same `ModelSelector` policy (pinned / preferred-with-failover /
   ensemble-quorum). **This is where "any model / hundreds of models / many-per-use-case" lives.** These calls do
   not need CLI-only features, so the uncertified-fidelity risk does not apply.

The gateway is therefore **one boundary, two fidelity-preserving lanes**: a Claude-only lane for the CLI substrate
and an any-provider lane for programmatic callers. Both lanes carry the same audit, cost-record, virtual-key, and
kill-switch invariants.

---

## Consequences

- **One audited egress chokepoint.** Every model call — CLI-lane or programmatic — flows through the gateway,
  which writes a hash-chained `UsageCostRecord` + audit record on the fail-closed path (no dropped-record
  repudiation; mirrors C3/T2). This is what makes W5 exact cross-model cost tracking possible at all.
- **Provider breadth without CLI-fidelity loss.** The CLI keeps Anthropic-only full fidelity; breadth is served
  programmatically. The uncertified cross-provider-CLI path is **never taken** — it is not a configuration the
  platform exposes.
- **Single-egress availability becomes a first-class threat (new C5′).** Concentrating egress creates a SPOF.
  Mitigated by **degraded-mode by capability** (item 2 of `gate1-decisions.md`): the CLI lane **fails static** to
  direct-to-Anthropic with a loud audited `egress.downgrade` event; the programmatic any-provider lane **fails
  that capability closed** — never a whole-platform halt. Gateway runs as an OTP-style supervised, auto-restarting
  local process whose restart-intensity cap escalates to the kill-switch rather than crash-looping.
- **New cost-data-integrity component (C9).** Cost is a deterministic pure function of provider-attested usage ×
  a versioned price snapshot, hash-chained and reconciled — the spender is never the scorekeeper.
- **Multi-provider secrets (C4′).** Per-provider, per-session, short-TTL, sender-constrained virtual keys minted
  by the existing `CredentialBroker`; **no god-key spanning providers**.
- **No graveyard.** `role_capability_index.py` and the operate-platform checks are *re-pointed* to the new
  registry; no parallel old/new model-calling path is left behind.

## Alternatives considered

- **A managed router (OpenRouter / Vercel AI Gateway / Portkey).** All three deliver "any model" breadth and
  unified billing, and were genuinely competitive on the breadth axis. **Rejected as the audited boundary** for
  three institution-grade reasons: (a) **egress trust** — a third-party router becomes an un-auditable hop that
  sees every prompt/response on the one channel everything funnels through, violating the single-self-hosted-PEP
  posture (A8.1) and the "untrusted-by-default external response" rule; (b) **cost ground truth** — billing is
  the router's aggregate, not a per-call provider-attested meter we can hash-chain and reconcile (C9 needs the
  provider's own usage figure, not a reseller's); (c) **fail-closed control** — we cannot guarantee a managed
  router's degraded-mode is fail-static-to-Anthropic for the CLI lane. A managed router may still be used
  *behind* our gateway for specific programmatic providers, but it is never the boundary of record.
- **Route the CLI itself to any provider via `ANTHROPIC_BASE_URL`.** Tempting (one path for everything), but the
  Gate-1 verification showed cross-provider CLI fidelity is uncertified (tool-use / extended-thinking /
  prompt-caching / `--bare` degrade). **Rejected** — it trades the substrate's full fidelity for breadth the
  programmatic lane already provides safely.
- **No gateway — each call site talks to each provider directly.** **Rejected** — no audited chokepoint, no
  single place to enforce cost-record/kill-switch/virtual-key, and N provider integrations scattered across the
  codebase. The whole point is one boundary.

**Status: ACCEPTED.**
