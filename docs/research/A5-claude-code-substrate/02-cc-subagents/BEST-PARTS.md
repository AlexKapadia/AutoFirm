# BEST-PARTS — Subagents for AutoFirm

## ADOPT

- **Subagents = the unit of the agent-company org chart, defined as version-controlled files in
  `.claude/agents/`.** "Roles as data" (CLAUDE.md §2, L2.ORG): each org role (COO, CTO, CRO,
  Researcher, QA, North Star) is a checked-in subagent file with a scoped `tools`/`mcpServers`/
  `permissionMode`. Build implication: the org engine reads/writes these files to spawn/retire/
  re-scope agents; the file set IS the auditable org chart.
- **Isolated context window per subagent (claim 1) as the context-protection mechanism.** This is
  the substrate guarantee behind CLAUDE.md §3.1 ("protect your own context") — delegate heavy
  reads/research/test-triage to subagents that "return only the summary." Adopt as the default
  pattern for every heavy task.
- **`tools` allowlist + `disallowedTools` + `permissionMode` per role for least privilege**
  (CLAUDE.md §5.6, maps to L1.A7.3). E.g. a Researcher subagent gets `Read, Grep, Glob, WebSearch,
  WebFetch` and `dontAsk`; it cannot Write/Edit/Bash. A QA reviewer is read-only. This is
  capability-scoping at the substrate level (see source 09, Miller).
- **Inline `mcpServers` to keep tool descriptions out of the orchestrator's context** (claim 6) —
  scope Playwright/DB/Slack to the specific worker that needs them; the orchestrator never pays
  the context cost. Directly supports A8 (integration layer) + context discipline.
- **`isolation: worktree` for branch-per-experiment workers** (CLAUDE.md §3.4/§4.4): each
  competing approach runs in its own isolated repo copy, auto-cleaned if it makes no changes —
  exactly the "experiments compete in isolation, main stays clean" model.
- **The fixed depth-5 background cap + `Agent`-in-`tools` gate (claim 7) as the runaway-fan-out
  safety control.** Adopt explicitly: AutoFirm's org engine sets per-role spawn allowlists via
  `Agent(type,...)` on main-thread agents and omits `Agent` from leaf workers, so fan-out is an
  explicit, bounded decision (CLAUDE.md §4.1/§4.3). Map the "span-of-control" org constraint
  (L1.B1.3) onto this primitive.

## REJECT / treat with caution

- **Do NOT rely on `hooks`/`mcpServers`/`permissionMode` in PLUGIN-distributed subagents** —
  silently ignored for security (claim 3). AutoFirm's governed roles must live in
  `.claude/agents/` or managed settings, NOT shipped as a plugin, or their security scoping
  evaporates. This is a fail-closed-relevant gotcha.
- **Do NOT treat `bypassPermissions` as an org-role default.** Reserve for sandboxed/container
  experiments only (see source 05/06).
- **Do NOT depend on cross-subagent shared memory via context** — each is fresh; pass state via
  the JSON envelope / externalized files (A4 memory layer), not via assumed shared history.
- **Resume via `SendMessage` requires the experimental agent-teams flag** — treat as not-yet-GA;
  prefer session-level `--resume` (source 01/08) for durable handoff until it stabilizes.

## Concrete build implications
- Component: `org-engine` that materializes roles as `.claude/agents/*.md` with scoped frontmatter.
- Contract: every role file pins `tools`, `model`, `permissionMode`, and (for spawners)
  `Agent(allowed-types)`.
- Test: assert leaf-worker role files have no `Agent` in `tools` (no unbounded fan-out);
  assert read-only roles deny `Write,Edit,Bash`; mutation-test that removing a deny still fails.
