# BEST-PARTS — Playwright E2E

## What AutoFirm should ADOPT and why

1. **Role-based locators as the standard for every E2E selector.** ADOPT `getByRole`/`getByLabel`/
   `getByText` over CSS/XPath. Build implication: the live-E2E suite (CLAUDE.md §4.9.6) that
   exercises "every button, input, link, flow" selects by accessibility role -> a11y (source 03)
   and E2E testability become the SAME work: an element that is untestable by role is usually an
   a11y defect. This is the single highest-leverage adoption.

2. **Web-first auto-retrying assertions; ban hard waits.** ADOPT `await expect(locator).toBe*()`
   exclusively; forbid `waitForTimeout`. Build implication: kills the #1 source of E2E flake, so
   the suite is deterministic enough to be a real CI gate (not a flaky one ignored by devs) —
   directly serves the §3.6 "tests with teeth" + determinism bar.

3. **Fresh-context test isolation.** ADOPT one browser context per test. Build implication: the
   generated client E2E suites are reproducible and parallelizable; satisfies the §5.5 "each test
   isolated" rule and lets the design-build playbook fan tests across CI shards.

4. **Assert real behavior + real-shaped data, mock only third parties.** ADOPT: drive the running
   app and assert each control "actually fires its real action and reaches the right state" (§3.14),
   mocking ONLY external APIs via `page.route`. Build implication: this is the mechanism that proves
   "nothing static" — a dead button fails because the asserted state transition never occurs.

5. **Happy-path AND failure/edge per control.** ADOPT: for every interactive element, test success
   and the error/edge path (mock a 500, empty response, slow response). Build implication: pairs
   with the loading/empty/error state contract (source 09) — each state gets a live assertion.

6. **Codegen + Trace Viewer in the agent loop.** ADOPT codegen to bootstrap resilient locators and
   Trace Viewer for the evaluator agent to diagnose CI failures. Build implication: tooling for the
   generator/evaluator split (§4.9.5) so a review agent can inspect a failed run, not guess.

## What AutoFirm should REJECT / DEFER

- **REJECT unit/component tests as sufficient for UI sign-off.** They are necessary but "not
  sufficient; the interface is proven by clicking through the running app" (§2 CDO). E2E is the
  gate.
- **REJECT brittle CSS/XPath selectors and hard waits** — they cause flake and false confidence.
- **DEFER visual-regression/screenshot-diff testing** to a complementary layer; behavioral E2E is
  the primary acceptance mechanism (screenshots support the evaluator critique, §4.9.5).

## Concrete build implication
Playwright role-based, auto-retrying, isolated E2E is the executable form of the §4.9.6 live test
suite: every button/input/link/flow asserted (happy + failure path) by accessibility role against
real-shaped data with only third parties mocked. It unifies a11y and testability (selectors = roles),
provides the green-E2E half of the UI Definition-of-Done, and supplies the evaluator agent its
diagnostic tooling (Trace Viewer).
