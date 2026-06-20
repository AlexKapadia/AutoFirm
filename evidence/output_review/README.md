# evidence/output_review/ — the human-output-review gate, proven & shown off

Self-contained, analysis-only showcase (CLAUDE.md §3.10) for AutoFirm's
**output-review lane** — the independent, fail-closed gate that stands between the
artifact builders and any human (owner / CEO / investor) and refuses to deliver
anything until a multi-pass review has proven it error-free. Every number here is
**measured** by running the real `autofirm.output_review` gate over a labelled
**synthetic** golden set (no real data — CLAUDE.md §3.12); nothing is hand-typed.

## Headline

> Un-reviewed human spreadsheets carry an error **~86%** of the time while their
> authors self-estimate only **~18%** (Panko; B16 `SYNTHESIS.md` §A.1). The
> independent gate's **measured escape rate is 0 / 14 = 0.0%**, with **0 / 4** false
> positives, **100%** detection on every must-block Panko-Halverson defect class, and
> byte-identical verdicts over **3,600** repeated reviews. That ~86% → ~0% gap is the
> case for the gate.

## Folder map

```
golden_set/   the efficacy harness + labelled synthetic corpus (deliverable 1)
  ooxml_file_open_probe.py        real, deterministic OOXML open probe (stdlib only)
  synthetic_golden_corpus.py      18 labelled cases: 14 planted defects + 4 controls
  run_efficacy_harness.py         runs the REAL gate; writes measured JSON + CSV
  summarise_mutation_gate.py      cites the 0-survivor mutation gate per module
_measured/    measured/cited data the stats + graphs read (no magic constants)
  efficacy_metrics.json  per_case.csv  coverage.json  mutation_gate_summary.json
stats/        METHODOLOGY.md + RESULTS.md — peer-reviewed-standard numbers
graphs/       5 graphs, each PNG (matplotlib) + interactive HTML (plotly)
diagrams/     4 black-&-white flow diagrams, each PNG + self-contained HTML
requirements-analysis.txt   analysis-only deps (NEVER runtime — §3.10 boundary)
```

## What each figure / stat shows

| Artifact | Shows |
| --- | --- |
| `graphs/detection_by_panko_class.{png,html}` | Detection rate per Panko class — must-block classes at 100%, Wilson-CI whiskers, EUREKA flagged out-of-floor |
| `graphs/escape_vs_human_baseline.{png,html}` | ~0% gate escape & false-positive vs the ~86% un-reviewed-human error baseline (~18% self-estimate) |
| `graphs/verdict_determinism.{png,html}` | 1 unique verdict digest per case over 3,600 repeated reviews |
| `graphs/coverage_line_branch.{png,html}` | 100% line + branch coverage vs the 90 / 85 CI gates |
| `graphs/mutation_score_by_module.{png,html}` | Per-module mutation score — 25 modules all 1.0, 0 survivors |
| `diagrams/gate_composition.{png,html}` | The gate composing 7 independent checks → one derived ReviewVerdict (false-pass guard) |
| `diagrams/correction_send_back_loop.{png,html}` | The bounded correction send-back / re-review loop |
| `diagrams/release_admission_seam.{png,html}` | Release authority + delivery admission guard (fail-closed refusal) |
| `diagrams/system_flow_whole.{png,html}` | Whole-system flow: builder → artifact → gate → verdict → release → librarian → human |
| `stats/METHODOLOGY.md` / `stats/RESULTS.md` | How every number was produced / the measured results |

## Measured results (read from `_measured/`)

- **Escape / false-pass rate:** 0 / 14 = **0.000** (Wilson 95% CI [0.000, 0.215]).
- **False-positive rate:** 0 / 4 = **0.000** (Wilson 95% CI [0.000, 0.490]).
- **Detection by Panko class:** MECHANICAL 7/7, PURE_LOGIC 6/6, OMISSION 1/1 — all
  **100%**, each caught by the correct check (EUREKA is out of the deterministic floor).
- **Determinism:** 18 cases × 200 reviews = **3,600** reviews, **1** unique digest per case.
- **Coverage:** **100.0%** line, **130/130 = 100.0%** branch across 26 source files.
- **Mutation:** **0** survivors, 25 modules at score **1.0** (cited gate result).

## Regenerate

```bash
# 1. measured numbers — needs only the stdlib + the runtime autofirm package
python evidence/output_review/golden_set/run_efficacy_harness.py
python evidence/output_review/golden_set/summarise_mutation_gate.py
# (coverage.json) — the package coverage report the graphs read:
pytest tests/output_review --cov=autofirm.output_review --cov-branch \
       --cov-report=json:evidence/output_review/_measured/coverage.json

# 2. graphs + diagrams — needs the analysis-only libraries
pip install -r evidence/output_review/requirements-analysis.txt
python evidence/output_review/graphs/render_all_graphs.py
python evidence/output_review/diagrams/render_all_diagrams.py
```

## Dependency boundary (binding — CLAUDE.md §3.10)

The analysis / plotting / diagram libraries (matplotlib, plotly, scipy, statsmodels)
live **only** in `requirements-analysis.txt` and are imported **only** by the scripts
in this folder — **never** by any runtime module under `src/autofirm/`. The
import-linter contract *"Runtime code must not import analysis-only libraries"* stays
**2 kept / 0 broken**. The harness itself uses only the standard library plus the
runtime `autofirm` package, so the measured numbers reproduce without any plotting
dependency. Flow diagrams are drawn with matplotlib (the Graphviz `dot` binary is not
available on the build host), in strict black & white. Nothing here ships in the
deployable runtime package.
