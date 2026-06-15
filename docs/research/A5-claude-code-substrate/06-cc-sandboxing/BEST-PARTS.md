# BEST-PARTS — Sandboxing for AutoFirm

## ADOPT

- **OS-level sandbox (Seatbelt/bubblewrap) as the second, model-independent enforcement layer for
  every Bash-capable agent.** Critical because permission Read/Edit rules do NOT cover arbitrary
  subprocesses (source 05, claim 7) — the sandbox does, at the OS level, "regardless of what the
  model chose to run." This closes the prompt-injection-to-subprocess-escape gap and is the
  substrate realization of CLAUDE.md §5.6 "treat all external input as untrusted."
- **Managed fail-closed sandbox profile (verbatim adopt):**
  `{"sandbox":{"enabled":true,"failIfUnavailable":true,"allowUnsandboxedCommands":false}}`
  plus `denyRead: ["~/.aws","~/.ssh","~/.config","~/.kube"]` (the default read policy exposes
  credentials — claim 3), `allowedDomains` = explicit per-tenant allowlist, and
  `allowManagedDomainsOnly: true`. This makes sandboxing a hard security GATE, not best-effort.
- **`CLAUDE_CODE_SUBPROCESS_ENV_SCRUB`** to strip cloud/Anthropic creds from subprocess env
  (claim 9) — secrets-handling (CLAUDE.md §5.6, A8.3).
- **Self-protection (claim 8)** — sandbox denies writes to its own `settings.json`/managed dir;
  adopt as a guarantee that a compromised agent cannot rewrite its policy (tamper-evidence, A6).
- **Per-tenant network egress via `allowedDomains` + WebFetch domain rules** as the data-layer
  isolation boundary for outbound traffic (A8.2 multi-tenant isolation).

## REJECT / CRITICAL CAVEATS (drives the L3 architecture, A7 veto)

- **DO NOT rely on the built-in sandbox as the SOLE isolation for untrusted/multi-tenant
  workloads.** The doc states plainly it is "not a complete isolation boundary" (claim 10):
  no TLS inspection (domain fronting/exfil via broad domains), Unix-socket escalation, weaker
  nested mode. **Resolution (L3.PLATFORM):** wrap the whole Claude Code process in a stronger
  outer boundary — a **dev container / VM / `@anthropic-ai/sandbox-runtime`** per tenant — and use
  the built-in Bash sandbox as the inner defense-in-depth layer. Multi-tenant isolation must be
  enforced at the infrastructure layer, "not by convention" (CLAUDE.md tenancy note).
- **DO NOT allow broad domains (e.g. bare `github.com`) for sensitive tenants** — explicit
  exfil/domain-fronting risk; allowlist the narrowest hostnames, or run a TLS-inspecting custom
  proxy (`httpProxyPort`/`socksProxyPort`).
- **DO NOT use `enableWeakerNestedSandbox`/`enableWeakerNetworkIsolation` unless the outer
  container already provides isolation** — flagged as considerably weaker.
- **DO NOT assume Windows hosts are sandboxed.** "Native Windows is not supported" — AutoFirm must
  run agents inside WSL2/Linux/macOS or a Linux container. (Relevant: this very research host is
  Windows; production agents must not run un-sandboxed Bash on native Windows.)
- **DO NOT grant `allowUnixSockets` to `docker.sock`** — host takeover.

## Concrete build implications
- Component: every tenant agent runs in a Linux container/VM (outer boundary) running
  `claude` with the managed fail-closed sandbox profile (inner boundary). Two layers, mandatory.
- Contract: a host-capability check at launch refuses to run Bash-capable agents where the
  sandbox is unavailable (`failIfUnavailable`).
- Test: (a) red-team exfil test — sandboxed agent attempts egress to a non-allowlisted host and is
  blocked; (b) subprocess credential-read test — confirm `~/.ssh` is denied; (c) policy-tamper
  test — sandboxed command attempts to write its own `settings.json` and is denied.
