# AutoFirm Threat Model (STRIDE) — living document

> **Status: stub.** This is initialised at Gate 0 and filled at Gate 2 (Architecture), then updated whenever
> the design changes (`CLAUDE.md` §5.6). AutoFirm is a security-critical system: it runs autonomous agents
> that can spend money, send outreach, touch real services, and operate unattended. Security controls are
> defaults, never afterthoughts, and the system **fails closed**.

## Why this matters here (more than usual)

AutoFirm orchestrates long-running, self-relaunching agents with real-world side effects. The blast radius of
a compromised or runaway agent is large. Therefore, from day one the design must assume: untrusted document
input, prompt-injection at every boundary, secret leakage risk, and the need for a global kill-switch and
spend/rate limits.

## STRIDE (to be completed at Gate 2, per architecture)

| Category | Concern | Control (to be specified) |
|----------|---------|----------------------------|
| **S**poofing | Agent/role impersonation across the message bus | Authenticated, scoped identities per agent |
| **T**ampering | Audit log / state / role-spec tampering | Append-only audit log; integrity checks |
| **R**epudiation | "Which agent decided this?" | Full decision provenance & traceability |
| **I**nformation disclosure | Secret/PII leakage in logs or to agents | Secrets via secret manager only; least privilege; no secrets in logs |
| **D**enial of service | Runaway loops / spend / API exhaustion | Spend & rate limits; loop backstops; kill-switch |
| **E**levation of privilege | A worker gaining orchestrator powers | Strict capability scoping; no shared god-keys |

## Standing invariants (binding now)

- **Fail closed** — missing/ambiguous permission, key, or check → refuse the action.
- **Global kill-switch** — a single config flag halts all external calls.
- **Synthetic-only-for-sensitive** — never real PII/client/deal data in tests or validation; public corporate
  data is allowed and clearly labelled.
- **Append-only audit log** of every sensitive action and external call: what, when, who.
