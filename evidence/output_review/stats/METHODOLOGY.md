# Methodology — output-review gate efficacy evidence

This page states *how* every number in [`RESULTS.md`](RESULTS.md) was produced, to a
peer-reviewed standard (CLAUDE.md §3.10). Nothing here is hand-typed: the harness
runs the **real production gate** over a labelled synthetic corpus and writes the
measurements to [`../_measured/`](../_measured/), which the results page and every
graph read directly.

## 1. What is under test

The `autofirm.output_review` gate: an **independent**, fail-closed evaluator that
composes **seven deterministic checks** over a built artifact and returns one typed
`ReviewVerdict` whose `passed` flag is *derived* from the findings (the false-pass
guard — a green-but-wrong verdict is structurally impossible). The seven checks and
their Panko-Halverson defect class:

| Check | Defect class(es) | What it catches |
| --- | --- | --- |
| `ACCOUNTING_IDENTITY` | PURE_LOGIC | `A != L + E`, exact to the unit |
| `NUMERIC_RECOMPUTE` | MECHANICAL | declared figure != independent recomputation |
| `SPEC_ROUND_TRIP` | MECHANICAL | a spec value altered / dropped / unexpectedly added |
| `FAST_LINT` | MECHANICAL, OMISSION | orphan constant / inconsistent row / missing line-item |
| `IBCS_SUCCESS` | PURE_LOGIC | missing IBCS notation / unlabelled units |
| `VISUAL_INTEGRITY` | PURE_LOGIC | truncated axis / overlap / clipping |
| `FILE_OPENS_CLEAN` | MECHANICAL | corrupt OOXML that will not open without repair |

## 2. Why this matters — the motivating gap

The whole lane exists because **self-review does not work**. Panko's spreadsheet-error
research (B16 `SYNTHESIS.md` §A.1) finds that operational spreadsheets contain errors
in **~86%** of cases, while their authors *self-estimate* an error rate of only
**~18%**. Acceptance therefore can never come from the builder's own assessment; an
**independent** evaluator must grade every artifact against a deterministic rubric
before it reaches a human. The headline result is the gate's **measured ~0% escape
rate** against that **~86%** un-reviewed-human baseline.

## 3. The corpus (synthetic golden set — CLAUDE.md §3.12)

`golden_set/synthetic_golden_corpus.py` builds **18 labelled cases**, each carrying a
ground-truth label (control vs. which defect class/check was planted):

- **14 planted-defect cases** — exactly one defect per relevant check, spanning every
  must-block Panko class. Each model case starts from fully-clean fact bundles and
  has **one** bundle broken, so the defect is attributable to a single check (no
  confounding). The corrupt-OOXML case keeps every fact bundle clean and breaks only
  the **bytes on disk**.
- **4 known-good controls** — one clean financial model (×2 with different figures),
  one clean slide deck, one clean business document — so a false positive on **any**
  artifact kind would surface.

All figures, labels, and files are **synthetic**. No real PII, client data, or deal
documents are used anywhere (CLAUDE.md §3.12). The files the `FILE_OPENS_CLEAN` check
reads are minimal but **structurally real** OOXML containers (a ZIP carrying the
mandatory `[Content_Types].xml` part); the planted-corrupt file is genuine garbage
bytes. The probe (`ooxml_file_open_probe.py`) **actually opens the bytes** — so the
file-opens detection is a real measurement, not a stubbed boolean.

**EUREKA is deliberately excluded from the must-block set.** Wrong-domain-model
defects are the sole class the deterministic floor provably cannot reach (B16
`SYNTHESIS.md` §3/§4 route them to an *advisory* model layer). Planting EUREKA as
must-block would misrepresent the floor, so it is reported as out-of-floor, not as a
miss.

## 4. Metrics (all computed from the verdicts)

- **Defect-detection rate, per Panko class** = blocked / planted, within each class.
  A planted case is "blocked" iff `verdict.passed is False`. We additionally confirm
  the **correct check raised the correct class** (`detected_by_correct_check`), so a
  block is never credited to an incidental finding.
- **Escape / false-pass rate** = planted defects the gate let `pass` / total planted.
  Target **0** — an escape is the precise failure mode the lane prevents.
- **False-positive rate** = controls the gate blocked / total controls. Target **0**.
- **95% confidence intervals**: the **Wilson score interval** (`run_efficacy_harness.py`,
  pure-stdlib implementation) is used rather than the normal/Wald approximation,
  because the rates sit at the boundaries (0 and 1) where Wald intervals are
  degenerate. The interval width reflects the finite golden-set size honestly.

## 5. Determinism (CLAUDE.md §3.11)

Each case is reviewed **200 times** under a **fixed injected clock** (the gate never
reads the wall clock). For every run the canonical verdict JSON is SHA-256 hashed;
the case is deterministic iff all 200 runs yield **one** unique digest. The harness
reports the max unique-digest count across all cases (must be 1).

## 6. Coverage & mutation (corroborating evidence)

- **Coverage** is measured directly: `pytest --cov=autofirm.output_review --cov-branch`
  → [`../_measured/coverage.json`](../_measured/coverage.json). Coverage is *necessary
  but not sufficient* (it only proves lines ran, never that a wrong answer is caught).
- **Mutation** is the real acceptance signal. The package is gated to **zero surviving
  mutants** by `scripts/run_mutation_gate.py` (fail-closed: only `ok_killed` counts;
  any survivor exits 1). [`summarise_mutation_gate.py`](../golden_set/summarise_mutation_gate.py)
  **cites** that gate result per module (it does **not** launch a fresh campaign —
  forbidden by the standing rules here) from the per-module hardening commits.

## 7. Reproduce

```bash
pip install -r evidence/output_review/requirements-analysis.txt   # graphs/diagrams only
python evidence/output_review/golden_set/run_efficacy_harness.py   # measured numbers
python evidence/output_review/golden_set/summarise_mutation_gate.py
python evidence/output_review/graphs/render_all_graphs.py          # PNG + HTML graphs
python evidence/output_review/diagrams/render_all_diagrams.py      # B&W flow diagrams
```

The harness needs only the standard library + the runtime `autofirm` package; the
analysis libraries are required **only** to render the graphs and diagrams.
