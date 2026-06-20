# Results — output-review gate efficacy (measured)

Every number below is read from [`../_measured/`](../_measured/), produced by running
the **real** `autofirm.output_review` gate over the labelled synthetic golden set.
See [`METHODOLOGY.md`](METHODOLOGY.md) for how each was computed. Corpus: **18 cases**
(14 planted defects, 4 known-good controls), **7-check** deterministic floor.

## Headline

> An un-reviewed human spreadsheet carries an error **~86%** of the time, yet its
> author self-estimates only **~18%** (Panko; B16 `SYNTHESIS.md` §A.1). The
> independent gate's **measured escape rate is 0/14 = 0.0%**, and it raised **0/4**
> false positives. The gap between **~86%** un-reviewed risk and a **~0%** escape
> rate is the case for the gate.

| Metric | Measured | Target | 95% CI (Wilson) |
| --- | --- | --- | --- |
| Escape / false-pass rate (planted) | **0 / 14 = 0.000** | 0 | [0.000, 0.215] |
| False-positive rate (controls) | **0 / 4 = 0.000** | 0 | [0.000, 0.490] |
| Defect detection (all must-block classes) | **14 / 14 = 100%** | ~100% | — |
| Determinism (verdict stability) | **1 unique digest / 3600 reviews** | 1 | — |
| Line coverage | **100.0%** | ≥ 90% | — |
| Branch coverage | **130 / 130 = 100.0%** | ≥ 85% | — |
| Mutation survivors (package) | **0** (25 modules, score 1.0) | 0 | — |

## Defect-detection rate by Panko-Halverson class

The deterministic floor must KILL the MECHANICAL / PURE_LOGIC / OMISSION classes;
each planted defect was caught **by the correct check raising the correct class**.

| Panko class | Planted | Blocked | By correct check | Detection rate | Wilson 95% CI |
| --- | --- | --- | --- | --- | --- |
| MECHANICAL | 7 | 7 | 7 | **100%** | [0.646, 1.000] |
| PURE_LOGIC | 6 | 6 | 6 | **100%** | [0.610, 1.000] |
| OMISSION | 1 | 1 | 1 | **100%** | [0.207, 1.000] |
| EUREKA | — | — | — | *out of floor* | — |

The Wilson lower bounds are below 1.0 purely because the golden set is finite (a
small sample cannot *prove* a population rate of exactly 1.0); the **point estimate
is 100% on every must-block class** with **zero** misses. EUREKA (wrong domain model)
is intentionally not planted as must-block — it is the only class the deterministic
floor provably cannot reach and is routed to the advisory model layer.

## Per-defect outcomes (every planted defect caught, every control clean)

All 14 planted defects produced a verdict of `passed = False` with exactly the
expected blocking finding; all 4 controls produced `passed = True` with no findings
(full table in [`../_measured/per_case.csv`](../_measured/per_case.csv)):

- off-by-0.01 balance → `ACCOUNTING_IDENTITY` (PURE_LOGIC) — caught
- declared ≠ recomputed → `NUMERIC_RECOMPUTE` (MECHANICAL) — caught
- spec value altered / missing / extra → `SPEC_ROUND_TRIP` (MECHANICAL) — caught ×3
- orphan constant / inconsistent row → `FAST_LINT` (MECHANICAL) — caught ×2
- missing line-item → `FAST_LINT` (OMISSION) — caught
- missing IBCS notation / units → `IBCS_SUCCESS` (PURE_LOGIC) — caught ×2
- truncated axis / overlap / clipping → `VISUAL_INTEGRITY` (PURE_LOGIC) — caught ×3
- corrupt OOXML → `FILE_OPENS_CLEAN` (MECHANICAL) — caught

## Determinism

Each of the 18 cases was reviewed **200 times** under a fixed injected clock:
**3600 reviews** in total, every case yielding exactly **one** unique verdict digest
(`max_unique_digests = 1`). The gate is byte-for-byte reproducible — the same artifact
always yields the identical verdict, so a release decision is auditable and replayable.

## Coverage (necessary, not sufficient)

`pytest --cov=autofirm.output_review --cov-branch` over the package: **691 statements,
130 branches, 0 missed → 100.0% line, 100.0% branch** across **26 source files**
(`../_measured/coverage.json`). Per CLAUDE.md §3.6 this only proves the lines ran — the
mutation result below is the real evidence the tests have teeth.

## Mutation score (the acceptance signal)

The package is mutation-gated to **zero surviving mutants** by
`scripts/run_mutation_gate.py` (fail-closed grading: only `ok_killed` passes; any
survivor / timeout / suspicious exits 1). **All 25 source modules score 1.0**
(`../_measured/mutation_gate_summary.json`). Documented survivors closed during
hardening include `correction_loop_state` (9), `release_decision_gate` (2),
`visual_integrity_lint_check` (1); the remaining modules were hardened to zero
survivors with exact-message assertions (per-module commits `c70a366 … d2a6ba0`).
These are **cited gate results**, not a fresh campaign (CLAUDE.md §7.2).

## Interpretation

The gate is **measurably effective**, not merely fault-free: it catches **100%** of a
deliberately diverse, single-defect-attributable planted set across every must-block
defect class, with **zero** escapes and **zero** false positives, **deterministically**.
Against a literature baseline where ~86% of un-reviewed artifacts carry an error, an
independent gate with a measured ~0% escape rate is the difference between shipping a
defect to an owner/investor and blocking it at the seam.
