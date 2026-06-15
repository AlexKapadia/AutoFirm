# BEST-PARTS — W3C Design Tokens Format Module

## What AutoFirm should ADOPT and why

1. **DTCG JSON as the single source of truth for every client design system.** ADOPT the
   tool-neutral token file as the canonical design-decision store. Build implication: the design
   brief (CLAUDE.md §4.9.2) emits a DTCG token file; UI-build agents consume it; nothing in code
   hard-codes a color/spacing/type value -> "design-token adherence (no hard-coded values)"
   (§4.9.7) becomes a machine-checkable lint (grep for raw hex/px = violation).

2. **Token aliasing for a semantic/theming layer.** ADOPT reference tokens -> semantic aliases
   (mirrors Material 3's tiers, source 08). Build implication: enables per-client multi-brand
   theming and dark mode by swapping one layer, and lets AutoFirm generate accessible palettes
   (contrast 4.5:1 / 3:1 from source 03) at the semantic layer by construction.

3. **The interoperability pipeline (Figma -> tokens -> CSS/native via Style Dictionary).** ADOPT to
   eliminate design-to-code drift. Build implication: a deterministic, auditable transform from the
   design decision to shipped CSS custom properties — fits AutoFirm's determinism + provenance bars
   (the token file is the audited artifact, the generated CSS is reproducible from it).

4. **Modern color (Oklch / Display P3 / CSS Color 4).** ADOPT for perceptually-uniform color scales,
   which make generating accessible, evenly-stepped palettes tractable. Build implication: feeds the
   anti-AI-slop "real type + spacing + color scale" requirement (§3.14) with a principled color
   space, not ad-hoc hex picks.

## What AutoFirm should REJECT / DEFER

- **REJECT hard-coded style values anywhere below the token layer** — the entire point is one source
  of truth; raw values defeat theming, a11y-by-construction, and the adherence gate.
- **DEFER reliance on the spec as "normative W3C standard."** It is a Community Group Report, not a
  Recommendation — adopt the FORMAT (broad tooling support) but do not overstate its standing; if a
  client tool lags, use Style Dictionary's compatibility layer.

## Concrete build implication
The DTCG JSON token format is the contract that makes "no hard-coded values" enforceable and theming/
accessibility achievable by construction. Every client design system AutoFirm builds is rooted in a
DTCG token file (reference + semantic-alias layers, Oklch color), transformed deterministically into
CSS/native outputs, with token adherence verified as a CI lint. It is the data-layer beneath atomic
design's atoms (source 06) and the structural twin of Material 3's tiered tokens (source 08).
