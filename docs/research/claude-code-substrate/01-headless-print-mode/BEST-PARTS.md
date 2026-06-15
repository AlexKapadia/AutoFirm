# Best parts to adopt — Headless / Print Mode

## Adopt
- **`claude -p` is AutoFirm's core role-execution call.** Every role-session is launched as a `claude -p` (or SDK `query()`) invocation with a role system prompt, a scoped tool allowlist, and a permission mode.
- **`--output-format json` is the machine-readable handoff envelope.** The orchestrator parses `result`, `session_id`, and `total_cost_usd` per invocation — gives free per-role spend telemetry feeding the §3.13 commit/gate cadence and the R08 spend limits.
- **`--output-format stream-json` for live monitoring.** Long role-sessions stream `system/init`, `api_retry`, and (with `--include-hook-events`) hook events to a watcher process — this is the substrate for the North Star heartbeat and the auto-resume watchdog observing progress.
- **`--max-budget-usd` and `--max-turns` are hard fail-closed guards** per role-session, satisfying CLAUDE.md §5.6 (deny by default) and the R08 spend/rate-limit requirement at the substrate level — not just in app logic.
- **`--json-schema` for typed inter-role contracts.** The CTO's typed data contracts (Gate 1) can be enforced at the substrate boundary: a role returns schema-validated `structured_output`, so the next role never parses free text.
- **`--append-system-prompt-file`** loads each role's durable brief (COO/CTO/CRO/CDO/CCO) from a file under version control rather than inlining prompts.
- **`--exclude-dynamic-system-prompt-sections`** improves prompt-cache reuse across the many machine-identical role launches — a real cost lever for a days/weeks run.

## Reject / caution
- **Do NOT rely on `--bare` for role-sessions** that need CLAUDE.md, hooks, skills, or project MCP — bare mode deliberately skips all of them. Reserve `--bare` for trivial, fully-flag-specified utility calls.
- **10MB stdin cap** — never pipe large corpora; write to a file and pass the path (matches the "send minimum data" §5.6 rule anyway).
- **Verify the Agent SDK credit change (2026-06-15)** against the live support article before assuming subscription-plan economics for a long autonomous run (open question, see SYNTHESIS).
