# BEST-PARTS — METR Time-Horizon Metric

## ADOPT
1. **Adopt "task time-horizon" as AutoFirm's task-decomposition sizing rule.**
   - *Why:* METR shows reliability decays predictably with task length; success at long horizons is a *capability frontier*, not a given. CLAUDE.md (global rule) already says "break work into tasks that each complete in <50% of remaining context." METR gives the empirical justification and a sizing heuristic.
   - *Build implication:* the COO decomposition engine (branch L2.A1/ORG) sizes each delegated subtask so its human-equivalent duration sits **well inside the model's measured 50% time horizon** — i.e., decompose until each unit is short enough to be reliably completed, then checkpoint (sources 08–10). This makes "decompose for reliability" a measured rule, not a vibe.

2. **Adopt time-horizon as a platform-evaluation metric in `evidence/` (branch A9).**
   - *Build implication:* AutoFirm runs its own 50%-time-horizon measurement on its golden task suite to quantify, with error bars, how long an autonomous run can be trusted before a human/checkpoint gate is mandatory — feeding §3.10 evidence charts (accuracy vs. task duration, with CIs).

3. **Adopt the doubling-trend as a forward-design assumption (not a relied-upon number).**
   - *Build implication:* architect the autonomy/handoff protocol to *raise* its per-run horizon as models improve (configurable horizon thresholds), rather than hard-coding today's ~1-2h ceiling.

## REJECT / DEFER
- **Reject** using the exact 110-min o3 figure or the logistic parameters as load-bearing constants until verified verbatim from arXiv:2503.14499 (flagged in SUMMARY). They are *illustrative*, not contract values.
- **Reject** the multi-year extrapolation/projection as a planning input — speculative; excluded from relied-upon claims per DEPTH-RUBRIC.
