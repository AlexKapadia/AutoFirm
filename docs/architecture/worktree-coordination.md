# Active-Worktree Coordination Ledger

> **Purpose.** AutoFirm is built by several agents running **in parallel, one per git worktree** (the
> manual-worktree pattern — `Agent` `isolation:"worktree"` is unreliable on this box). This file is the
> single, living record of **who works where, which files each lane owns, and how shared files are
> reconciled at merge** so that no two agents ever edit the same artifact (`CLAUDE.md` §3.1 coordination
> rule; memory: *Coordination & CLAUDE.md binding*, *Cockpit coordination boundary*). It is operational,
> not architectural — update it whenever a worktree is added, retired, or re-scoped. The W1–W5 workstream
> design lives in [`evolution-plan.md`](evolution-plan.md); the gate checklist in [`roadmap.md`](roadmap.md).

## 1. Active worktrees (one agent per checkout)

| Worktree path | Branch | Lane (files this agent may write) | Uses |
|---|---|---|---|
| `C:/dev/AutoFirm` | `feature/w3-activation-bootstrap` | `src/autofirm/runtime/**` (composition root, `cli_entrypoint`), `src/autofirm/bootstrap/**`, their tests. **Owns** the shared-file reconciliation (see §2). | `autofirm` console script + `python -m autofirm.runtime.cli_entrypoint` |
| `C:/dev/AutoFirm-cockpit` | `feature/operator-cockpit` | `src/autofirm/cockpit/**`, `tests/cockpit/**`. **Add-only consumer** of the on-`main` front door. | `python -m autofirm.cockpit` (never a new console script) |
| `C:/dev/AutoFirm-review-gate` | `feature/human-output-review-gate` | `src/autofirm/output_review/**`, its tests. | `python -m autofirm.output_review` |

**Rule: one agent per worktree, one worktree per branch.** An agent never reaches into another worktree's
path or lane. Verify *your* worktree before acting (`git rev-parse --show-toplevel`); do not assume `cwd`.

## 2. Shared files — owner reconciles, everyone else appends additively

Three files are touched by every package and are therefore **owned by the w3-activation-bootstrap agent**,
who reconciles them when feature branches integrate to `main`:

- **`pyproject.toml` `[project.scripts]`** — only the w3 lane adds console scripts. Consumer packages
  (cockpit, output_review) ship as `python -m <pkg>` and add **only** their own
  `[project.optional-dependencies]` tier (e.g. cockpit's `textual`/`rich`), never a script entry.
- **`.importlinter`** — every new package **registers itself in the same change that creates it**
  (`CLAUDE.md` §7.3): add the package to the relevant `source_modules` list and, if it has an internal
  purity boundary, its own `[importlinter:contract:*]` block scoped to its own namespace. Additions are
  **append-only and namespace-local**, so they merge cleanly; the owner resolves any textual adjacency.
- **`CLAUDE.md`** — the binding contract. Edited only to record a new way of working (`§6`); a single owner
  per change, read back after writing (`§7.4`).

**Why append-only works:** because each lane only ever *adds* lines in its own namespace, git auto-merges
the common case; the owner's reconciliation pass at integration is a check, not a rewrite. No agent rewrites
or reorders another lane's entries.

## 3. Merge / integration protocol

1. **Stay green on your own branch first** — full fast gate locally (ruff → mypy → pytest/cov →
   import-linter), and the mutation gate for your lane (`CLAUDE.md` §3.6, §7.2) before requesting integration.
2. **Push your branch** (crash-safety; `CLAUDE.md` §3.13) — never leave verified work only on-machine.
3. **Integrate one branch at a time** through the w3/owner pass: the owner merges, reconciles the three
   shared files (§2), re-runs the fast gate on the merge result, and only then advances `main`.
4. **`main` stays self-consistent at all times** — it must never reference a package (in `.importlinter` or
   `[project.scripts]`) that is not also present in the same commit. (Verified: as of this writing `main`
   carries no W3/cockpit/output_review references — those live only on their feature branches.)
5. **No graveyard** (`CLAUDE.md` §3.8) — a retired worktree's row is deleted from §1 in the same change.

## 4. Current status snapshot (2026-06-19)

- **w3:** committed + pushed (`feature/w3-activation-bootstrap`), fast gate green (1812 tests, 99.47% cov).
- **cockpit:** active, running its mutation gate on `cockpit/core` in its own venv; respects the no-script
  boundary; `.importlinter`/`pyproject` edits are additive and namespace-local (no conflict with w3).
- **output_review:** committed, touches no shared file yet (will register in `.importlinter` when it lands).
- **No overlap detected** — every agent is confined to its own worktree and lane.
