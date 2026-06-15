# BEST-PARTS — Permissions for AutoFirm

## ADOPT

- **The permission system (NOT hooks) is AutoFirm's hard authority boundary.** "Permission rules
  are enforced by Claude Code, not by the model" (claim 3) — prompt injection cannot grant
  authority the model doesn't have. This is the substrate primitive that makes least-privilege
  (CLAUDE.md §5.6, L1.A7.3) real and deterministic. Build implication: every agent role's
  capability set is a managed `permissions.{allow,deny}` profile, deny-first.
- **Deny-first precedence + managed-scope deny** (claims 2, 10) as the fail-closed core: a managed
  `deny` cannot be overridden by any project/user/CLI `allow`. AutoFirm's never-do list (e.g.
  `Read(./.env*)`, `Read(**/secrets/**)`, `Bash(curl *)`, `WebFetch(domain:*)` except an
  allowlist, `Bash(git push *)` outside approved branches) lives in managed deny.
- **`dontAsk` as the default mode for unattended autonomous agents** (claim 4): auto-deny anything
  not explicitly allowed — fail-closed by construction.
- **`Agent(...)` deny/allow rules to enforce the org's span-of-control** (claim 8): which roles
  may delegate to which (pairs with subagent `Agent(type)` allowlists, source 02).
- **gitignore-anchored Read/Edit rules for multi-tenant file isolation** (claim 7): scope each
  tenant's agents to `/<tenant>/**` and deny cross-tenant paths. Use `//` for true absolute paths
  (the doc warns `/Users/...` is project-relative, NOT absolute — a real footgun).
- **`disableBypassPermissionsMode`/`disableAutoMode` = "disable" in managed settings** to remove
  the dangerous modes entirely for production agents.

## REJECT / CRITICAL CAVEATS (A7 veto applies)

- **DO NOT treat permission rules as a complete sandbox.** The doc is explicit: Read/Edit deny
  rules "do not apply to arbitrary subprocesses... like a Python or Node script that opens files
  itself" (claim 7). A permission-only boundary is bypassable by any Bash-spawned program.
  **Resolution:** combine permission rules WITH OS-level sandbox (source 06) for any agent that
  can run Bash — defense in depth, both required (CLAUDE.md §5.6).
- **DO NOT write argument-constraining Bash allow rules and trust them** (the doc's own warning):
  `Bash(curl http://github.com/ *)` is trivially bypassed (options-before-URL, https, redirects,
  `URL=...; curl $URL`, extra spaces). **Resolution:** deny the network Bash tools (`curl`/`wget`)
  and route allowed egress through WebFetch domain rules + sandbox `allowedDomains`.
- **DO NOT allowlist environment runners loosely.** `Bash(devbox run *)` matches
  `devbox run rm -rf .`; `npx`/`docker exec` are NOT wrapper-stripped and execute arbitrary inner
  commands. **Resolution:** write exact-match rules per inner command.
- **DO NOT use `bypassPermissions` outside a container/VM** — it skips `.git`/`.claude` write
  protection. Disable it via managed settings for AutoFirm agents.

## Concrete build implications
- Component: per-role `permissions` profile (managed) + per-tenant path-isolation deny set.
- Contract: hard controls are deny rules in managed scope; sandbox mirrors them at OS level.
- Test: (a) deny-precedence test — project allow + managed deny -> blocked; (b) subprocess-escape
  test — a Bash-spawned python script tries to read a Read-denied path and is blocked ONLY when
  sandbox is enabled (proves permission rules alone are insufficient); (c) wrapper/operator tests
  for `devbox run rm`, `safe && evil`, `curl $URL`.
