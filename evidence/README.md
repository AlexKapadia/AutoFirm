# evidence/ — AutoFirm showcase (analysis-only)

This folder is the **self-contained showcase** that proves and shows off how good
the platform is (CLAUDE.md §3.10): peer-reviewed-standard statistics, PNG +
interactive HTML graphs, and aesthetic black-&-white HTML + PNG flow diagrams per
component and for the whole system.

## Dependency boundary (binding)

`evidence/` is the **only** place analysis/plotting/diagram/eval libraries
(matplotlib, plotly, graphviz, cairosvg, scipy, statsmodels) may be imported.
They live exclusively in the `analysis` optional-dependency extra
(`pip install -e ".[analysis]"`) and are **fenced out of the runtime closure** by
the `import-linter` contract (`.importlinter`; ADR-001 §5). Runtime packages under
`src/autofirm/` must never import them — the `make test` contract gate fails the
build if they do.

## Status

Placeholder. Showcase artifacts (statistical evidence, graphs, flow diagrams) are
produced in later gates once platform components land. Nothing here is part of the
deployable runtime package.
