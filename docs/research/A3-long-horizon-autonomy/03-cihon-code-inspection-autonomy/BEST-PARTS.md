# BEST-PARTS — Cihon et al. Code-Inspection Autonomy Measurement

## ADOPT (high-value, directly actionable for AutoFirm)
1. **Adopt static inspection of the orchestration code as AutoFirm's autonomy-gating mechanism.**
   - *Why:* AutoFirm IS orchestrated Claude Code CLI sessions — the "orchestration code" (CLAUDE.md contract, settings.json, hooks, subagent specs, MCP/permission config) is exactly the artifact Cihon et al. say to inspect. We can compute a session's autonomy level *before* it runs, with no runtime cost or risk.
   - *Build implication:* a **pre-flight "autonomy linter"** that reads a session's config and emits `{impact, oversight}` scores + the derived level (sources 01/02). It runs as a hook/gate before any autonomous launch (ties to §4.8 watchdog + §4.9 gates). A property test: a config granting broad tool impact with no approval hook must lint to a level that the orchestrator refuses to auto-launch (fail-closed, §5.6).

2. **Adopt the two-axis (impact x oversight) scoring as the canonical level-derivation function.**
   - *Build implication:* `level = f(impact, oversight)` becomes the single, testable mapping reconciling sources 01 (named levels) and 02 (dimensions). Determinism test: identical config => identical level, every run (CLAUDE.md §5.5 determinism).

## REJECT / DEFER
- **Reject** relying on code inspection *alone* — it bounds *potential* autonomy, not *exhibited* behavior. Pair it with runtime telemetry (branch A6.3 governance-aware telemetry) for the full picture.
- **Defer** the AutoGen-specific scoring rubric; AutoFirm re-derives the rubric for the Claude Code CLI substrate (branch A5).
