# BEST-PARTS — Carta State of Private Markets (2024-2025)

## ADOPT

- **Adopt the stage-benchmark medians as a LIVE-PULLED reference table**, not baked-in constants. The
  playbook should compare a client's proposed round (size, valuation, implied dilution) against the
  current Carta-style benchmark for its stage and flag out-of-range asks. Every displayed number
  carries its as-of date.
- **Adopt the post-money SAFE as the default early-stage instrument to model.** Post-money SAFE
  ownership is exactly `investment / post_money_cap` (e.g. $100K on a $10M cap -> 1.0%), which is a
  clean, unit-exact, testable formula — ideal for AutoFirm's deterministic dilution engine.
- **Adopt the instrument-mix data** (61% cap-only / 30% cap+discount / 8% discount-only / 1% neither,
  2024) to set sensible SAFE-structuring defaults and to validate that a recommended SAFE structure
  is market-normal.
- **Adopt observed per-round dilution medians (~16-25% by stage)** as the calibration target for the
  multi-round dilution / cap-table projection model.

## REJECT

- **Reject hard-coding any Carta number into engine logic.** These are time-varying, US-centric, and
  Carta-customer-selected. Treat them as a *refreshable benchmark feed*, never a magic constant
  (CLAUDE.md §3.9). A figure with no as-of date is rejected.
- **Reject US/Carta benchmarks as global truth** for non-US or non-Carta-typical clients (e.g.
  capital-intensive manufacturing rarely uses SAFEs) — must be industry/geo parameterized (B12).

## Concrete build implication

- **Component:** `dilution_engine` implementing exact post-money-SAFE conversion
  (`ownership = investment / post_money_cap`), priced-round dilution, and multi-round cap-table
  projection; plus `round_benchmark_check(stage, size, valuation)` against a dated benchmark table.
- **Test:** unit-exact property tests on SAFE conversion ($100K / $10M cap == 1.0000%), additivity of
  multiple SAFEs under post-money caps, and that benchmark checks reference a date-stamped table. A
  single arithmetic error here is unacceptable (CLAUDE.md §3.11).
