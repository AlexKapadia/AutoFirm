"""Real-data decision-modeling engine — models that drive real business decisions.

Agents build and maintain financial / customer-base / operational models on a
company's REAL operational + public/market data and use them to derive
EXPLAINABLE business recommendations (pricing, features, strategy). Every model
is a deterministic, owned, fail-closed :class:`DecisionModel` whose recommendation
carries the exact drivers that produced it, so the "why" always matches the
"what" (CLAUDE.md §3.11). Monetary quantities are exact :class:`~decimal.Decimal`
routed through ``autofirm.foundation.money`` and ``autofirm.finance`` — never
floats.

Data-boundary note: the engine runs on real company data for live decisions, but
the platform's OWN tests use synthetic fixtures only (CLAUDE.md §3.12).
"""
