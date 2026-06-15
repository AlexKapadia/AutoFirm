# SYNTHESIS — A5: Claude Code CLI substrate capabilities (L1.A5.1 / .2 / .3)

> Branch A5 (Platform Engineering). Layer 1 (Foundations) — literature/spec only, no build
> decisions; produces the evidence that L2.A5 will turn into the CLI-substrate execution model.
> Single-writer: this branch owns only docs/research/A5-claude-code-substrate/.
> Sources: 10 (8 Anthropic Claude Code primary-spec pages + 2 external primary/peer-grade).

## 1. The question, and how the substrate answers it

AutoFirm runs as orchestrated Claude Code CLI sessions. A5 establishes, from the authoritative
sources, EXACTLY what that substrate can and cannot do, so the platform is built on documented
capability rather than assumption.

### L1.A5.1 — CLI capabilities and limits (sessions, subagents, hooks, MCP, headless, settings)
The substrate provides every primitive AutoFirm's orchestrator model needs:
- Headless execution (claude -p, --bare, --output-format json[+--json-schema], --max-turns) — the
  per-agent execution unit (source 01).
- Subagents with isolated context windows, file-defined roles, per-role tool/MCP/permission
  scoping, parallelism, and a fixed depth-5 background fan-out cap (source 02) — the org-chart
  primitive.
- Hooks (PreToolUse/PostToolUse/Stop/SessionStart/...) for audit, policy gating, and the
  iterate-loop green-gate (source 03).
- MCP as the standardized external-tool plane (HTTP/stdio/SSE-deprecated/WS), scoped+managed (src 07).
- Settings with a strict managed > CLI > local > project > user precedence (source 04).
- Sessions persisted as JSONL transcripts, resumable by id, branchable (source 08).
Documented LIMITS that shape AutoFirm: stdin 10MB cap; background tasks killed ~5s after exit;
plugin subagents silently ignore hooks/mcpServers/permissionMode; sandbox unavailable on native
Windows; --strict-mcp-config does not filter --agents-inline servers.

### L1.A5.2 — Determinism, resumability and idempotency
TWO LAYERS, cited separately and both load-bearing:
- State layer (deterministic): sessions/transcripts/--resume/settings replay state faithfully;
  --bare gives host-independent launch (sources 01, 08). Resume is scoped to the project dir + git
  worktrees. Concurrency caveat: resuming one session-id from two processes interleaves transcripts,
  so session-id must be single-writer; parallelism uses --fork-session or separate worktrees (src 08).
- Model-output layer (NOT deterministic): identical prompts at temperature 0 yield a distribution
  of completions because hosted inference lacks batch invariance (Thinking Machines 2025: 80 unique
  completions / 1000; source 10). AutoFirm cannot control the serving batch size.
Resolution: deterministic guarantees come from CODE paths; the LLM is a validated stochastic layer
(CLAUDE.md 3.5/3.11). Reproducibility is proven statistically (repeat-trial, CIs — A9.2), not asserted.

### L1.A5.3 — Tool/permission model and sandboxing
A layered, model-independent authority model, grounded in object-capability theory (Miller 2003,
source 09 — POLA, confused-deputy prevention via "no designation without authority"):
- Permission rules (deny-first; managed-deny un-overridable; enforced by Claude Code, not the
  model) are the HARD authority boundary (source 05).
- OS sandbox (Seatbelt / bubblewrap+socat) enforces fs+network limits on Bash AND its subprocesses,
  closing the gap that permission Read/Edit rules leave open for subprocess file access (src 06).
- Hooks are fail-OPEN and must NOT be the sole control (source 03).
Documented SANDBOX LIMITS: not a complete boundary (no TLS inspection -> domain fronting/exfil;
Unix-socket escalation; default read exposes credentials; native Windows unsupported).

## 2. Full alternative space surveyed (per DEPTH-RUBRIC 4)

The options for A5 are the candidate ways to USE / harden the substrate; each judged ADOPT/REJECT
with cited evidence:

