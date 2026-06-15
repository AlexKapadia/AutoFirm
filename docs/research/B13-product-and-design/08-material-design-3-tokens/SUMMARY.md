# SUMMARY — Material Design 3: Tiered Design Tokens & System Foundations

## Full citation
- **Title:** Material Design 3 — Design tokens / Foundations (Accessibility, Color system)
- **Author/Org:** Google (Material Design team)
- **Year:** Material 3 launched 2021; ongoing (Material 3 Expressive update 2025)
- **Venue/Publisher:** Google / m3.material.io (open design system, primary authority)
- **URL:** https://m3.material.io/foundations/design-tokens ·
  https://m3.material.io/foundations/overview/principles (accessibility) ·
  https://m3.material.io/styles/color/system/overview (color)

## Questions it informs
- **L1.B13.2** (design-systems / token architecture — PRIMARY worked example of a tiered token
  system at scale)
- L1.B13.4 (accessibility-by-default color roles — supporting)

## GRADE tier: Moderate
A mature, production design system from a major vendor (Google) used at planetary scale; the
canonical worked example of three-tier tokens. Down-rate from High (vendor design system, not a
neutral standard); up-rate for scale, completeness, and explicit accessibility defaults. Corroborates
the DTCG format (source 07) with a concrete, deployed implementation.

## Key claims (exact)

**What design tokens are (Material).** "Design tokens store style values like colors and fonts so
the same values can be used across designs, code, tools, and platforms."

**Three-tier token architecture.**
1. **Reference tokens** — the raw, literal palette/values (e.g. a specific blue, "md.ref.palette.
   primary40"). The full set of possible values.
2. **System tokens** (semantic) — meaning-based roles that point AT reference tokens (e.g.
   "primary", "on-primary", "surface", "error"). "Component Tokens point to the semantic System
   Tokens (e.g. 'the primary color') rather than the literal Reference Tokens (e.g. 'blue'), so the
   entire application's UI updates automatically, consistently, and correctly."
3. **Component tokens** — token values scoped to a specific component (e.g. a filled-button's
   container color), which point to system tokens.

**Color system.** "Five Key Colors" seed the system; each generates a Tonal Palette (tones 0-100);
semantic Color Roles (primary/secondary/tertiary/neutral, plus container/surface/on-* roles) map to
specific tones. The "on-" roles (on-primary, on-surface) are paired to guarantee legible foreground/
background contrast.

**Accessibility by default.** "Accessibility by default is a core design value for Material"; the
token-based theming model ships "WCAG 2.1 AA accessibility defaults" — the on-color roles are
designed to meet contrast minimums against their paired surfaces by construction.

## Reproducibility note
The reference/system/component three-tier model, the "component tokens point to system tokens, not
reference tokens" rule, the five-key-color/tonal-palette derivation, and the WCAG-AA-default claim
are stated at m3.material.io/foundations/design-tokens and the color/accessibility pages.
