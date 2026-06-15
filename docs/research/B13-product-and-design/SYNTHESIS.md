# SYNTHESIS — B13 Product & Design Capability for Client Builds (Layer 1)

> Covers L1.B13.1-.5. Sources are the numbered folders in this branch. Feeds **L2.B13** (the
> AutoFirm design-build + live-E2E playbook). All claims meet DEPTH-RUBRIC source-count + exact-
> citation rules; every source is graded with up/down-rate reasoning in its `SUMMARY.md`.

## 1. The five sub-questions and the surveyed alternative space

**L1.B13.1 Design-research / competitive-teardown method.** Alternatives surveyed: (a) heuristic
evaluation (expert review vs. a rubric); (b) moderated/unmoderated user testing; (c) competitive/
comparative usability benchmarking; (d) ad-hoc "look at competitors" (the AI-slop default). CHOSEN:
**structured heuristic evaluation (sources 01+02)** as the teardown method — a 3-5 independent-
evaluator panel rating category-leading products against Nielsen's 10 heuristics, severity-scored
0-4, distilling PRINCIPLES (not pixels). Rejected (d) as unstructured; user testing (b) deferred to
post-launch (no real users at design time).

**L1.B13.2 Design-systems & token theory.** Alternatives: component hierarchy = (a) atomic design,
(b) flat component libraries, (c) ad-hoc; token format = (a) W3C DTCG JSON, (b) Material 3 tiers,
(c) framework-proprietary (Tailwind config, CSS vars only), (d) hard-coded values. CHOSEN: **atomic
design (06)** for hierarchy + **DTCG JSON (07)** as the interoperable format + **Material 3's three-
tier reference/semantic/component model (08)** as the layering, with **accessibility-by-construction
on-color pairings**. Rejected hard-coded values (defeats theming/a11y/adherence gate) and adopting
any single library's VISUAL identity (plagiarism, §3.14).

**L1.B13.3 UX heuristics, interaction design & state coverage.** Alternatives for the quality lens:
(a) Nielsen's 10 heuristics, (b) Shneiderman's 8 golden rules, (c) ISO 9241-110 dialogue principles,
(d) gut feel. CHOSEN: **Nielsen's 10 (01)** as the general, factor-analysis-grounded rubric (others
noted as compatible supplements). State coverage CHOSEN: the **four-state minimum loading/empty/
error/ideal + edge (09)**, which operationalizes Heuristic 1.

**L1.B13.4 Accessibility + performance budgets.** Accessibility: WCAG 2.2 is the sole normative
standard; level A (too weak) / AA (chosen) / AAA (too strict as default). CHOSEN: **WCAG 2.2 AA (03)**
with exact thresholds (24x24px targets, 4.5:1 / 3:1 contrast), automated + manual. Performance:
Core Web Vitals vs. legacy proxies (PageSpeed score, TTFB). CHOSEN: **Core Web Vitals (04)** —
LCP<=2.5s, CLS<=0.1, INP<=200ms at p75. FID rejected (deprecated March 2024).

