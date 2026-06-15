# BEST-PARTS — Tufte Data-Ink / Chartjunk

## ADOPT
- **Maximize-data-ink as a chart-rendering policy** for every chart in decks, models, and `evidence/`. The chart styler defaults to: no 3D, no heavy gridlines, no redundant borders, minimal/no chart background fill, direct labels over legends where feasible. This is the concrete anti-chartjunk default that beats matplotlib/python-pptx out-of-box "AI-slop" styling.
- **Data-ink ratio as a measurable lint** (approximation): flag charts with chartjunk tells (3D type, gridline density above a threshold, redundant legend when <=2 series directly labellable, decorative fills). A computable proxy for "1.0 minus erasable ink".
- **"Above all else show the data"** becomes a deck rule: charts carry the message; the title states the takeaway (pairs with Minto action titles, source 06).

## REJECT
- **Default library chart styling** (python-pptx Accent-1..6 theme defaults, matplotlib default gridlines/3D, Excel default chart) — these are the templated look the CDO bans (CLAUDE §3.14). Override with a Tufte/IBCS styler.
- **Chartjunk:** 3D charts, gradient fills, heavy gridlines, drop-shadows, decorative imagery — explicitly banned in the styler.

## BUILD IMPLICATION
A shared `chart_styler` (used by deck, model, and evidence builders) enforcing maximize-data-ink defaults + a `chartjunk_lint`. This is the single most reusable anti-AI-slop control across B15 AND the `evidence/` showcase (CLAUDE §3.10 PNG+HTML charts). Quantify in evidence: data-ink-ratio proxy per generated chart.
