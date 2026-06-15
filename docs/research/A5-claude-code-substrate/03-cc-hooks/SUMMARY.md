# SUMMARY — Claude Code: Hooks reference

## Full citation
- **Title:** "Hooks reference" / "Automate actions with hooks"
- **Author/Org:** Anthropic (Claude Code documentation)
- **Year:** 2026 (live docs; fetched 2026-06-15)
- **Venue/Publisher:** Official Claude Code documentation
- **URL:** https://code.claude.com/docs/en/hooks (guide: https://code.claude.com/docs/en/hooks-guide)

## Questions informed
- **L1.A5.1** Hooks capability (lifecycle automation, deterministic enforcement).
- **L1.A5.3** Tool/permission enforcement via PreToolUse hooks (fail-closed gating).

## GRADE tier
**High** (primary source of record for the substrate). Hook decision semantics corroborated on
the permissions page (source 05: "A hook that exits with code 2 stops the tool call before
permission rules are evaluated").

## Key claims (exact, with locators)

1. **Hook events & blockability.** `SessionStart` (no block); `Setup`; `UserPromptSubmit`
   (block via exit 2); `PreToolUse` (block via `permissionDecision`); `PostToolUse` (no block);
   `PostToolUseFailure`; `PermissionRequest` (can decide allow/deny); `PermissionDenied`
   (no block, can `retry: true`); `Stop` (block via exit 2 prevents stopping);
   `SubagentStart`/`SubagentStop`; `SessionEnd`; plus `PreCompact`/`ConfigChange`.

2. **Exit-code semantics (load-bearing).** **Exit 0** = success; JSON on stdout is processed.
   **Exit 2** = blocking error; stderr is fed to Claude, stdout/JSON ignored; effect by event:
   `PreToolUse` blocks the tool call; `UserPromptSubmit` rejects the prompt; `PermissionRequest`
   denies; `Stop`/`SubagentStop` prevents stopping; `PreCompact` blocks compaction. **Other exit
   codes** = non-blocking error (stderr shown as notice; execution continues).

3. **PreToolUse decision JSON.** `hookSpecificOutput.permissionDecision` ∈ {`"deny"` (blocks),
   `"allow"` (permits), `"ask"` (escalates to user), `"defer"` (normal flow)}, with
   `permissionDecisionReason`; may return `updatedInput` to modify tool args before execution.

4. **Common input (stdin JSON) to every hook:** `session_id`, `transcript_path`, `cwd`,
   `permission_mode`, `hook_event_name`, `effort.level`. Inside subagents adds `agent_id`,
   `agent_type` (= the subagent `name`).

5. **Handler types (5):** `command` (shell; JSON on stdin, JSON/exit-code out), `http` (POST JSON
   body; 2xx JSON for decisions), `mcp_tool` (calls a tool on a connected MCP server),
   `prompt` (single-turn Claude eval), `agent` (spawns a subagent to verify — experimental).

6. **Matchers.** Tool events match `tool_name`: `"Bash"`, `"Edit|Write"`, regex like
   `mcp__memory__.*`, `mcp__.*__write.*`. The `if` field narrows with permission-rule syntax
   (`Bash(rm *)`, `Edit(*.ts)`); "Filter is best-effort; fails open to allow execution if pattern
   can't be parsed."

7. **FAIL-OPEN DEFAULT (critical).** "Hooks are **fail-open by default**: if a hook times out,
   crashes, or returns invalid JSON, **execution continues**. To enforce a policy: use exit code
   2 in command hooks to block actions; return JSON with a blocking decision (exit 0) for explicit
   control; **use the permission system for hard allow/deny rules (not hooks).** Hooks are best
   for validation, logging, transformation, and context injection — not for replacing the
   permission system." HTTP hooks "Cannot signal blocking error through status alone" — must
   return 2xx with JSON `decision: "block"` / `permissionDecision: "deny"`.

8. **`additionalContext` injection** (inside `hookSpecificOutput`) injects context at the hook
   point; capped at 10,000 characters (excess saved to file with preview).

9. **Hot-reload.** Per settings page (source 04): edits to `hooks` apply to a running session
   without restart.

10. **Managed lockdown.** `allowManagedHooksOnly: true` (managed settings) loads only managed/SDK
    hooks and hooks from force-enabled plugins; user/project/other-plugin hooks are blocked
    (source 05).

## Reproducibility note
Re-fetch and verify the event table, the exit-0/exit-2 semantics, the `permissionDecision` enum,
and the verbatim "fail-open by default" sentence. The fail-open default is the single most
load-bearing claim for AutoFirm's fail-closed design and is corroborated cross-page.
