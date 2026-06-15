# BEST-PARTS — Nielsen's 10 Usability Heuristics

## What AutoFirm should ADOPT and why

1. **The 10 heuristics as a machine-checkable design-review rubric.** ADOPT all 10 as the
   evaluator agent's scoring axes for every client UI the design-build playbook (L2.B13) produces.
   Build implication: the generator/evaluator split (CLAUDE.md §4.9 step 5) gets a concrete,
   non-vibe rubric — the evaluator agent rates each screen against H1–H10, producing a structured
   defect list, not a vibe verdict.

2. **H1 Visibility of system status → ties directly to state coverage.** ADOPT as the formal
   justification for the "loading / empty / error / edge" state requirement (CLAUDE.md §3.14,
   §4.9.7). Build implication: a screen with no loading/feedback state is an H1 violation and a
   UI-Definition-of-Done failure — testable.

3. **H5 Error prevention + H9 recover-from-errors → wired-error-state contract.** ADOPT as the
   spec for AutoFirm's "nothing static" rule: every form/control must have prevention (validation)
   and recovery (plain-language error + retry). Build implication: drives the error-state E2E
   tests in source 05/09.

4. **H4 Consistency and standards → design-token + component-inventory enforcement.** ADOPT as
   the rationale linking heuristics to the design-system work (sources 06/07/08): consistency is
   not aesthetic preference, it is a usability heuristic. Build implication: token adherence
   (no hard-coded values) is a measurable H4 gate.

5. **H8 Aesthetic and minimalist design → the anti-AI-slop bar, but evidence-based.** ADOPT to
   reframe "no vibe-coding" (CLAUDE.md §3.14) as a usability requirement: irrelevant decoration
   competes with relevant content. Build implication: the design brief justifies restraint with
   H8, not taste.

## What AutoFirm should REJECT / DEFER

- **REJECT treating heuristics as a sufficient acceptance gate.** Heuristic evaluation finds
  *likely* problems via experts; it does not replace live behavioural E2E testing (source 05) or
  real-user data. Adopt as a *review* layer, not the DoD by itself.
- **DEFER domain-specific heuristic extensions** (e.g. e-commerce, gaming heuristic sets) until a
  client industry demands them; the 10 are the general, industry-agnostic core (generality, §3.9).

## Concrete build implication
Nielsen's 10 are the canonical, general rubric for the **evaluator agent** in the design-build
loop. They convert "is this UI good?" into 10 testable axes and directly justify three platform
contracts: full state-coverage (H1), wired error handling (H5/H9), and token-driven consistency
(H4). They are the lens the competitive-teardown method (source 02) applies.
