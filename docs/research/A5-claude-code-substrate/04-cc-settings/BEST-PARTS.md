# BEST-PARTS — Settings for AutoFirm

## ADOPT

- **Managed settings = AutoFirm's non-overridable governance control plane.** The precedence
  rule "Managed... can't be overridden by anything" and "if a tool is denied at any level, no
  other level can allow it" (claims 1, 7) is precisely the substrate hook AutoFirm needs to make
  its security/compliance baseline (CLAUDE.md §5.6, A6/A7) **structurally** un-removable by any
  tenant/project/agent. Build implication: AutoFirm deploys its kill-switch, deny rules, sandbox
  enforcement, and `allowManaged*Only` locks via the managed `managed-settings.json` +
  `managed-settings.d/*.json` drop-ins; agents and clients get only User/Project/Local scope,
  which managed always wins over.
- **`allowManagedHooksOnly`, `allowManagedMcpServersOnly`, `allowManagedPermissionRulesOnly`,
  `strictPluginOnlyCustomization`** as the lockdown set (claim 7): prevents prompt-injected or
  client-supplied config from introducing hooks/MCP servers/permission rules that weaken
  governance. Adopt as the default managed profile for any agent that touches tenant data.
- **`forceRemoteSettingsRefresh: true` for fail-closed startup** — refuses to start until managed
  policy is freshly fetched. Maps directly to CLAUDE.md §5.6 fail-closed + the kill-switch.
- **`requiredMinimumVersion`** to pin the substrate version (reproducibility/audit) and
  `availableModels` to constrain which models a tenant's agents may use (cost + compliance).
- **`cleanupPeriodDays` + `CLAUDE_CONFIG_DIR`** to control transcript retention/location for the
  audit/provenance layer (A6); set explicitly rather than relying on the 30-day default.
- **Hot-reload of `permissions`/`hooks`** (claim 6) enables a **live kill-switch**: flipping a
  managed deny rule halts new tool calls without restarting running sessions.

## REJECT / caution

- **Do NOT rely on Local/Project/User settings for any security control** — they are
  agent/tenant-mutable and lower-precedence. Security lives ONLY in managed scope.
- **Do NOT assume `model`/`outputStyle` changes take effect live** — they are read once at
  startup (claim 6); a model swap requires a fresh session.
- **Do NOT put secrets in `env` within shared (`project`) settings** — git-shared; use a secret
  manager / `apiKeyHelper` (CLAUDE.md §5.6 secrets-via-manager).

## Concrete build implications
- Component: `managed-policy` profile (a `managed-settings.json` + `.d/` drop-ins) deployed per
  AutoFirm host/tenant, carrying deny rules, sandbox locks, `allowManaged*Only`, kill-switch,
  `requiredMinimumVersion`, `forceRemoteSettingsRefresh`.
- Contract: precedence test — a project `allow` for a managed-denied tool MUST NOT grant access.
- Test: integration test that injects a malicious project hook + project `allow` rule and asserts
  managed deny + `allowManagedHooksOnly` neutralize both (fail-closed proof).
