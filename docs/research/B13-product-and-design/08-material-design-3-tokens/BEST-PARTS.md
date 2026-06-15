# BEST-PARTS — Material Design 3 Tokens

## What AutoFirm should ADOPT and why

1. **The three-tier token model (reference -> system/semantic -> component) as the canonical token
   architecture.** ADOPT this layering on top of the DTCG format (source 07). Build implication:
   AutoFirm's generated design systems use reference tokens (raw palette) -> semantic system tokens
   (primary/surface/error/on-*) -> component tokens. Theming = swap the reference layer; the rule
   "components reference SEMANTIC tokens, never raw values" makes the entire UI re-theme consistently
   and is the precise lint for "no hard-coded values" (§4.9.7).

2. **The "on-color" pairing for accessibility-by-construction.** ADOPT paired foreground/background
   roles (on-primary on primary, on-surface on surface) engineered to meet WCAG contrast (source 03)
   automatically. Build implication: AutoFirm generates palettes whose semantic roles satisfy 4.5:1 /
   3:1 BY CONSTRUCTION, so a11y contrast is largely guaranteed before testing rather than patched
   after — a force-multiplier on the WCAG AA gate.

3. **Tonal-palette generation from a few key colors.** ADOPT algorithmic palette generation (key
   color -> tonal palette tones 0-100 -> role mapping) to produce principled, evenly-stepped,
   per-client color systems without hand-picking. Build implication: defeats AI-slop random-hex
   palettes (§3.14) with a deterministic, defensible color algorithm; supports per-client brand input.

4. **"Accessibility by default" as the system-level value.** ADOPT as the design-system ethos: a11y
   is baked into tokens/components, not bolted on. Build implication: aligns the design-build playbook
   with the fail-closed/secure-by-default ethos (§5.6) applied to accessibility.

## What AutoFirm should REJECT / DEFER

- **REJECT adopting Material's VISUAL identity wholesale.** Material is Google's brand signature;
  copying its look = the plagiarism/clone failure (§3.14 "inspiration, never plagiarism"). ADOPT the
  token ARCHITECTURE and accessibility approach; REJECT the Material look as a default client skin.
- **REJECT defaulting every client UI to a single library look** (Material/shadcn/etc.) — the
  anti-vibe-coded bar demands custom decisions; use libraries as accessible primitives, then
  re-skin via tokens (generality + originality, §3.14).
- **DEFER Material-specific component tokens naming** — adopt the three-tier CONCEPT, name per client.

## Concrete build implication
Material 3 is AutoFirm's proven blueprint for tiered design tokens: reference -> semantic -> component,
with on-color pairings that satisfy WCAG contrast by construction and algorithmic tonal-palette
generation that kills random-hex AI-slop. Adopt the architecture and accessibility-by-default approach
(layered on the DTCG format, source 07; consumed at the atom level, source 06); REJECT the Material
brand look so each client UI stays custom and non-plagiarized.
