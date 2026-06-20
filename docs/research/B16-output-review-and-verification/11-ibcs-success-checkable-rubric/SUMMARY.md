# 11 — IBCS Standards v1.2 — the SUCCESS formula as an objective, checkable rubric

- **Author / org:** IBCS Association; Rolf Hichert & Jürgen Faisst.
- **Year:** v1.2 (book ISBN 9783982141428).
- **Link:** https://www.ibcs.com/ibcs-standards-1-2/
- **Tier:** High — primary published standard for business-report/deck conformance.

## Faithful structured summary

IBCS makes deck/report quality **objectively checkable** by decomposing it into the **SUCCESS**
formula — seven rule groups, **98 individual rules** evenly distributed across the groups:

- **S** AY — convey a clear message (action/message titles).
- **U** NIFY — apply **semantic notation** (a fixed visual vocabulary for actual / plan / forecast /
  variance / previous-year, so the same concept always looks the same).
- **C** ONDENSE — increase information density.
- **C** HECK — **ensure visual integrity** (no truncated/misleading axes, no distortion).
- **E** XPRESS — choose the proper visualisation (message-type -> chart-family).
- **S** IMPLIFY — avoid clutter (no chartjunk/3D/decoration).
- **S** TRUCTURE — organise content (MECE).

Because the rules are enumerated and notation is fixed, **conformance is machine-checkable** rather
than a matter of taste — the **CHECK** group in particular is a deterministic visual-integrity audit.

## Best parts to take (for our gate) and why

1. **Deck review can be deterministic too** — IBCS gives us a closed, enumerated rule set so our
   `IBCS_SUCCESS` and `VISUAL_INTEGRITY` checks are standard-grounded lint, not subjective opinion.
2. **CHECK = visual-integrity floor** (truncated/misleading axes) is a *blocking* deterministic check
   — a misleading axis shown to an investor is a correctness defect, not a style nit.
3. **UNIFY (semantic notation) is per-company config**, keeping the check general (CLAUDE §3.9): the
   gate validates conformance to the company's declared notation, never a hard-coded palette.
4. **EXPRESS (message-type -> chart-family)** lets us deterministically reject mismatches (e.g. a pie
   used for a time series), echoing Zelazny in B15.
