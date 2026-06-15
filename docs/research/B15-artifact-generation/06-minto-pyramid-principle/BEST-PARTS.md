# BEST-PARTS — Minto Pyramid Principle

## ADOPT
- **Answer-first storyline as the deck's data contract.** Before any slide is rendered, the deck builder must produce a **storyline tree**: governing thought -> MECE key messages -> supporting evidence. This is the structural input to the renderer (not free-form slides). Directly anti-AI-slop: the deck has an argument, not a template.
- **Action/message titles mandatory.** Every slide title is a full-sentence assertion of that slide's takeaway. Test with teeth: title must be a complete assertive sentence (has a verb, makes a claim), not a noun-phrase topic label.
- **Title-only readthrough test:** reading the slide titles in order must reconstruct the governing argument. A coherence check (titles form a logical chain supporting the governing thought).
- **MECE check on key messages:** the top-level supporting points are non-overlapping and collectively cover the governing thought.

## REJECT
- **Topic-label titles** ("Overview", "Financials", "Market") — the #1 AI-slop deck tell. Banned by the title-assertion test.
- **Data-first slide ordering** (building up to the conclusion) — inverted; conclusion leads.

## BUILD IMPLICATION
Component `deck_storyline_planner` emits a typed storyline tree (governing thought + MECE messages + evidence) BEFORE `deck_renderer` (python-pptx) draws anything — separating *argument* from *rendering*. Tests: title-is-assertion, title-readthrough-coherence, MECE-grouping. This is the core mechanism that makes generated decks "excellent, not templated".
