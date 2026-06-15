# SUMMARY — Playwright: Live Browser-Driven E2E Testing Best Practices

## Full citation
- **(A) Title:** Best Practices — Playwright documentation
  - **URL:** https://playwright.dev/docs/best-practices
- **(B) Title:** Assertions (web-first / auto-retrying) — Playwright docs
  - **URL:** https://playwright.dev/docs/test-assertions
- **(C) Title:** Locators — Playwright docs · **URL:** https://playwright.dev/docs/locators
- **Author/Org:** Microsoft (Playwright team)
- **Year:** ongoing (current as of 2026); Playwright GA 2020
- **Venue/Publisher:** Microsoft / official Playwright documentation (primary tool authority)

## Questions it informs
- **L1.B13.5** (live, browser-driven E2E testing theory — PRIMARY for the Playwright-style approach)
- L1.B13.4 (keyboard/focus testing executes through the same live-browser harness)

## GRADE tier: High
Primary documentation from the tool's authors. Authoritative for the tool's semantics. Down-rate
slightly (Moderate-to-High) for being vendor docs rather than peer-reviewed; corroborated by the
general E2E-testing literature (test-pyramid, flake reduction). Treated High for tool-specific
mechanics, which are normative.

## Key claims (exact)

**Test user-visible behavior.** "Test your site the way your users use it." Avoid asserting on
implementation details (function names, CSS class internals) users never see.

**Use role-based, user-facing locators.** Prefer accessibility-role locators over CSS/XPath:
- recommended: `page.getByRole('button', { name: 'submit' })`
- discouraged: `page.locator('button.buttonIcon.episode-actions-later')`
Locators can be chained/filtered:
`page.getByRole('listitem').filter({ hasText: 'Product 2' }).getByRole('button', { name: 'Add to cart' })`
This couples tests to the accessibility tree, so a11y and testability reinforce each other.

**Web-first (auto-retrying) assertions.** Assertions like `expect(locator).toBeVisible()`
"automatically wait and retry until the expected condition is met," e.g.
`await expect(page.getByText('welcome')).toBeVisible()`. CONTRAST with the anti-pattern
`expect(await locator.isVisible()).toBe(true)`, which "returns immediately without waiting."
Corollary: AVOID hard waits (`page.waitForTimeout(...)`); rely on actionability + auto-waiting.

**Test isolation.** "Each test should be completely isolated from another test and should run
independently with its own local storage, session storage, data, cookies." Each test gets a fresh
browser context — "full isolation with near-zero overhead." `beforeEach` reduces repetition.

**Don't test third parties.** "Only test what you control." Mock externals with the Network API:
`await page.route('**/api/endpoint', route => route.fulfill({ status: 200, body: testData }))`.

**Cross-browser + CI.** Configure projects for Chromium, Firefox, WebKit; use sharding
(`--shard=1/3`) and parallelism; use the **Trace Viewer** for CI-failure debugging and **codegen**
to generate resilient role/text/test-id locators. Soft assertions (`expect.soft`) collect multiple
failures in one run.

## Reproducibility note
The getByRole locator pattern, web-first assertion auto-retry semantics, fresh-context isolation,
and the route-mocking snippet are quoted from playwright.dev/docs/best-practices and are
re-verifiable by running `npx playwright test`.
