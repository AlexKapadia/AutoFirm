"""Balance-sheet fact bundles for the ACCOUNTING_IDENTITY check.

What this does
--------------
Frozen, by-value facts the ACCOUNTING_IDENTITY check reads: per-period
``assets``/``liabilities``/``equity`` as :class:`~decimal.Decimal`, so the check
asserts ``assets == liabilities + equity`` EXACT to the unit (CLAUDE.md §3.11).

Why it exists / where it sits
-----------------------------
One slice of the per-family split of the by-value fact surface (CLAUDE.md §5.7);
re-exported through :mod:`reviewable_artifact_facts` as the single stable import
point so importers are unchanged.

Security / compliance invariants upheld (CLAUDE.md §5.6, §3.11)
--------------------------------------------------------------
* **Decimal-only money, NO float drift:** monetary figures forbid ``float`` at the
  boundary via :func:`reject_float_input`.
* **Fail closed on blanks / emptiness:** blank period labels and empty/duplicate
  period sets are refused at construction (a vacuous check is refused).
* **Frozen & by-value:** ``frozen=True``/``extra="forbid"`` — checks share immutable
  data and cannot mutate each other's view.
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from autofirm.output_review.fact_value_guards import (
    reject_float_input,
    require_non_blank,
)
from autofirm.output_review.output_review_errors import OutputReviewError

__all__ = [
    "BalanceSheetFigures",
    "BalanceSheetPeriod",
]


class BalanceSheetPeriod(BaseModel):
    """One period's balance-sheet figures — the ACCOUNTING_IDENTITY check's unit.

    Inputs
    ------
    * ``period`` — opaque period label (e.g. ``"FY24"``); non-blank.
    * ``assets`` / ``liabilities`` / ``equity`` — :class:`~decimal.Decimal` figures
      the check compares as ``assets == liabilities + equity`` exact to the unit.

    Failure modes
    -------------
    Raises :class:`OutputReviewError` on a blank ``period`` or any ``float`` figure.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    period: str
    assets: Decimal
    liabilities: Decimal
    equity: Decimal

    @field_validator("assets", "liabilities", "equity", mode="before")
    # @classmethod removal is equivalent: pydantic v2 auto-wraps a @field_validator
    # as a classmethod, so dropping the explicit decorator is behaviourally identical.
    @classmethod  # pragma: no mutate
    def _no_float_figures(cls, value: object) -> object:
        return reject_float_input(value)

    @field_validator("period")
    # @classmethod removal is equivalent: pydantic v2 auto-wraps a @field_validator
    # as a classmethod, so dropping the explicit decorator is behaviourally identical.
    @classmethod  # pragma: no mutate
    def _period_non_blank(cls, value: str) -> str:
        return require_non_blank(value, field="BalanceSheetPeriod.period")


class BalanceSheetFigures(BaseModel):
    """The full set of periods the ACCOUNTING_IDENTITY check verifies.

    Inputs
    ------
    * ``periods`` — one :class:`BalanceSheetPeriod` per reporting period; at least one
      (an empty balance sheet has nothing to verify — refused fail-closed).

    Failure modes
    -------------
    Raises :class:`OutputReviewError` on an empty ``periods`` or duplicate period
    labels (an ambiguous period set could hide a defect in a shadowed period).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    periods: tuple[BalanceSheetPeriod, ...]

    @model_validator(mode="after")
    def _non_empty_unique_periods(self) -> BalanceSheetFigures:
        if not self.periods:
            # fail-closed: an empty balance sheet means the check would vacuously
            # "pass" — refuse rather than wave through a model with nothing to verify.
            raise OutputReviewError("BalanceSheetFigures.periods must be non-empty")
        labels = [p.period for p in self.periods]
        if len(set(labels)) != len(labels):
            raise OutputReviewError("BalanceSheetFigures period labels must be unique")
        return self
