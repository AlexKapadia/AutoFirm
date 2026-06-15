# SUMMARY — Claude Code: Manage sessions (+ CLI reference)

## Full citation
- **Title:** "Manage sessions" (with cross-reference to "CLI reference")
- **Author/Org:** Anthropic (Claude Code documentation)
- **Year:** 2026 (live docs; fetched 2026-06-15)
- **Venue/Publisher:** Official Claude Code documentation
- **URL:** https://code.claude.com/docs/en/sessions ; CLI: https://code.claude.com/docs/en/cli-reference

## Questions informed
- **L1.A5.2** Determinism, resumability & idempotency of CLI sessions (PRIMARY — substrate side).
- **L1.A5.1** Session/state-externalization capability for long-horizon autonomy + handoff (A3).

## GRADE tier
**High** (primary source of record for substrate session mechanics). The model-output
non-determinism side of L1.A5.2 is covered by source 10 (Thinking Machines) + corroborating
arXiv work — the substrate is deterministic about state/replay, the MODEL is not, and the two
must be cited separately.

## Key claims (exact, with locators)

1. **Session = saved conversation tied to a project directory.** "Claude Code stores it locally
   as you work, so you can resume where you left off, branch to try a different approach, or
   switch between tasks."

2. **Resume entry points.** `claude --continue` (most recent session in current dir);
   `claude --resume` (session picker); `claude --resume <name>`; `claude --from-pr <number>`;
   `/resume` (switch from inside a session). Headless/SDK sessions (`claude -p`) don't appear in
   the picker but "you can still resume one by passing its session ID to
   `claude --resume <session-id>`."

3. **Resume scope rules (LOAD-BEARING for handoff).** "Run this from the directory the session was
   started in: session ID lookup is **scoped to the current project directory and its git
   worktrees**, so a session created elsewhere reports `No conversation found with session ID:
   <session-id>`." Picker defaults to current worktree; `Ctrl+W` widens to all worktrees of the
   repo, `Ctrl+A` to every project on the machine.

4. **State externalization (the durable substrate).** "Transcripts are stored as JSONL at
   `~/.claude/projects/<project>/<session-id>.jsonl`, where `<project>` is derived from your
   working directory path. **Each line is a JSON object for a message, tool use, or metadata
   entry.**" Relocatable via `CLAUDE_CONFIG_DIR`. Local files removed after 30 days by default
   (`cleanupPeriodDays`). Suppress writes via `CLAUDE_CODE_SKIP_PROMPT_HISTORY` or, in
   non-interactive mode, `--no-session-persistence`.

5. **Branching / forking.** `/branch [name]` or `claude --continue/--resume --fork-session`
   "creates a copy of the conversation so far and switches you into it, leaving the original
   intact." The original is unchanged. **CAVEAT:** "Permissions you approved with 'allow for this
   session' do not carry over to the new branch." And: **"If you resume the same session in two
   terminals without forking, messages from both interleave into one transcript."** (i.e. concurrent
   resume of one session ID is NOT safe.)

6. **Context management within a session.** `/clear` (empty context; previous saved+resumable);
   `/compact [instructions]` (replace history with a summary); `/context` (show usage).
   Checkpointing (`/rewind`) rewinds code + conversation to an earlier point.

7. **CLI reference corroboration** (source: cli-reference page) — flags exist as named:
   `-p/--print`, `--output-format`, `--resume`, `--continue`, `--session-id`, `--fork-session`,
   `--max-turns`, `--allowedTools`, `--disallowedTools`, `--permission-mode`,
   `--dangerously-skip-permissions`, `--add-dir`, `--mcp-config`, `--strict-mcp-config`,
   `--agents`, `--append-system-prompt`, `--settings`, `--no-session-persistence`, `--bare`,
   `--model`, `--verbose`.

## Reproducibility note
Re-fetch and verify the JSONL transcript path/format, the "scoped to the current project
directory and its git worktrees" resume rule, and the two CAVEAT quotes (fork doesn't carry
session permissions; concurrent resume interleaves). These caveats are safety-critical for any
orchestrator that resumes/forks sessions programmatically.