| Dimension | Options surveyed | Decision (evidence) |
|---|---|---|
| Agent execution | interactive / non-bare -p / **-p --bare + pinned manifest** | ADOPT bare+pinned for prod; REJECT non-bare for prod (ambient hooks/MCP vary) — src 01 |
| Inter-agent contract | free-text stdout / **--output-format json + --json-schema** | ADOPT JSON envelope; REJECT text — src 01 |
| Org/roles | ad-hoc prompts / **file-defined subagents** / agent teams / background agents | ADOPT subagent files as roles; teams/background for sustained parallelism — src 02 |
| Hard authority boundary | CLAUDE.md instructions / **permission deny rules** / hooks / **OS sandbox** | ADOPT permission rules + sandbox (both); REJECT hooks-as-boundary (fail-open) and instructions (not enforced) — src 03/05/06/09 |
| Multi-tenant isolation | convention / permission paths only / **sandbox + outer container/VM** | ADOPT sandbox + per-tenant container (built-in sandbox not a complete boundary); REJECT convention/permission-only — src 06 |
| Network egress | arg-constrained Bash allow / **deny curl+wget, WebFetch domain rules + sandbox allowedDomains** | ADOPT deny-net-tools + domain allowlist; REJECT arg-constrained Bash (trivially bypassed) — src 05/06 |
| MCP transport | **HTTP** / SSE(deprecated) / stdio / WS | ADOPT HTTP default; stdio for local; REJECT SSE/WS for new OAuth integrations — src 07 |
| Resume/handoff | re-prompt fresh / **--resume <id> from JSON envelope** / SendMessage(experimental) | ADOPT --resume (single-writer lease); SendMessage not-yet-GA — src 01/02/08 |
| Determinism stance | "temp 0 = deterministic" / **deterministic-code-core + stochastic-LLM-layer + statistical eval** | ADOPT two-layer model; REJECT LLM-output-determinism claims — src 08/10 |
| Config governance | per-project trust / **managed control plane + allowManaged*Only locks** | ADOPT managed control plane; REJECT trusting lower scopes for security — src 04/05 |

Excluded (scope boundary, named): the Python/TypeScript Agent SDK packages internal APIs (A5 covers
the CLI substrate; SDK-package ergonomics belong to L2.A5 build); plugin-marketplace distribution
mechanics (A8/governance); agent-teams deep mechanics (A1/A2). Referenced where they bound a
decision but not summarized in full here.

## 3. Concrete, cited recommendation for AutoFirm (feeds L2.A5 + L3.PLATFORM)

The AutoFirm CLI-substrate execution model should be:

1. Execution unit: claude -p --bare --output-format json with a version-pinned
   --settings/--mcp-config/--agents manifest and --permission-mode dontAsk. Capture
   session_id/total_cost_usd from the JSON envelope. (src 01)
2. Org engine: roles materialized as .claude/agents/*.md with least-authority tools, scoped
   mcpServers, permissionMode, and Agent(allowed-types) spawn allowlists; leaf workers omit Agent;
   rely on the fixed depth-5 cap as the runaway guard. (src 02, 09)
3. Authority = capabilities, deny-first, in MANAGED scope: the never-do list, kill-switch, sandbox
   locks, and allowManaged{Hooks,Mcp,PermissionRules}Only live in managed settings; no lower scope
   can loosen them. (src 04, 05)
4. Two-layer enforcement for every Bash-capable agent: managed fail-closed sandbox
   (enabled+failIfUnavailable+allowUnsandboxedCommands:false, credential denyRead, domain allowlist)
   INSIDE a per-tenant container/VM; permission deny rules mirror the boundary. (src 06)
5. Untrusted-input discipline (confused-deputy prevention): agents that ingest external/MCP content
   are SEPARATE capability subjects from any agent with write/egress authority. (src 07, 09)
6. Hooks for audit + iterate-gate only (append-only ledger via SessionStart/PostToolUse; Stop
   exit-2 green-gate), never as the hard boundary. (src 03)
7. Resume/handoff: --resume <session_id> from the originating worktree, session-id treated as
   single-writer (lease in run ledger); --fork-session/worktrees for parallel experiments; raise
   cleanupPeriodDays + pin CLAUDE_CONFIG_DIR for audit retention. (src 08)
8. Determinism doctrine: deterministic decisions in code; LLM layer stochastic and validated by
   repeat-trial statistics; never claim reproducible LLM output. (src 08, 10)

## 4. Open items handed to L2.A5 (build decisions, not L1)
- Concrete container/VM choice for the outer isolation boundary (dev container vs
  @anthropic-ai/sandbox-runtime vs per-tenant VM) — measure on a golden security/perf set.
- Whether to adopt agent-teams/SendMessage once GA vs session --resume for live multi-agent comms
  (depends on A1/A2 topology choice).
- Watchdog vs the new (2026-06-15) Agent SDK credit + system/api_retry telemetry.

## 5. Dependencies / gate status
A5 is pure L1 (no un-PASSED L1 dependency). It FEEDS L2.A5 (execution model), L2.A7 (safety stack:
sandbox/permissions/kill-switch), L2.A6 (audit via JSONL transcripts + hooks), and L2.ORG
(roles-as-subagent-files). Not yet QA-PASSED — seeded for CRO/QA review per RESEARCH-PROGRAM 2.
