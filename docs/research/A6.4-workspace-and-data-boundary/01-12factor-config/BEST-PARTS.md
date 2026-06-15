# BEST-PARTS — 12-Factor Config → AutoFirm

## ADOPT

1. **The litmus test as AutoFirm's boundary-correctness invariant.** Restate it as a hard,
   testable gate: *"The public AutoFirm codebase must be open-sourceable at any instant without
   leaking a single credential, finance figure, client name, or per-company datum."* This is the
   one-line definition of the A6.4 public/private boundary and the acceptance criterion the
   organizer/librarian role enforces. **Build implication:** a CI check + pre-commit gate that
   FAILS the build if any secret/sensitive value appears in the version-controlled tree (wired to
   source 04/05 scanners).

2. **Config (incl. all per-company finance & secrets) lives outside the repo, in the
   environment or a secret manager — never as committed files.** **Build implication:** the
   platform reads per-company config and credentials from env / a secret manager; the public repo
   carries only `*.example`/template files (cf. Go `/configs` "templates or default configs",
   source 06), never populated ones.

## REJECT / QUALIFY

- **Reject env-vars as the *sole* mechanism for large sensitive datasets.** The 12-factor model
  is about *config* (small key-values). AutoFirm's private side also holds whole **datasets**
  (financial models, deal docs, customer files) that do not fit in env vars. Those belong in a
  **gitignored private workspace + a governed data store with encryption-at-rest and data-layer
  tenant isolation** (sources 03, 09, 10), not in environment variables. So: env/secret-manager
  for *credentials & config*; governed private store for *data*. Both are "outside the public repo".

## Concrete build implication (component / contract / test)
- **Component:** `boundary-guard` (pre-commit + CI) implementing the litmus test as an automated
  gate over the public repo.
- **Contract:** public repo = code + templates only; private workspace = config + secrets + data,
  gitignored and stored under the governed store.
- **Test:** a CI job that synthesizes a fake credential/finance value, attempts to stage it, and
  asserts the gate **fails closed** (CLAUDE.md §5.6) — proving the boundary has teeth, not vibes.
