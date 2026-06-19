"""The by-value fact surface, re-exported from per-family modules as one stable point.

What this does
--------------
This module's single responsibility is to be **the by-value fact surface,
re-exported from per-family modules as one stable import point**. Every typed,
frozen, by-value fact bundle the seven deterministic checks read is defined in a
per-check-family module and re-exported here, so each historical
``from autofirm.output_review.reviewable_artifact_facts import X`` keeps working
unchanged. One sub-model per check family:

* :class:`BalanceSheetPeriod` / :class:`BalanceSheetFigures` — ACCOUNTING_IDENTITY
  (:mod:`balance_sheet_facts`).
* :class:`NumericClaim` / :class:`NumericClaimSet` — NUMERIC_RECOMPUTE
  (:mod:`numeric_claim_facts`).
* :class:`SpecRoundTrip` — SPEC_ROUND_TRIP (:mod:`spec_round_trip_facts`).
* :class:`ModelRowFormulaFacts` / :class:`ModelLintFacts` — FAST_LINT
  (:mod:`model_lint_facts`).
* :class:`DeckElementFacts` / :class:`DeckStructuralFacts` — IBCS_SUCCESS +
  VISUAL_INTEGRITY (:mod:`deck_structural_facts`).

Why it exists / where it sits
-----------------------------
``SYNTHESIS.md`` §2.2 makes the deterministic floor a *pure function of by-value
data*. The fact surface was split per family to keep every file under the CLAUDE.md
§5.7 300-line limit; this thin aggregator preserves the single import point so the
seven P1 checks and their tests need NO import churn. Every re-exported name is
listed in ``__all__`` (alphabetised) — required so mypy ``--strict``
(``no_implicit_reexport``) treats each as an explicit, public re-export.
"""

from __future__ import annotations

from autofirm.output_review.balance_sheet_facts import (
    BalanceSheetFigures,
    BalanceSheetPeriod,
)
from autofirm.output_review.deck_structural_facts import (
    DeckElementFacts,
    DeckStructuralFacts,
)
from autofirm.output_review.model_lint_facts import (
    ModelLintFacts,
    ModelRowFormulaFacts,
)
from autofirm.output_review.numeric_claim_facts import (
    NumericClaim,
    NumericClaimSet,
)
from autofirm.output_review.spec_round_trip_facts import SpecRoundTrip

__all__ = [
    "BalanceSheetFigures",
    "BalanceSheetPeriod",
    "DeckElementFacts",
    "DeckStructuralFacts",
    "ModelLintFacts",
    "ModelRowFormulaFacts",
    "NumericClaim",
    "NumericClaimSet",
    "SpecRoundTrip",
]
