# BEST-PARTS — Headless / `claude -p` for AutoFirm

## ADOPT

- **`claude -p --bare` as the default execution unit of every AutoFirm agent (orchestrator AND
  subagent-process).** Rationale: bare mode is explicitly designed so you "need the same result
  on every machine" — it skips ambient hooks/MCP/CLAUDE.md/plugins that vary by host, giving the
  **idempotent, host-independent launch** AutoFirm's reproducibility/audit bar (CLAUDE.md §3.2,
  §5.6) requires. Build implication: the platform's "spawn an agent" primitive is a wrapper that
  always passes `--bare` plus an explicit, version-pinned `--settings`/`--mcp-config`/`--agents`
  manifest. Nothing implicit.
- **`--output-format json` (+ `--json-schema`) as the typed inter-agent contract carrier.** Every
  agent returns a machine-parseable envelope with `result`, `session_id`, `total_cost_usd`, and
  schema-validated `structured_output`. This is exactly the "typed data contract between stages"
  the CTO role mandates (CLAUDE.md §2) — directly feeds A2 (communication) and A9 (eval).
  Build implication: the orchestrator never parses free text; it parses the JSON envelope and
  validates `structured_output` against the stage's schema; a schema-validation failure is a
  fail-closed gate.
- **`--resume <session_id>` captured from the JSON envelope as the handoff/resume mechanism.**
  Directly satisfies the watchdog/auto-resume requirement (CLAUDE.md §4.8): persist `session_id`
  to git/roadmap state, and a relaunched agent resumes the exact session. Couple with the
  same-directory/worktree scope rule (claim 6).
- **`system/init` `plugins`/`plugin_errors` and `system/api_retry` events for closed-loop
  telemetry.** Feed A6 (telemetry) and the North Star heartbeat: fail the run if a required
  plugin did not load; surface rate-limit/overload retries to the watchdog instead of silently
  stalling.
- **`dontAsk` permission mode for unattended runs.** "Denies anything not in your
  `permissions.allow` rules or the read-only command set" — the fail-closed default for
  autonomous CI-style execution (CLAUDE.md §5.6).

## REJECT (for AutoFirm's substrate)

- **Relying on ambient (non-`--bare`) `-p` for production agents.** Rejected: the doc states a
  teammate's `~/.claude` hook or a project `.mcp.json` server "won't run" only in bare mode —
  i.e. in non-bare mode they *do* run, which is exactly the non-determinism / supply-chain
  surface AutoFirm must exclude. Allowed only for human-interactive developer sessions.
- **Piping >10MB via stdin.** Hard 10MB cap (v2.1.128). Reject piping large corpora; pass file
  paths (also better for audit provenance).
- **Treating `claude -p` text output as the contract.** Reject; always `--output-format json`.

## Concrete build implications
- Component: `agent-launcher` wrapper enforces `--bare` + pinned manifest + `--output-format json`
  + `dontAsk`; emits the `session_id` to the run ledger.
- Contract: every agent result conforms to a versioned JSON Schema (validated by orchestrator).
- Test: a determinism test launches the same bare manifest N times and asserts identical
  `system/init` tool/plugin sets (substrate-config determinism; model-output determinism is a
  separate concern — see source 10).
- Operational: budget against the new Agent SDK credit (2026-06-15); the watchdog reads
  `total_cost_usd` per invocation.
