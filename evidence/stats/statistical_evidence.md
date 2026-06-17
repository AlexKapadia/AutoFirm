# Statistical evidence

Every figure below is produced by a real run of the suite and the end-to-end validation harness — nothing is hand-entered. Regenerate with `python evidence/generators/run_all.py`.

## Test suite

- **Tests:** 1,331 automated tests, all passing.
- **Total line coverage:** 99.64% over 4,703 statements and 870 branches (branch mode on).
- **Enforced gate:** line ≥ 90% / branch ≥ 85% in CI — exceeded with margin on every one of the 18 platform packages.

## Per-package coverage

Across the 18 platform packages, line coverage is min **98.89%**, median **100.00%**, mean **99.79%** — high and uniform, not propped up by any single package.

| Package | Line % | Branch % | Statements |
| --- | ---: | ---: | ---: |
| `access` | 100.00 | 100.00 | 239 |
| `artifacts` | 100.00 | 96.72 | 453 |
| `audit` | 99.38 | 97.44 | 323 |
| `comms` | 100.00 | 100.00 | 272 |
| `decisions` | 98.89 | 96.77 | 271 |
| `design_product` | 100.00 | 100.00 | 256 |
| `document_store` | 100.00 | 100.00 | 89 |
| `e2e` | 99.53 | 92.86 | 427 |
| `finance` | 100.00 | 100.00 | 294 |
| `flow` | 99.26 | 100.00 | 135 |
| `foundation` | 100.00 | 100.00 | 40 |
| `frontdoor` | 100.00 | 100.00 | 289 |
| `heartbeat` | 99.09 | 93.75 | 110 |
| `market_intel` | 100.00 | 98.08 | 304 |
| `memory` | 100.00 | 100.00 | 305 |
| `orchestration` | 100.00 | 100.00 | 182 |
| `org` | 100.00 | 100.00 | 369 |
| `substrate` | 100.00 | 100.00 | 344 |

![Per-package coverage](../graphs/coverage_by_package.png)

## End-to-end validation (public-data only)

- **Companies built + operated:** 4 diverse public-data companies (B2B SaaS, manufacturing, e-commerce retail, renewable energy).
- **Companies fully green:** 4 / 4.
- **Feature checks asserted correct:** 60 / 60 (100.0%).
- **Capability grid:** 15 platform features × 4 companies, every cell passing.

![E2E pass matrix](../graphs/e2e_pass_matrix.png)

![Company financials](../graphs/company_financials.png)

## Determinism

The full build+operate pipeline was run **5** times on identical inputs and produced **1** distinct output hash (SHA-256 `251faa8e19574f9d…`) — i.e. byte-for-byte reproducible, the property auditability depends on.

## Architecture

![Whole-system architecture](../diagrams/system_architecture.png)

![Build & operate flow](../diagrams/build_operate_flow.png)
