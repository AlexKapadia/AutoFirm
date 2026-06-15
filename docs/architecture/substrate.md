# AutoFirm — Execution Substrate: Orchestrated Claude Code CLI Sessions (Gate-2 v1, ratified)

> How agents are spawned, scoped, handed off, and auto-resumed. The execution unit is a **headless
> Claude Code CLI session** (A5). Synthesizes A5 (substrate primitives), A3 (autonomy/handoff/resume),
> A1.5 (roles-as-agents), A7/A8 (sandbox + least-privilege), A6 (audit). **Determinism in code paths;
> stochastic LLM validated statistically** (A5). Source authority for A5 is the first-party Anthropic
> Claude Code spec — appropriate and CRO-accepted (LAYER1-SIGNOFF §1).

---

## 1. The execution unit (A5.1)
Production invocation is the **bare, schema-typed, headless** form (A5):
```
claude -p --bare --output-format json --json-schema <stage-output-contract>
       --permission-mode dontAsk
       --settings <version-pinned> --mcp-config <version-pinned> --agents <version-pinned>
```
- `--bare` strips ambient hooks/MCP so production runs are reproducible (A5 **rejects** non-bare for
  production — ambient config varies per machine).
- The JSON envelope returns `session_id` and `total_cost_usd` — captured into the audit log (A6) and
  used as the A1 first-class cost metric.
- Manifests (settings / mcp-config / agents) are **version-pinned** so a run is replayable (A3).

---

## 2. Roles as agents (A5.2 ↔ A1.5)
- A `RoleSpec` (org-model §2) materializes as a `.claude/agents/<role>.md` file: **roles-as-data
  become roles-as-agent-files**.
- **Least-authority tool scoping** per role: each agent file declares only the tools/MCP/permissions
  its `tool_grants` allow (A5; A8.3 least-privilege). Tool/MCP/permission inheritance is role-based.
- **Fixed depth-5 cap** on subagent nesting prevents runaway fan-out (A5). This is the substrate-level
  guard underneath the A1 ~3–4-per-cluster routing cap. **Subagents do not silently spawn subagents**
  (CLAUDE.md §3.1) — fan-out is an explicit orchestrator decision realized as a SPAWN request
  (org-model §2.3).

---

## 3. Scoping & authority (A5.3, A7, A8) — and the T2 hook ruling
**Authority is deny-first in MANAGED scope only** (A5): lower scopes cannot loosen a managed-deny
rule. Enforcement is layered:

```
TRUE ENFORCEMENT BOUNDARY (fail-closed):
  1. OS-level + container/VM two-layer sandbox          (A5, A7)
  2. permission deny-rules mirroring the sandbox        (A5)
  3. A8 API gateway PEP — the only egress to the world  (A8.1)
  4. SPIFFE identity + short-TTL scoped credentials     (A8.3)

LOGGING / CONVENIENCE PLANE ONLY (fail-OPEN — NOT a boundary):
  - Claude Code hooks (PreToolUse / PostToolUse / Stop)
```

**T2 ruling (explicit, binding):** Claude Code **hooks are fail-OPEN** — A5 proves a missed/failed
hook does not stop the action. Therefore hooks are used **only** for audit-convenience and the
iterate-gate; they are **never the security boundary and never the sole path an audit record can take.**
The audit record is written through the A8 gateway mediation path (which *can* fail closed), so a
dropped hook can never silently lose an audit record (reconciles A6's hook-based logging with A5's
fail-open proof — see `tension-resolutions.md` T2).

---

## 4. Handoff & resume (A3, A5)
- **Resume:** `--resume <session_id>` from the **originating worktree** (A5).
- **Single-writer lease:** only one live session may hold a worktree's resume lease at a time (A5) —
  this is the substrate enforcement of the org-model single-writer artifact lock.
- **Parallel branches:** `--fork-session` spins isolated parallel explorations (A1 fan-out / E1
  topology bake-off), reconciled by the orchestrator on their own pushed branches (CLAUDE.md §4.4).
- **Re-grounding on resume (A3):** a resumed session re-injects the **verbatim stored goal** + saga
  state (SA/SO/SD, `data-contracts.md` §4) into a fresh context window. It **never re-infers the goal
  from a drifted transcript** (A3 src 07 goal-misgeneralization defense). A separate validation agent
  verifies outputs before the checkpoint commits.

---

## 5. Auto-resume watchdog (A3, CLAUDE.md §4.8)
A lightweight recurring watchdog provides resilience against quota/usage stalls. It is **idempotent
and non-invasive**: on each tick it checks git + the task list + the roadmap doc; if a run is already
in progress or the work is complete, it **exits immediately** and never starts a second concurrent
run or edits code. Resume state comes entirely from durable artifacts (git commit, task list, roadmap,
A4 memory snapshot), so a relaunched session picks up exactly where it left off (A3 saga checkpoints).
Two tiers (CLAUDE.md §4.8): (a) in-session scheduled task for ordinary heartbeats; (b) OS-level
scheduler (Windows Task Scheduler / cron) when the run must survive full session death. **Choice of
(a) vs (b) and watchdog-vs-Agent-SDK-telemetry is a DEFERRED L2 build decision** (A5).

---

## 6. Determinism doctrine (A5)
- **Code paths are deterministic** and tested for exactness (CLAUDE.md §3.11).
- **The LLM layer is stochastic** — A5 cites ≈80 unique completions per 1000 identical prompts
  (Thinking Machines 2025). It is therefore **validated statistically** via the A9 harness
  (pass@k/pass^k, repeated trials, reported variance), never asserted to be reproducible.

---

## 7. Substrate test hooks (feed A9 / E-series)
- Sandbox-escape tests; cross-agent context-leakage tests (A5, A7).
- Session-resume **idempotency** test (replay never double-applies — A3 idempotency keys).
- Stochastic-output **distribution** test over ≥1000 trials (A5/A9).
- Depth-5 / spawn-cap saturation tests (A5/A1.5).
All mutation-tested (A9, B14).

---

## 8. Deferred substrate decisions (A5 → L2 build)
- Container vs VM isolation technology choice.
- Agent-teams vs session-`--resume` for long-running org continuity.
- Watchdog mechanism vs new Agent-SDK telemetry.
These are **build-time** choices gated on golden-set evidence, not architecture-time assumptions.
