# Best parts to adopt — CLI Reference

## Adopt
- **`claude --bg` + `claude agents --json` + `claude logs <id>` ARE AutoFirm's worker fleet primitives.** This is the officially-documented way to "run many independent sessions in parallel and monitor them from one place." The COO orchestrator dispatches background role-sessions, polls `claude agents --json` for live state, and tails `claude logs <id>` for triage — exactly the §4.1 fan-out / §4.3 fan-in mechanic, without bespoke process management.
- **`claude respawn <id>` is a first-class auto-resume primitive.** A stopped/dead background session restarts "with its conversation intact." `claude respawn --all` even re-launches every running session to pick up an updated binary. This is more robust than re-deriving state from git alone (complements R04 long-horizon autonomy).
- **`claude rm <id>` keeps the transcript** — removing a session from the list leaves the JSONL resumable via `--resume`, so the audit trail (R07) survives fleet cleanup.
- **`--worktree` maps directly onto §4.4 branch-per-experiment.** Each `experiment/<approach>` runs in its own isolated worktree under `.claude/worktrees/`, keeping `main` clean and parallel experiments context-isolated.
- **`--fallback-model` chain** (e.g. `opus,sonnet,haiku`) keeps a long unattended run alive through model-overload/retirement without human intervention.
- **`claude setup-token`** generates the long-lived OAuth token AutoFirm's scheduled/relaunched sessions need to authenticate non-interactively (CI/scripts).
- **`--settings` / `--setting-sources` / `--strict-mcp-config`** give per-role, locked-down, reproducible configuration — each role gets exactly the MCP servers and permissions it needs (least privilege, §5.6).
- **`--name`** every role-session (`coo`, `cto`, `cro-r06`, ...) so the fleet is human-navigable and resumable by name.

## Reject / caution
- **`--add-dir` does not load `.claude/` config from the added dirs** — don't expect a role's hooks/rules to activate just by adding its directory; configure per-session via `--settings`/`--mcp-config`.
- **`claude agents` / agent view "requires an interactive terminal"** to OPEN — so the *monitoring UI* is interactive, but `claude agents --json` (scriptable) and `claude --bg`/`logs`/`stop`/`respawn` are the headless-friendly fleet controls AutoFirm should script.
