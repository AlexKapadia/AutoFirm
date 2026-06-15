# BEST-PARTS — Zelazny Say It With Charts

## ADOPT
- **Message-to-chart-type selector as a deterministic rule table.** Given a slide's message type (component / item / time / frequency / correlation), the renderer auto-selects the canonical chart family (pie / bar / column / histogram / scatter). This makes chart choice *principled and testable*, not arbitrary.
- **Keyword heuristic for classification:** parse the action title's verb/keyword ("grew", "share", "ranks", "correlates") to infer the comparison type, then pick the chart. Pairs directly with Minto action titles (source 06) — the title's claim drives the exhibit.
- **One message per chart** — banned: multi-message kitchen-sink exhibits.

## REJECT
- **Data-driven chart choice** (picking a chart because the data is "a table of numbers") — Zelazny's whole thesis is message-first. Reject any auto-charting that ignores the intended message.
- **Pie charts for anything but component/share**, and **pie charts with many slices** (Zelazny + Tufte both discourage) — constrain pie to small component splits.

## BUILD IMPLICATION
A `chart_type_selector` (message-type -> chart-family rule table) sits between `deck_storyline_planner` (source 06) and `chart_styler` (source 07). Test: for each comparison type, assert the selected chart family; adversarial test that a mismatched message/chart (e.g. time series rendered as pie) is rejected. Deterministic, general, and directly anti-AI-slop.
