# SUMMARY — Claude Code: Create custom subagents

## Full citation
- **Title:** "Create custom subagents"
- **Author/Org:** Anthropic (Claude Code documentation)
- **Year:** 2026 (live docs; fetched 2026-06-15)
- **Venue/Publisher:** Official Claude Code documentation
- **URL:** https://code.claude.com/docs/en/sub-agents

## Questions informed
- **L1.A5.1** Subagents capability/limits (the core orchestration substrate primitive).
- **L1.A5.3** Per-subagent tool/permission/MCP scoping.

## GRADE tier
**High** (primary source of record for the substrate; same up-rate rationale as source 01).
Corroborated by the permissions page (source 05, `Agent(...)` rules) and sandboxing page
(source 06, "subagents run in the same process as the parent session").

## Key claims (exact, with locators)

1. **Isolated context.** "Each subagent runs in its own context window with a custom system
   prompt, specific tool access, and independent permissions... works independently and returns
   results." Non-fork subagent initial context = its own system prompt + a delegation/task
   message + CLAUDE.md/memory hierarchy + a git-status snapshot + preloaded skills. "It does not
   see your conversation history, the skills you've already invoked, or the files Claude has
   already read." (Explore/Plan skip CLAUDE.md and git status.)

2. **Definition format.** Markdown files with YAML frontmatter; body = system prompt. Required
   fields: `name`, `description`. Optional: `tools`, `disallowedTools`, `model`, `permissionMode`,
   `maxTurns`, `skills`, `mcpServers`, `hooks`, `memory`, `background`, `effort`, `isolation`,
   `color`, `initialPrompt`.

3. **Scopes & precedence (highest→lowest):** Managed settings (1) > `--agents` CLI flag
   (2, session-only, not saved to disk) > `.claude/agents/` project (3) > `~/.claude/agents/`
   user (4) > plugin `agents/` (5). "When multiple subagents share the same name, the
   higher-priority location wins." Identity comes only from the `name` field. **Plugin subagents
   do NOT support `hooks`, `mcpServers`, or `permissionMode` (ignored for security reasons).**

4. **Tool scoping.** Inherit all main-conversation tools + MCP tools by default. `tools`
   (allowlist) or `disallowedTools` (denylist); if both set, "`disallowedTools` is applied first,
   then `tools` is resolved against the remaining pool." Unavailable to subagents regardless of
   `tools`: `AskUserQuestion`, `EnterPlanMode`, `ExitPlanMode` (unless `permissionMode: plan`),
   `ScheduleWakeup`, `WaitForMcpServers`.

5. **Permission modes per subagent.** `default`, `acceptEdits`, `auto`, `dontAsk`
   (auto-deny prompts; explicitly-allowed tools still work), `bypassPermissions`, `plan`.
   "Subagents inherit the permission context from the main conversation and can override the
   mode, except when the parent mode takes precedence."

6. **MCP scoping.** `mcpServers` gives a subagent servers not in the main conversation. "Inline
   servers defined here are connected when the subagent starts and disconnected when it finishes.
   String references share the parent session's connection." "To keep an MCP server out of the
   main conversation entirely and avoid its tool descriptions consuming context there, define it
   inline here." Managed/`--strict-mcp-config`/`--bare` restrictions also cover subagent-frontmatter
   servers (v2.1.153).

7. **Nested subagents + hard depth cap.** "As of Claude Code v2.1.172, a subagent can spawn its
   own subagents... Only the top-level subagent's summary returns to you." Foreground subagents
   "can spawn at any depth... self-limiting." **"A background subagent at depth five does not
   receive the Agent tool and cannot spawn further. The limit is fixed and not configurable, and
   exists to prevent runaway concurrent trees."** Spawning is gated by listing `Agent` in `tools`
   (omit it to forbid). The main-thread-only `Agent(agent_type)` allowlist restricts which types
   can be spawned; inside a subagent definition the type list inside the parentheses is ignored.

8. **Parallelism.** "For independent investigations, spawn multiple subagents to work
   simultaneously." For sustained parallelism exceeding context, use **agent teams** (each worker
   its own independent context); to run many independent sessions in parallel, **background
   agents**.

9. **Resume.** Each invocation is a fresh instance; resuming retains "full conversation history,
   including all previous tool calls, results, and reasoning." Explore/Plan are one-shot
   (no agent ID, not resumable). Resume uses `SendMessage` (only available when agent teams are
   enabled via `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`).

10. **Model resolution order:** `CLAUDE_CODE_SUBAGENT_MODEL` env > per-invocation `model` param >
    frontmatter `model` > main conversation model. Default `inherit`. `isolation: worktree` runs
    the subagent in a temporary git worktree (isolated repo copy), auto-cleaned if no changes.
    `CLAUDE_AGENT_SDK_DISABLE_BUILTIN_AGENTS=1` removes all built-in subagent types in headless/SDK.

## Reproducibility note
Re-fetch the page; verify the frontmatter-fields table, the scope-precedence table, the
"depth five" background cap, and the plugin-field-restriction Note. All quotes are verbatim.
