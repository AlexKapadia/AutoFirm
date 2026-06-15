# BEST-PARTS — Atomic Design

## What AutoFirm should ADOPT and why

1. **The five-tier component hierarchy as the design-system structure.** ADOPT atoms -> molecules
   -> organisms -> templates -> pages as the canonical organization for every client design system.
   Build implication: the design brief's "component inventory" (CLAUDE.md §4.9.2) is structured by
   atomic-design tier; UI-build agents (§4.9.3) build bottom-up (atoms first), guaranteeing reuse
   and consistency (Nielsen H4, source 01).

2. **Templates as the "every state, real data" contract.** ADOPT the templates-vs-pages
   distinction: templates define structure for ALL states (loading/empty/error/edge, source 09);
   pages instantiate with real representative content. Build implication: directly encodes the
   "build around real data and every state, never happy-path mockups" rule (§3.14) — a template
   missing the empty/error variant is incomplete.

3. **Atoms-as-tokens bridge.** ADOPT: atoms are where design tokens (sources 07/08) materialize
   (a button atom consumes color/spacing/type tokens). Build implication: token adherence is
   enforced at the atom level — no hard-coded values below the atom -> measurable token compliance.

4. **The "parts and whole simultaneously" mental model for the agent build.** ADOPT as the
   decomposition strategy for parallel UI-build fan-out (§4.3): atoms/molecules are independent,
   parallelizable units; organisms/templates are the fan-in integration. Build implication: maps
   cleanly onto AutoFirm's orchestrator fan-out/fan-in.

## What AutoFirm should REJECT / DEFER

- **REJECT rigid/linear application.** Frost is explicit it "is not a linear process" — do not force
  every UI element into exactly one tier or block progress on taxonomy debates; it is a mental
  model, not a build gate.
- **REJECT it as a sufficient quality bar.** Atomic design organizes components but says nothing
  about whether they are good, accessible, or non-vibe-coded — pair with sources 01 (heuristics),
  03 (WCAG), 07/08 (tokens) for the quality bar.
- **DEFER the exact tier naming** as a hard requirement — a client team may prefer "primitives/
  components/patterns"; adopt the *structure*, allow naming flexibility (generality, §3.9).

## Concrete build implication
Atomic design is the structural backbone of every client design system AutoFirm builds: a five-tier
component inventory (atoms->pages) that makes reuse/consistency the default, materializes design
tokens at the atom level, encodes "every state with real data" at the template level, and decomposes
the UI build into parallelizable (atoms/molecules) and integration (organisms/templates) units for
the orchestrator. It is the organizing methodology; quality comes from sources 01/03/04/07/08.
