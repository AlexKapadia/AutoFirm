# BEST-PARTS — Kosslyn, Clear and to the Point

## ADOPT
- **A cognitive-science basis for the deck lint, corroborating practitioner standards.** Every
  B15.2 deck rule now has both a craft authority *and* a psychological mechanism, lifting the claim
  set above practitioner-book-only and meeting DEPTH-RUBRIC §1/§4 for the deck-craft architecture:
  - **Capacity Limitations** → justifies the "one message per slide / limit items" rule
    (↔ Minto MECE, IBCS). Drives a `slide_density_lint` (max distinct messages/elements per slide).
  - **Salience + Discriminability** → justifies the contrast/emphasis rule (↔ IBCS UNIFY, Tufte).
    Drives a `contrast_lint` (the headline takeaway must be the highest-salience element).
  - **Informative Changes** → justifies "no decorative variation" (↔ Tufte data-ink, IBCS).
    Drives a `decorative-change lint` (color/size changes must carry meaning, not theme accents).
  - **Compatibility** → justifies message-type→chart-type matching (↔ Zelazny). Reinforces the
    deterministic `chart_type_selector`.
  - **Perceptual Organization** → justifies proximity/grouping of related content; drives a layout
    rule that related items are visually chunked.
  - **Relevance + Appropriate Knowledge** → justifies audience-parameterized content depth and
    jargon-avoidance (per-company/per-audience config, not hard-coded → generality, CLAUDE §3.9).
- **Adds the only mechanistic "why" in the deck library** — so the IBCS SUCCESS rubric is graded
  not just by convention but by an evidence-backed principle the evaluator can cite.

## REJECT
- **Reject decoration-as-emphasis** — Informative Changes forbids color/size/style changes that
  carry no information (the default-theme Accent-1–6 palette, gratuitous shadows): an AI-slop tell.
- **Reject overloaded slides** — Capacity Limitations gives an evidence basis for failing
  kitchen-sink multi-message exhibits.

## BUILD IMPLICATION
Component: strengthens `success_rubric` evaluator and `visual_integrity_lint`. New, principle-named
checks: slide-density (Capacity), takeaway-is-highest-salience (Salience/Discriminability),
no-decorative-change (Informative Changes), related-items-chunked (Perceptual Organization). Each
deck rule in `evidence/` now carries TWO citations — a practitioner standard and a Kosslyn
principle — demonstrating the deck contract is corroborated across craft and cognitive-science
disciplines, not asserted.
