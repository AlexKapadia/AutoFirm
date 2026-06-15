# SUMMARY — Claude Code: Configure the sandboxed Bash tool

## Full citation
- **Title:** "Configure the sandboxed Bash tool"
- **Author/Org:** Anthropic (Claude Code documentation)
- **Year:** 2026 (live docs; fetched 2026-06-15)
- **Venue/Publisher:** Official Claude Code documentation
- **URL:** https://code.claude.com/docs/en/sandboxing

## Questions informed
- **L1.A5.3** Sandboxing of the substrate (PRIMARY).
- **L1.A5.1** Capability for autonomous unattended execution.

## GRADE tier
**High** (primary source of record for the substrate). OS mechanism claims corroborated against
the upstream projects (bubblewrap GitHub, macOS Seatbelt) and the standalone
`@anthropic-ai/sandbox-runtime` package; conceptual model corroborated by capability-security
literature (source 09).

## Key claims (exact, with locators)

1. **What it is/covers.** OS-level filesystem + network isolation for **the Bash tool and its
   child processes**. Runs on macOS, Linux, WSL2; **"Native Windows is not supported."** Built-in;
   enabled via `/sandbox` or `sandbox.enabled: true`.

2. **OS mechanisms (named).** **macOS: Seatbelt** (built-in, nothing to install).
   **Linux & WSL2: bubblewrap** (`bubblewrap` for fs isolation + `socat` for the network relay).
   "These OS-level restrictions ensure that all child processes spawned by Claude Code's commands
   inherit the same security boundaries." Optional seccomp filter adds Unix-domain-socket blocking
   (`@anthropic-ai/sandbox-runtime`). WSL1 unsupported (bubblewrap needs WSL2 kernel features).

3. **Default filesystem policy.** Write: cwd + subdirs + session temp (`$TMPDIR`). Read:
   **entire computer except denied dirs** — "this default still allows reading credential files
   such as `~/.aws/credentials` and `~/.ssh/`. Add them to `denyRead` to block them." Blocked:
   modifying files outside cwd/temp (incl. `~/.bashrc`, `/bin/`). Configurable:
   `sandbox.filesystem.{allowWrite,denyWrite,denyRead,allowRead}`.

4. **Default network policy.** "no domains are pre-allowed. The first time a command needs a new
   domain, Claude Code prompts." Pre-allow via `allowedDomains`; block via `deniedDomains`.
   Managed lockdown `allowManagedDomainsOnly` blocks non-allowed domains automatically (no prompt).

5. **Sandbox modes.** Auto-allow (sandboxed commands run without prompting; non-sandboxable
   commands fall back to permission flow) vs Regular permissions (all Bash goes through permission
   flow even when sandboxed). In both, the same fs/network restrictions apply. In auto-allow:
   explicit deny rules still respected; `rm`/`rmdir` of `/`/home/critical paths still prompt;
   content-scoped ask rules (`Bash(git push *)`) still prompt; a bare `Bash` ask rule is skipped
   for sandboxed commands. `autoAllowBashIfSandboxed: true` is the default.

6. **Escape hatch.** When a command fails due to sandbox restrictions, Claude may retry with the
   `dangerouslyDisableSandbox` parameter (runs OUTSIDE sandbox -> regular permission flow + your
   approval). Disable via `allowUnsandboxedCommands: false` ("Strict sandbox mode" — the param is
   "completely ignored").

7. **Fail-closed startup.** "By default, if the sandbox cannot start... Claude Code shows a
   warning and runs commands **without sandboxing**." Set `sandbox.failIfUnavailable: true` to
   make it a hard failure ("intended for managed deployments that require sandboxing as a security
   gate"). Recommended managed config:
   `{"sandbox":{"enabled":true,"failIfUnavailable":true,"allowUnsandboxedCommands":false}}`.

8. **Self-protection.** "the sandbox automatically denies write access to Claude Code's
   `settings.json` files at every scope and to the managed settings directory, so a sandboxed
   command cannot modify its own policy."

9. **Subagents & sandbox.** "subagents run in the same process as the parent session and use the
   same sandbox configuration. Bash commands inside a subagent are sandboxed when sandboxing is
   enabled in the parent session." Env scrub: `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB` strips
   Anthropic/cloud creds from subprocess env. Git worktrees: writes to the shared `.git` are
   allowed (so `git commit` works) but `.git/hooks/` and `.git/config` remain denied.

10. **Stated LIMITATIONS (security-critical).** "Sandboxing reduces risk but is not a complete
    isolation boundary." (a) The proxy "does not terminate or perform TLS inspection" — broad
    domains (e.g. `github.com`) enable data-exfil / domain-fronting; use a custom TLS-inspecting
    proxy if needed. (b) `allowUnixSockets` to `/var/run/docker.sock` "effectively grants access
    to the host system." (c) Overly broad `allowWrite` to `$PATH`/shell-rc dirs -> privilege
    escalation. (d) `enableWeakerNestedSandbox` "considerably weakens security." (e) Built-in file
    tools, computer use, and env vars are NOT covered by the sandbox.

## Reproducibility note
Re-fetch and verify: OS mechanism names (Seatbelt / bubblewrap / socat), "Native Windows is not
supported", the default-read-allows-credentials warning, `failIfUnavailable`, and the verbatim
"not a complete isolation boundary" sentence. All are direct quotes; the OS mechanism names are
independently verifiable at github.com/containers/bubblewrap and Apple Seatbelt docs.
