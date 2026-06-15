# SUMMARY — W3C Design Tokens Format Module (DTCG)

## Full citation
- **Title:** Design Tokens Format Module (specification) + "Design Tokens specification reaches
  first stable version"
- **Author/Org:** Design Tokens Community Group (DTCG), a W3C Community Group
- **Year:** First stable version **2025.10**, announced **28 October 2025**
- **Venue/Publisher:** W3C Community Group (vendor-neutral standard; note: a Community Group Report,
  not a W3C Recommendation track)
- **URL:** https://www.designtokens.org/ · spec: https://www.designtokens.org/tr/drafts/format/ ·
  announcement: https://www.w3.org/community/design-tokens/2025/10/28/design-tokens-specification-reaches-first-stable-version/

## Questions it informs
- **L1.B13.2** (design-tokens theory — PRIMARY interoperable format standard)

## GRADE tier: Moderate
A W3C Community Group standard (vendor-neutral, multi-tool consensus: Figma, Tokens Studio, Style
Dictionary, etc.). Down-rate from High because a Community Group Report is not a normative W3C
Recommendation (unlike WCAG). Up-rate for being the single cross-vendor interoperability standard
with broad tooling adoption. Authoritative for the token *format*.

## Key claims (exact)

**Purpose.** The spec "describes a file format to exchange design tokens between different tools."
The DTCG JSON format "unlocks interoperability and theming between your tools" — one source of
truth shared across design tools (Figma), codebases, and platforms.

**What a design token is.** A design token stores a named design decision (a style value such as a
color, font, spacing, or duration) so "the same values can be used across designs, code, tools, and
platforms" — decoupling the decision (semantic name) from its raw value.

**Format essentials (DTCG JSON).** A token is a JSON object with a value (`$value`) and a type
(`$type`); tokens are organized into groups; tokens may ALIAS other tokens (references), enabling
semantic layering and theming. The 2025.10 stable version adds: theming / multi-brand support;
"modern color specification with full support for Display P3, Oklch, and CSS Color Module 4 spaces";
and "rich token relationships for sophisticated design systems."

**Interoperability value.** Because the format is tool-neutral, a token file authored in one tool
(e.g. Figma via a plugin) can be transformed (e.g. by Style Dictionary) into platform outputs (CSS
custom properties, iOS, Android) without manual re-entry — eliminating design-to-code drift.

## Reproducibility note
The "file format to exchange design tokens between tools" purpose, the $value/$type/alias structure,
and the 2025.10 stable-version capabilities (P3/Oklch/CSS Color 4, theming) are stated at
designtokens.org and the 28 Oct 2025 W3C CG announcement, and re-verifiable there.
