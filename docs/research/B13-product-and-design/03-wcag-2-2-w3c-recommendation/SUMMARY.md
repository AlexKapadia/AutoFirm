# SUMMARY — Web Content Accessibility Guidelines (WCAG) 2.2

## Full citation
- **Title:** Web Content Accessibility Guidelines (WCAG) 2.2
- **Author/Org:** W3C — Web Accessibility Initiative (WAI), Accessibility Guidelines Working Group
- **Year:** First published as W3C Recommendation **5 October 2023**; current revised
  Recommendation dated **12 December 2024** (the version served at the canonical URL)
- **Venue/Publisher:** World Wide Web Consortium (W3C) — official web standard
- **URL:** https://www.w3.org/TR/WCAG22/ ·
  Overview: https://www.w3.org/WAI/standards-guidelines/wcag/

## Questions it informs
- **L1.B13.4** (Accessibility foundations — WCAG 2.2 AA — PRIMARY normative standard)

## GRADE tier: High
Official W3C Recommendation (normative web standard). The single authoritative source; primary.
No down-rate. Quantitative thresholds are normative, not opinion.

## Key claims (exact)

**Structure.** WCAG 2.2 is organized under 4 principles (Perceivable, Operable, Understandable,
Robust), 13 guidelines, and testable success criteria at three conformance levels: A, AA, AAA.
WCAG 2.2 is backward compatible: it ADDS criteria to 2.1 and removes/changes none EXCEPT
**4.1.1 Parsing**, which is "(Obsolete and removed)."

**Nine NEW success criteria in 2.2 (vs 2.1), with level:**
- 2.4.11 Focus Not Obscured (Minimum) — **AA**
- 2.4.12 Focus Not Obscured (Enhanced) — AAA
- 2.4.13 Focus Appearance — AAA
- 2.5.7 Dragging Movements — **AA**
- 2.5.8 Target Size (Minimum) — **AA**
- 3.2.6 Consistent Help — A
- 3.3.7 Redundant Entry — A
- 3.3.8 Accessible Authentication (Minimum) — **AA**
- 3.3.9 Accessible Authentication (Enhanced) — AAA

**Exact normative text (load-bearing AA criteria):**
- **2.5.8 Target Size (Minimum) [AA]:** the size of the target for pointer inputs is at least
  **24 by 24 CSS pixels**, except where: Spacing (a 24px-diameter circle centered on the target
  does not intersect any other target's circle), Equivalent, Inline, User-agent control, or
  Essential.
- **2.4.11 Focus Not Obscured (Minimum) [AA]:** "When a user interface component receives keyboard
  focus, the component is not entirely hidden due to author-created content."
- **2.4.13 Focus Appearance [AAA]:** the focus indicator area is "at least as large as the area of
  a 2 CSS pixel thick perimeter of the unfocused component" AND has "a contrast ratio of at least
  3:1 between the same pixels in the focused and unfocused states."
- **3.3.8 Accessible Authentication (Minimum) [AA]:** a cognitive function test (e.g. remembering a
  password, transcribing) is not required for any authentication step unless an alternative, a
  mechanism, object-recognition, or personal-content recognition is provided.

**Carried-over AA basics (from 2.0/2.1, still required at AA):** 1.4.3 Contrast (Minimum) — text
contrast ratio **at least 4.5:1** (3:1 for large text); 1.4.11 Non-text Contrast — **3:1** for UI
components/graphics; 1.4.10 Reflow; 1.4.4 Resize Text to 200%; 2.1.1 Keyboard; 2.4.7 Focus Visible.

## Reproducibility note
The nine new criteria, levels, removal of 4.1.1, and the 24x24 CSS-pixel / 3:1 / 4.5:1 numbers are
normatively fixed at https://www.w3.org/TR/WCAG22/ and re-verifiable per success-criterion anchor.
