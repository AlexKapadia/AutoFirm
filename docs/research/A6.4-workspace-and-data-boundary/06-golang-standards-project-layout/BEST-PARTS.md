# BEST-PARTS — Standard Go Project Layout → AutoFirm

## ADOPT
1. **Self-documenting top-level directories** whose names announce contents (directly satisfies
   CLAUDE.md §5.7 "no junk-drawer names"). AutoFirm public-repo skeleton, flow-ordered:
   `orchestration/`, `agents/`, `memory/`, `governance/`, `integration/`, `evaluation/`,
   `playbooks/`, `docs/research/`, `evidence/`, `configs/` (templates only), `scripts/`, `tests/`.
   No `utils/`, `common/`, `misc/`.
2. **The `/internal` principle = enforce the boundary by MECHANISM, not convention.** Go's compiler
   makes `internal/` un-importable from outside. AutoFirm's analogue: the **private workspace is
   un-committable by mechanism** — gitignore + pre-commit/CI scanners + a data-layer store — never
   "please don't commit this." This is the single most important transferable idea: privacy that a
   tool enforces, mirroring CLAUDE.md §5.6 "enforce in the data layer, not by convention."
3. **`/configs` = templates/defaults only** — populated config/secrets live outside the repo
   (reinforces 12-factor, source 01). Ship `*.example` files, never real values.
4. **Avoid `/src`** and other cargo-culted layouts; the structure should "read top-to-bottom like
   the data flow" (CLAUDE.md §5.7).

## REJECT / QUALIFY
- **Reject importing the Go-specific dirs literally** (`/cmd`, `/pkg`, `/build/package`) — AutoFirm
  is not a Go monorepo. Take the *naming/privacy principles*, not the Go directory names.
- **Qualify its authority:** it is a community convention, not an official spec — adopt the
  principles, don't cite it as a standard.

## Concrete build implication
- **Component:** the public-repo directory skeleton + a `STRUCTURE.md` map (flow-ordered).
- **Contract:** every top-level dir has one clear responsibility; "internal-style" privacy is
  enforced by the boundary-guard, not by naming alone.
- **Test:** a structure-lint test asserting no banned junk-drawer names exist and no file exceeds
  the 300-line limit (CLAUDE.md §5.7) — the layout is machine-checked, not vibes.
