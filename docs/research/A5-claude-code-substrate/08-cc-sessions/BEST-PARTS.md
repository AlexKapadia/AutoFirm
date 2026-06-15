# BEST-PARTS — Sessions / resumability for AutoFirm

## ADOPT

- **JSONL transcripts at `~/.claude/projects/<project>/<session-id>.jsonl` as the substrate's
  built-in externalized state + audit replay log.** "Each line is a JSON object for a message,
  tool use, or metadata entry" (claim 4) — this is a ready-made append-only event log for A6
  provenance and A3 handoff/resume. Build implication: AutoFirm's run ledger references the
  session-id JSONL; the watchdog (CLAUDE.md §4.8) resumes via `--resume <session-id>` read from
  git/roadmap state. Pin `CLAUDE_CONFIG_DIR` and raise `cleanupPeriodDays` so audit history isn't
  auto-deleted at 30 days.
- **`--resume <session-id>` (captured from the `-p --output-format json` envelope) as the
  canonical durable-handoff/resume mechanism** (L2.A3, A5 watchdog). It is deterministic over
  STATE: the same transcript is reloaded and appended to. Pair with the scope rule (claim 3):
  resume MUST run from the originating project directory / a git worktree of it.
- **`isolation: worktree` (subagents, source 02) + git-worktree-scoped session lookup (claim 3)**
  as the branch-per-experiment substrate: each `experiment/<approach>` runs in its own worktree
  with its own resumable sessions, main stays clean (CLAUDE.md §3.4/§4.4).
- **`--fork-session` / `/branch` for exploring alternatives without mutating the baseline session**
  (CLAUDE.md §3.4 evidence-driven forks) — original transcript preserved.
- **`--no-session-persistence` / `CLAUDE_CODE_SKIP_PROMPT_HISTORY` for ephemeral
  no-PII-on-disk runs** when handling anything that must not be persisted (CLAUDE.md §3.12
  synthetic-only-for-sensitive boundary).

## REJECT / CRITICAL CAVEATS (concurrency + determinism)

- **DO NOT concurrently resume the same session-id from two processes.** The doc warns: "If you
  resume the same session in two terminals without forking, messages from both interleave into one
  transcript" (claim 5). AutoFirm's orchestrator MUST treat a session-id as a single-writer
  resource (a lease/lock in the run ledger) and use `--fork-session` for parallel exploration.
  This is the substrate analogue of the single-writer rule AutoFirm already enforces on disk.
- **DO NOT assume forked/resumed sessions inherit session-scoped permission grants** (claim 5):
  "allow for this session" approvals do NOT carry to a fork. Persisted authority must come from
  managed/project `permissions.allow` rules (source 04/05), NOT from interactive session grants —
  reinforces "security lives in managed settings, not session state."
- **DO NOT conflate substrate determinism with MODEL determinism.** The session/transcript layer
  is deterministic about state and replay; the MODEL's token output is NOT inherently deterministic
  (source 10). AutoFirm cannot claim reproducible *outputs* from `--resume` alone; deterministic
  *decisions* must come from deterministic CODE paths (CLAUDE.md §3.5 deterministic core), with
  the LLM layer treated as stochastic and validated statistically (A9.2).

## Concrete build implications
- Component: `run-ledger` storing {session-id, project-dir/worktree, status, cost, lease-holder};
  watchdog resumes idempotently via `--resume` only if no live lease (CLAUDE.md §4.8 idempotent).
- Contract: session-id = single-writer; parallel work = fork or separate worktree/session.
- Test: concurrency test asserts a second resume of a leased session-id is refused (no transcript
  interleave); resume-from-wrong-dir test asserts the documented "No conversation found" failure.