**L1.B13.5 Live E2E testing.** Alternatives: (a) Playwright, (b) Cypress, (c) Selenium/WebDriver,
(d) unit/component tests only. CHOSEN: **Playwright-style role-based, auto-retrying, isolated E2E
(05)**. Cypress is a viable peer (defer as an alternative engine); Selenium rejected (no native auto-
wait, flakier); unit-only rejected (CDO: "the interface is proven by clicking through the running
app"). Role-based locators chosen because they UNIFY a11y (03) and testability.

## 2. The integrated B13 picture (how the sources compose)

```
COMPETITIVE TEARDOWN (01+02: heuristic eval, 3-5 evaluators, severity 0-4)
        | distils principles, not pixels
        v
DESIGN BRIEF  ->  DESIGN TOKENS (07 DTCG format / 08 three-tier ref->semantic->component,
        |                         on-color a11y-by-construction, Oklch palettes)
        |                                   |
        v                                   v consumed at the atom level
ATOMIC DESIGN (06: atoms->molecules->organisms->templates->pages)
        | templates encode EVERY STATE
        v
STATE COVERAGE (09: loading/empty/error/ideal + edge)  <- Nielsen H1/H5/H9 (01)
        |
        v   built bottom-up by fan-out UI agents, reviewed by evaluator agents (02)
QUALITY GATES (the UI Definition-of-Done, CLAUDE.md 4.9.7):
   - WCAG 2.2 AA (03): 24x24px, 4.5:1/3:1, keyboard/focus, automated + MANUAL
   - Core Web Vitals (04): LCP<=2.5s / CLS<=0.1 / INP<=200ms at p75
   - Live E2E green (05): every button/input/link/flow, role-based, happy + failure path
   - Token adherence (07/08): no hard-coded values (lint)
   - All states present (09); nothing static (05 asserts real behavior)
```

## 3. Concrete recommendation for L2.B13 (build-relevant, general, cited)

AutoFirm's **design-build + live-E2E playbook** should be:

1. **Teardown by heuristic evaluation** — 3-5 independent evaluator agents rate category-leading
   competitors against Nielsen's 10 (01), severity 0-4 (02), using the Poisson coverage estimate
   `Found(i)=N(1-(1-L)^i)`, L~=0.34 (02) as the stop-rule; output a PRINCIPLES brief (never a clone).
2. **Token-first design system** — emit a DTCG JSON file (07) with Material-3-style three tiers
   (reference->semantic->component, 08); generate on-color pairings meeting WCAG 4.5:1/3:1 (03) BY
   CONSTRUCTION; Oklch palettes (07) defeat random-hex AI-slop.
3. **Atomic component build** (06) bottom-up, fanned out across UI agents; templates carry every
   state (09).
4. **Two-number quality gate** — WCAG 2.2 AA (03) + Core Web Vitals p75 (04), both CI-enforced and
   charted in `evidence/`.
5. **Live Playwright E2E (05)** as the acceptance mechanism — role-based selectors (unifying a11y +
   testability), auto-retrying assertions (no flake/hard waits), fresh-context isolation, each of the
   four states (09) asserted (mock slow/empty/500), every control proven to fire its real action.
6. **Evaluator/generator split** (02) on a design heartbeat (§4.9.4-5): different agents judge;
   severity-3/4 findings block the Definition-of-Done.

**Generality (DEPTH-RUBRIC §5).** Nothing here is industry-specific: heuristics, atomic design,
DTCG tokens, WCAG AA, Core Web Vitals, and Playwright apply to ANY client UI across the B12 panel
(SaaS, fintech, healthcare, marketplace, DTC, etc.). Industry-specific heuristic extensions and AAA
criteria are DEFERRED to client demand, not baked in.

## 4. Source-count / rubric compliance
- **Safety/correctness-critical numbers** (WCAG 24x24px/4.5:1/3:1; CWV 2.5s/0.1/200ms@p75): each
  carries the primary normative source (W3C / Google web.dev) plus the exact locator; >=2-3 corroborating
  searches/fetches performed. WCAG and CWV are single-authority NORMATIVE standards (the standard IS
  the source of record) — corroboration is by the official spec + the official measurement doc.
- **Important architecture claims** (token tiers, atomic hierarchy, heuristic-eval panel size): >=2
  independent sources each (DTCG + Material 3 for tokens; Frost + atomic adoption for hierarchy;
  Nielsen-Landauer CHI paper + NN/g method for evaluator count).
- **Exact citations + formulae** reproduced verbatim with locators; no fabricated source/number.

## 5. Open items handed to L2.B13 / QA
- Pick the E2E engine winner (Playwright vs. Cypress) on a golden set via branch-per-experiment
  (recommendation: Playwright, per 05).
- Decide the automated a11y scanner(s) (axe-core / Lighthouse / Pa11y) and the manual-test checklist
  scope for the WCAG AA "manual" half.
- Confirm DTCG 2025.10 tooling maturity (Style Dictionary support) before committing the token pipeline.
