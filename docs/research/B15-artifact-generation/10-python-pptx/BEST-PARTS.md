# BEST-PARTS — python-pptx

## ADOPT
- **python-pptx as the deck renderer** (no Office needed; OOXML-native; template + data-merge). Renders the storyline tree from `deck_storyline_planner` (source 06) into slides.
- **Template-driven layout via a custom .pptx master/template** carrying the per-company design tokens (type scale, spacing, palette) — placeholders addressed by **idx**. The custom master is how we escape the default look.
- **OOXML escape hatch** for premium formatting python-pptx does not expose (e.g. fine typographic control, custom chart styling) — edit the raw Open XML part (source 12). This is the sanctioned path to "not templated".
- **Override theme Accent 1–6 defaults** with the IBCS semantic palette (source 09) + Tufte styler (source 07) — the default Accent colours are the AI-slop tell.

## REJECT
- **Shipping default-theme decks** (Accent 1–6, default chart styling) — instant CDO fail (CLAUDE §3.14).
- **3D charts** — unsupported by python-pptx anyway, and banned by Tufte chartjunk rules. Convenient alignment.

## BUILD IMPLICATION
`deck_renderer` = python-pptx + a custom company master/template (design tokens) + `chart_styler`/`chart_type_selector` (sources 07/08) + IBCS palette (source 09) + raw-XML escape hatch for premium touches. Live E2E-style check: render -> open via LibreOffice headless -> assert valid, no default-Accent palette, every placeholder filled, every chart matches its message type.
