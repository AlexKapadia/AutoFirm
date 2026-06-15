# SUMMARY — Claude Code: Run Claude Code programmatically (headless / Agent SDK CLI)

## Full citation
- **Title:** "Run Claude Code programmatically" (Headless mode / `claude -p`)
- **Author/Org:** Anthropic (Claude Code documentation)
- **Year:** 2026 (live docs; fetched 2026-06-15)
- **Venue/Publisher:** Official Claude Code documentation
- **URL:** https://code.claude.com/docs/en/headless (canonical; `docs.claude.com/.../headless` 301-redirects here)

## Questions informed
- **L1.A5.1** CLI capabilities/limits (headless, sessions, settings, MCP).
- **L1.A5.2** Determinism / resumability / idempotency of CLI sessions.
- **L1.A5.3** Tool/permission model (allowedTools, permission modes in `-p`).

## GRADE tier
**High** for the substrate-capability claims. This is the **primary source of record** for the
exact system AutoFirm runs on (the vendor's own normative spec of `claude -p`). Vendor docs are
normally Low under DEPTH-RUBRIC §2, but **up-rated to High** because it is the authoritative,
versioned specification of the artifact under study — there is no "more primary" source for what
a flag does than the tool's own reference. Claims cross-checked against the CLI reference,
permissions, and sandboxing pages (independent doc pages, consistent).

## Key claims (exact, with locators)

1. **Non-interactive entry point.** "Add the `-p` (or `--print`) flag to any `claude` command to
   run it non-interactively. All [CLI options] work with `-p`." Verbatim example:
   `claude -p "Find and fix the bug in auth.py" --allowedTools "Read,Edit,Bash"`

2. **Bare mode for reproducibility.** "Add `--bare` to reduce startup time by skipping
   auto-discovery of hooks, skills, plugins, MCP servers, auto memory, and CLAUDE.md... Bare mode
   is useful for CI and scripts where you need **the same result on every machine**. A hook in a
   teammate's `~/.claude` or an MCP server in the project's `.mcp.json` won't run, because bare
   mode never reads them. Only flags you pass explicitly take effect." In bare mode Claude has
   the Bash, file read, and file edit tools; context loads only via explicit flags
   (`--append-system-prompt[-file]`, `--settings`, `--mcp-config`, `--agents`,
   `--plugin-dir`/`--plugin-url`). "Bare mode skips OAuth and keychain reads. Anthropic
   authentication must come from `ANTHROPIC_API_KEY` or an `apiKeyHelper`." "`--bare` is the
   recommended mode for scripted and SDK calls, and will become the default for `-p`."

3. **Output formats.** `--output-format`: `text` (default); `json` (structured JSON with result,
   session ID, metadata — text in `result`; payload includes `total_cost_usd` + per-model cost
   breakdown); `stream-json` (newline-delimited JSON events). `--output-format json
   --json-schema '<JSON Schema>'` returns schema-conforming output in the `structured_output`
   field.

4. **Streaming + retry telemetry.** `--output-format stream-json --verbose
   --include-partial-messages` streams token deltas. On retryable API error a `system/api_retry`
   event is emitted with fields `attempt`, `max_retries`, `retry_delay_ms`, `error_status`,
   `error` (categories incl. `rate_limit`, `overloaded`, `server_error`, `max_output_tokens`),
   `uuid`, `session_id`. First stream event is `system/init` (reports model, tools, MCP servers,
   loaded plugins; `plugins` and `plugin_errors` arrays — usable to **fail CI when a plugin did
   not load**).

5. **Auto-approve / locked-down runs.** `--allowedTools "Bash,Read,Edit"` lets listed tools run
   without prompting (permission-rule syntax, e.g. `Bash(git diff *)`). Permission modes set a
   baseline: `dontAsk` "denies anything not in your `permissions.allow` rules or the read-only
   command set, which is useful for locked-down CI runs"; `acceptEdits` auto-approves edits +
   common fs commands (`mkdir`, `touch`, `mv`, `cp`) but "other shell commands and network
   requests still need an `--allowedTools` entry or a `permissions.allow` rule, otherwise the run
   aborts when one is attempted."

6. **Resumption (multi-turn).** "Use `--continue` to continue the most recent conversation, or
   `--resume` with a session ID to continue a specific conversation." Capture pattern:
   `session_id=$(claude -p "Start a review" --output-format json | jq -r '.session_id')` then
   `claude -p "Continue that review" --resume "$session_id"`. "Run both commands from the same
   directory: session ID lookup is scoped to the current project directory and its git worktrees."

7. **Stdin cap (limit).** "As of Claude Code v2.1.128, piped stdin is capped at 10MB"; exceeding
   it exits non-zero with a clear error — workaround is to reference a file path in the prompt.

8. **Background-task lifecycle at exit.** A background Bash task started during `claude -p` "is
   terminated about five seconds after Claude has returned its final result and stdin has closed."
   Before v2.1.163 a never-exiting background process held the invocation open indefinitely.

9. **Skills/commands in `-p`.** User-invoked skills and custom commands work in `-p` (include
   `/skill-name` in the prompt). Interactive-dialog commands (`/config`, `/login`) are unavailable.

10. **Billing note (operational).** "Starting June 15, 2026, Agent SDK and `claude -p` usage on
    subscription plans will draw from a new monthly Agent SDK credit, separate from interactive
    usage limits." (Directly relevant to AutoFirm quota/watchdog planning.)

## Reproducibility note
Re-fetch https://code.claude.com/docs/en/headless and grep for `--bare`, `--output-format`,
`--resume`, "10MB", "five seconds". Flag names verified against the CLI reference page. No
formulae; claims are exact flag semantics quoted above.
