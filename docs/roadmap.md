# AutoFirm Roadmap — Gated Phases

AutoFirm is built in numbered phases, each ending in a **hard verification gate** (`CLAUDE.md` §4.2). Phase
N+1 does not start until phase N's gate is green. `main` is always green and shippable. This file is the
single source of truth for what is and isn't done — kept honest, updated at every gate.

Legend: ✅ done · 🔄 in progress · ⏳ not started

| Gate | Phase | Objective | Gate is green when… | Status |
|------|-------|-----------|----------------------|--------|
| 0 | **Bootstrap** | Repo, contract, skeleton, CI scaffold | Repo initialised, `CLAUDE.md` ratified, structure + research charter in place, pushed to GitHub | 🔄 |
| 1 | **Deep Research** | Populate the research library to the CRO bar across all streams | Every stream has a peer-reviewed-grade `SYNTHESIS.md`; peer-review pass accepts; CRO declares depth sufficient | ⏳ |
| 2 | **Architecture & Contracts** | Ratify the platform architecture, typed data contracts, threat model | CTO architecture + STRIDE threat model reviewed and ratified, fully research-cited | ⏳ |
| 3 | **Orchestration substrate (vertical slice)** | Prove the core mechanic end-to-end on a small scale | Orchestrator spawns a worker session, they communicate over the audited bus, an audited decision is produced — with tests | ⏳ |
| 4 | **Dynamic org engine** | Roles-as-data: hire / fire / re-scope, strict hierarchy, managers own reports' specs | Org can restructure itself under test; hierarchy + role specs enforced; fully audited | ⏳ |
| 5 | **Knowledge / learning layer** | The researched-best memory infrastructure; everything learns | Persistent knowledge layer integrated; agents read/write/learn; tested | ⏳ |
| 6 | **Business-function agent library** | Modular agents/teams for each automatable company function | Each function team operational against contracts, general (not overfit), tested | ⏳ |
| 7 | **Integration & data layer** | Pluggable DBs and AI-provider connectors | Connectors behind a stable contract, secrets fail-closed, tested with sandboxed fakes | ⏳ |
| 8 | **Control plane / UI** | The user-facing way to give an idea and watch the company run | UI DoD met (live E2E, a11y, responsive, perf, state coverage) — if/when UI is in scope | ⏳ |
| 9 | **Resilience** | Handoff-on-context-exhaustion + auto-resume watchdog | A run survives context exhaustion and a simulated quota stall, resuming from git + tasks + roadmap | ⏳ |
| 10 | **Hardening & release** | Coverage, mutation, scans, evidence showcase, public-data validation | Mutation score high, scans clean, `evidence/` built, public-data validation passed, release tagged | ⏳ |

## Notes

- Gates 3–7 will spawn `experiment/<approach>` branches where more than one approach is viable; only the
  measured winner merges to `main` (no graveyard).
- The North Star / CCO alignment review runs on a ~30-minute heartbeat (or at each gate) and any RED is
  stop-and-fix before new feature work.
