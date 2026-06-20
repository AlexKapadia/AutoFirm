# evidence/ — AutoFirm showcase (analysis-only)

This folder is the **self-contained showcase** that proves and shows off how good
the platform is (CLAUDE.md §3.10): peer-reviewed-standard statistics, PNG +
interactive HTML graphs, and aesthetic black-&-white HTML + PNG flow diagrams per
component and for the whole system. **Every number is real** — produced by a real
run of the test suite and the end-to-end validation harness, never hand-entered.

## What's here

```
generators/   Analysis-only scripts that produce every artifact (≤300 lines each)
graphs/       PNG (matplotlib) + interactive HTML (plotly) charts
diagrams/     B&W flow diagrams, each as PNG + standalone HTML
stats/        statistical_evidence.md — the peer-reviewed-standard numbers page
_raw/         collected real evidence (evidence_data.json) the generators consume
```

| Artifact | What it shows |
| --- | --- |
| `graphs/coverage_by_package.png` / `.html` | Line + branch coverage of all 18 packages vs the 90/85 gates |
| `graphs/e2e_pass_matrix.png` / `.html` | 15 features × 4 public companies — every cell asserted correct |
| `graphs/company_financials.png` / `.html` | Net income / total assets / DCF value the engine produced |
| `diagrams/system_architecture.png` / `.html` | Whole-system architecture — 26 packages in flow order |
| `diagrams/build_operate_flow.png` / `.html` | Per-company build → operate → asserted-result flow |
| `diagrams/activation_lifecycle_flow.png` / `.html` | `autofirm up` — converge → compose → supervise → prove |
| `diagrams/output_review_gate_flow.png` / `.html` | Fail-closed output review — checks → derived verdict → deliver/send-back |
| `diagrams/cockpit_control_plane_flow.png` / `.html` | Operator cockpit — bind live platform → pure projections → TUI → audited commands |
| `stats/statistical_evidence.md` | Tests, coverage stats, the e2e fraction, determinism proof |

## Headline numbers (real)

- **1,331** automated tests, all passing; **99.64%** line coverage (branch mode).
- **4** diverse public-data companies built **and** operated end-to-end.
- **60 / 60** feature checks asserted correct (15 capabilities × 4 companies).
- Build+operate is **byte-for-byte deterministic** (5 runs → 1 output hash).

## Regenerate

```bash
pip install -e ".[analysis]"          # matplotlib / plotly / scipy / statsmodels
python -m pytest tests/ --cov=autofirm --cov-report=json:evidence/_raw/coverage.json
python evidence/generators/run_all.py # rebuilds every graph, diagram and the stats page
```

## Dependency boundary (binding)

`evidence/` is the **only** place analysis/plotting/diagram libraries (matplotlib,
plotly, graphviz, cairosvg, scipy, statsmodels) may be imported. They live
exclusively in the `analysis` optional-dependency extra and are **fenced out of the
runtime closure** by the `import-linter` contract (ADR-001 §5). Runtime packages
under `src/autofirm/` never import them. Flow diagrams are rendered with matplotlib
(not the graphviz `dot` binary, which is unavailable on the build host) for exact,
clean B&W output. Nothing here is part of the deployable runtime package.
