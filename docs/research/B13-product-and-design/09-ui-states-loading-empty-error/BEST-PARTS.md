# BEST-PARTS — UI State Coverage

## What AutoFirm should ADOPT and why

1. **The four-state minimum (loading / empty / error / ideal) as a hard build contract.** ADOPT:
   every data-driven view MUST implement all four states (plus relevant edge variants). Build
   implication: this is the concrete definition of "all states (loading / empty / error / edge)"
   in the UI Definition-of-Done (CLAUDE.md §4.9.7); a view missing any state is a defect, and the
   evaluator agent (source 02) flags it as a Heuristic-1 violation.

2. **Each state gets its own live E2E test.** ADOPT: the Playwright suite (source 05) drives each
   state explicitly — mock a slow response to assert the loading/skeleton, an empty response to
   assert the empty-state CTA, a 500 to assert the error message + retry button works. Build
   implication: makes "nothing static" provable — the error retry button must actually re-fetch and
   reach the ideal state, asserted live.

3. **Empty states as onboarding, not blanks; error states with working retry.** ADOPT the rules:
   empty = explain + CTA; error = plain language + (optional code) + retry mechanism. Build
   implication: directly encodes Nielsen H5/H9 (source 01) into generated UI; the design-build
   playbook generates these as required, wired components — never placeholder text.

4. **Reusable state components, separated from content (atomic-design molecules).** ADOPT building
   loading/empty/error as standardized, reused components. Build implication: consistency (H4) +
   atomic-design reuse (source 06); one audited implementation per state, themed via tokens
   (sources 07/08).

## What AutoFirm should REJECT / DEFER

- **REJECT happy-path-only mockups passed off as features** — explicitly a defect (§2 CDO, §3.14).
  A UI proven only in the populated state is not done.
- **REJECT generic spinners where skeleton screens fit** — skeletons better satisfy perceived-
  performance and Core Web Vitals layout-stability (source 04, CLS) by reserving layout space.
- **DEFER exotic edge states** (offline, optimistic-update rollback) to client-specific need, but
  always cover the four-state minimum (generality without over-engineering, §3.9).

## Concrete build implication
The loading/empty/error/ideal four-state model is the operational definition of "build around real
data and EVERY state" (§3.14). It makes state coverage a checkable contract: every data-driven view
implements four reusable, token-themed, accessibility-compliant state components, and EACH state is
asserted by a live Playwright test (mock slow/empty/500 -> assert skeleton/CTA/retry). It binds
together Nielsen H1/H5/H9 (source 01), atomic design (source 06), tokens (07/08), Playwright (05),
and CLS (04) into one enforceable requirement.
