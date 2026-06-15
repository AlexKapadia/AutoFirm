# BEST-PARTS — WCAG 2.2

## What AutoFirm should ADOPT and why

1. **WCAG 2.2 Level AA as the binding, testable accessibility bar.** ADOPT AA (not just A) as the
   UI Definition-of-Done floor (CLAUDE.md §4.9.7). Build implication: every client UI must pass all
   2.1 AA criteria PLUS the new 2.2 AA criteria (2.4.11, 2.5.7, 2.5.8, 3.3.8). This is a concrete,
   normative gate, not aspiration.

2. **The exact numeric thresholds as automated-test assertions.** ADOPT verbatim:
   - Target size >= **24x24 CSS px** (2.5.8) -> automated check on every interactive element.
   - Text contrast >= **4.5:1** (3:1 large) (1.4.3); non-text/UI contrast >= **3:1** (1.4.11).
   - Keyboard focus never entirely obscured (2.4.11); focus visible (2.4.7).
   Build implication: these feed axe-core/Lighthouse automated scans in CI AND the design-token
   color system (sources 07/08) must be generated to satisfy 4.5:1 / 3:1 by construction.

3. **Automated + MANUAL coverage split.** ADOPT the §3.14 mandate: automated scanners (axe-core,
   Lighthouse, Pa11y) catch ~30-50% of issues; manual keyboard/focus/screen-reader testing covers
   the rest (2.4.11 focus order, 3.3.8 auth, cognitive criteria). Build implication: the a11y gate
   = automated CI scan + a scripted manual checklist driven through the live app (links to source 05
   Playwright keyboard-navigation tests).

4. **3.3.8 Accessible Authentication as a design constraint for client auth flows.** ADOPT: no
   client login may require a cognitive-function test without an alternative. Build implication:
   constrains the auth UX the design-build playbook generates (e.g. allow password managers/paste,
   provide WebAuthn).

5. **Backward-compatibility + removal of 4.1.1 Parsing.** ADOPT the current 2.2 criterion list
   exactly; do NOT test against the obsolete 4.1.1. Build implication: keeps the a11y rule set
   current and avoids false failures.

## What AutoFirm should REJECT / DEFER

- **REJECT automated-scan-only conformance.** Automated tools verify a minority of criteria;
  claiming "WCAG AA" on a scanner pass alone is misrepresentation. Manual testing is mandatory.
- **DEFER AAA criteria** (2.4.12, 2.4.13, 3.3.9) as default — adopt AA; offer AAA only when a client
  (e.g. public-sector, healthcare from the B12 panel) requires it (generality + don't over-engineer).

## Concrete build implication
WCAG 2.2 AA is the normative accessibility contract for every client UI: a fixed set of testable
criteria with exact numbers (24x24px, 4.5:1, 3:1) that become CI scan assertions, design-token
generation constraints (contrast by construction), and a manual keyboard/screen-reader checklist
in the live-E2E gate. It is the non-negotiable half of the UI Definition-of-Done (the other half =
Core Web Vitals, source 04).
