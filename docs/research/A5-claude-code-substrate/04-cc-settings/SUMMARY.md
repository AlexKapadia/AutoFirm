# SUMMARY — Claude Code: Settings

## Full citation
- **Title:** "Claude Code settings"
- **Author/Org:** Anthropic (Claude Code documentation)
- **Year:** 2026 (live docs; fetched 2026-06-15)
- **Venue/Publisher:** Official Claude Code documentation
- **URL:** https://code.claude.com/docs/en/settings

## Questions informed
- **L1.A5.1** Settings system & configuration surface.
- **L1.A5.3** Settings precedence as a control plane (managed > everything).

## GRADE tier
**High** (primary source of record). Precedence corroborated verbatim on the permissions page
(source 05, "Settings precedence" section).

## Key claims (exact, with locators)

1. **Precedence (highest→lowest):** (1) **Managed** — "can't be overridden by anything";
   (2) **Command line arguments** — temporary session overrides; (3) **Local**
   (`.claude/settings.local.json`, gitignored) — overrides project and user; (4) **Project**
   (`.claude/settings.json`, git-shared) — overrides user; (5) **User**
   (`~/.claude/settings.json`) — lowest.

2. **Storage locations.** Managed: server-managed / plist (macOS) / registry (Windows) / system
   `managed-settings.json` (file paths: macOS `/Library/Application Support/ClaudeCode/`, Linux
   `/etc/claude-code/`, Windows `C:\Program Files\ClaudeCode\`). User `~/.claude/settings.json`;
   Project `.claude/settings.json`; Local `.claude/settings.local.json`.

3. **Managed drop-in merge.** File-based managed settings support `managed-settings.json` (base)
   + `managed-settings.d/*.json` merged alphabetically (numeric prefixes like `10-telemetry.json`).

4. **`permissions` block.** Arrays `allow` / `deny` / `ask`; rule syntax `ToolName(pattern)`;
   wildcards `*`/`**`. (Full semantics in source 05.) Plus `defaultMode` and
   `additionalDirectories`.

5. **Key settings fields (selected):** `model`, `availableModels` (restrict model selection),
   `env`, `permissions`, `hooks`, `autoMemoryEnabled`, `outputStyle`, `claudeMd`
   (org-wide memory), `forceLoginOrgUUID`, `requiredMinimumVersion`, `cleanupPeriodDays`,
   `includeGitInstructions`, `disableRemoteControl`.

6. **Hot-reload.** "Claude Code watches your settings files and reloads them when they change, so
   edits to most keys apply to the running session without a restart. This includes
   `permissions`, `hooks`, and credential helpers like `apiKeyHelper`." Read once at startup:
   `model`, `outputStyle`.

7. **Managed-only policy keys** (read only from managed settings; see source 05 for the full
   table): incl. `allowManagedHooksOnly`, `allowManagedMcpServersOnly`,
   `allowManagedPermissionRulesOnly`, `strictPluginOnlyCustomization`, `forceRemoteSettingsRefresh`
   (fail-closed startup), `sandbox.*` managed locks. "If a tool is denied at any level, no other
   level can allow it" — managed deny cannot be overridden by `--allowedTools`.

## Reproducibility note
Re-fetch and verify the 5-level precedence list and the hot-reload sentence (verbatim). The
"managed deny cannot be overridden by CLI args" rule is the load-bearing governance invariant and
appears identically on the permissions page.
