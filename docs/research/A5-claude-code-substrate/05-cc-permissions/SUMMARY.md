# SUMMARY — Claude Code: Configure permissions

## Full citation
- **Title:** "Configure permissions"
- **Author/Org:** Anthropic (Claude Code documentation)
- **Year:** 2026 (live docs; fetched 2026-06-15)
- **Venue/Publisher:** Official Claude Code documentation
- **URL:** https://code.claude.com/docs/en/permissions

## Questions informed
- **L1.A5.3** Tool/permission model & sandboxing (PRIMARY — this is the core of the question).
- **L1.A5.1** Permission modes available in CLI/headless.

## GRADE tier
**High** (primary source of record for the substrate's permission model). Corroborated by the
sandboxing page (source 06) and settings page (source 04, precedence).

## Key claims (exact, with locators)

1. **Tiered model.** Read-only tools: no approval. Bash: approval required ("Yes, don't ask
   again" = permanently per project directory + command). File modification (Edit/Write):
   approval required ("Yes, don't ask again" = until session end).

2. **Allow/Ask/Deny precedence (LOAD-BEARING).** "Rules are evaluated in order: **deny, then ask,
   then allow.** The first match in that order determines the outcome, and **rule specificity does
   not change the order.** A matching ask rule prompts even when a more specific allow rule also
   matches." Bare tool name in `deny` (e.g. `Bash`) "removes the tool from Claude's context
   entirely, so Claude never sees it"; scoped (`Bash(rm *)`) leaves the tool but blocks matches.

3. **Enforced by Claude Code, not the model.** "Permission rules are enforced by Claude Code, not
   by the model. Instructions in your prompt or `CLAUDE.md`... don't change what Claude Code
   allows." (This is the deterministic enforcement boundary — prompt injection cannot grant
   authority it doesn't have.)

4. **Permission modes.** `default`; `acceptEdits` (auto-accept edits + `mkdir`/`touch`/`mv`/`cp`
   in cwd/`additionalDirectories`); `plan` (read-only exploration, no source edits);
   `auto` (auto-approves with background safety-check classifier — research preview);
   `dontAsk` (auto-deny unless pre-approved via `permissions.allow`); `bypassPermissions` (skips
   prompts EXCEPT explicit `ask` rules and `rm -rf /`/`rm -rf ~` circuit-breaker; also skips
   protection of `.git`/`.claude`/etc.). `permissions.disableBypassPermissionsMode` and
   `disableAutoMode` set to `"disable"` block those modes (best in managed settings).

5. **Rule syntax.** `Tool` or `Tool(specifier)`. `Bash(*)` ≡ `Bash`. Glob `*` at any position;
   `Bash(ls *)` enforces a word boundary (matches `ls -la` not `lsof`); `:*` suffix ≡ trailing
   ` *`. Claude Code is shell-operator-aware: `Bash(safe-cmd *)` does NOT permit
   `safe-cmd && other-cmd`; separators `&& || ; | |& & newline` each matched independently.
   Process wrappers stripped before matching: `timeout time nice nohup stdbuf` (+ bare `xargs`).
   NOT stripped (so they can smuggle commands): `direnv exec`, `devbox run`, `mise exec`, `npx`,
   `docker exec`; `watch setsid ionice flock` and `find -exec/-delete` always prompt.

6. **Read-only command set** (no prompt in every mode, not configurable): `ls cat echo pwd head
   tail grep find wc which diff stat du cd` + read-only `git` forms.

7. **Read/Edit path rules follow gitignore semantics with anchors:** `//path` absolute,
   `~/path` home, `/path` project-root-relative, `path`/`./path` cwd-relative. Windows paths
   normalized to POSIX (`C:\Users` -> `/c/Users`). **CAVEAT:** Read/Edit deny rules apply to
   built-in file tools + recognized Bash file commands (`cat`/`head`/`tail`/`sed`) "They do not
   apply to arbitrary subprocesses that read or write files indirectly, like a Python or Node
   script... For OS-level enforcement that blocks all processes from accessing a path, enable the
   sandbox." Symlinks: allow rules require both symlink+target match; deny rules block if either
   matches.

8. **`Agent(AgentName)` rules** control which subagents Claude may use (deny `Agent(Explore)`,
   etc.). `Cd(...)` rules gate `/cd`.

9. **Hooks vs rules.** "Hook decisions do not bypass permission rules. Deny and ask rules are
   evaluated regardless of what a PreToolUse hook returns." But "A hook that exits with code 2
   stops the tool call before permission rules are evaluated." (Deny-first precedence preserved.)

10. **Precedence across scopes.** Managed (1, cannot be overridden incl. by CLI) > CLI args (2) >
    Local (3) > Project (4) > User (5). "If a tool is denied at any level, no other level can
    allow it"; "a user-level deny blocks a project-level allow." SDK `managedSettings` with
    `parentSettingsBehavior: "merge"` can tighten but not loosen.

## Reproducibility note
Re-fetch and verify the verbatim "deny, then ask, then allow" sentence, the
"enforced by Claude Code, not by the model" sentence, the process-wrapper strip list, and the
"do not apply to arbitrary subprocesses... enable the sandbox" caveat. These four are the
safety-critical claims; all are direct quotes from this single authoritative spec and are
mutually corroborated by source 06 (sandbox) for the subprocess-escape point.
