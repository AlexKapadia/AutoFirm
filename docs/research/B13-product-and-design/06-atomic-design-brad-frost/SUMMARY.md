# SUMMARY — Atomic Design (Brad Frost)

## Full citation
- **Title:** Atomic Design — Chapter 2: Atomic Design Methodology (full book)
- **Author/Org:** Brad Frost
- **Year:** Methodology introduced 2013 (blog post); book published 2016
- **Venue/Publisher:** self-published book, atomicdesign.bradfrost.com (open access)
- **URL:** https://atomicdesign.bradfrost.com/chapter-2/ · book: https://atomicdesign.bradfrost.com/

## Questions it informs
- **L1.B13.2** (design-systems & component-inventory theory — PRIMARY methodology for component
  hierarchy)

## GRADE tier: Moderate
Definitive practitioner methodology by its originator; widely adopted across the industry (the
de-facto standard mental model for component hierarchy). Down-rate from High because it is a
practitioner book, not peer-reviewed; up-rate for near-universal adoption and being the original,
unambiguous source. Treated as the canonical reference for the component-inventory concept.

## Key claims (exact)

**The chemistry analogy.** "atomic elements combine together to form molecules. These molecules
can combine further to form relatively complex organisms." Atomic design borrows this hierarchy
for UIs.

**The five stages (exact definitions):**
1. **Atoms** — "the atoms of our interfaces serve as the foundational building blocks that
   comprise all our user interfaces." Basic HTML elements (labels, inputs, buttons) that cannot be
   broken down further without ceasing to be functional.
2. **Molecules** — "molecules are relatively simple groups of UI elements functioning together as
   a unit." Example: a label + input + button forming a search form.
3. **Organisms** — "Organisms are relatively complex UI components composed of groups of molecules
   and/or atoms and/or other organisms." Example: a site header (logo + nav + search molecule).
4. **Templates** — "Templates are page-level objects that place components into a layout and
   articulate the design's underlying content structure." They show structure/skeleton, content-
   agnostic.
5. **Pages** — "Pages are specific instances of templates that show what a UI looks like with real
   representative content in place." Pages test the design system with actual content.

**Core principle.** "atomic design is not a linear process," but "a mental model to help us think
of our user interfaces as both a cohesive whole and a collection of parts at the same time."
Value: it lets designers traverse abstraction levels concurrently and enforces consistency by
reusing the same atoms/molecules everywhere.

## Reproducibility note
The five stage names and quoted definitions are fixed at atomicdesign.bradfrost.com/chapter-2/
and re-verifiable in the open-access book.
