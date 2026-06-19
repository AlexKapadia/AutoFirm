"""Numeric-claim fact bundles for the NUMERIC_RECOMPUTE check.

What this does
--------------
Frozen, by-value facts the NUMERIC_RECOMPUTE check reads: each claim pairs a
``declared_value`` (what the artifact states) with an independently
``recomputed_value`` (both :class:`~decimal.Decimal`); the check asserts exact
equality (CLAUDE.md §3.11).

Why it exists / where it sits
-----------------------------
One slice of the per-family split of the by-value fact surface (CLAUDE.md §5.7);
re-exported through :mod:`reviewable_artifact_facts` as the single stable import
point so importers are unchanged.

Security / compliance invariants upheld (CLAUDE.md §5.6, §3.11)
--------------------------------------------------------------
* **Decimal-only money, NO float drift:** numeric values forbid ``float`` at the
  boundary via :func:`reject_float_input`.
* **Fail closed on blanks / emptiness:** blank labels and empty/duplicate claim
  sets are refused at construction (a vacuous check is refused).
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
    "NumericClaim",
    "NumericClaimSet",
]


class NumericClaim(BaseModel):
    """One declared-vs-recomputed numeric pair — the NUMERIC_RECOMPUTE check's unit.

    Inputs
    ------
    * ``label`` — opaque claim label (e.g. ``"gross_margin_fy24"``); non-blank.
    * ``declared_value`` — the value the artifact states (cached/written), ``Decimal``.
    * ``recomputed_value`` — the value the caller computed INDEPENDENTLY, ``Decimal``;
      the check asserts ``declared_value == recomputed_value`` exact to the unit.

    Failure modes
    -------------
    Raises :class:`OutputReviewError` on a blank ``label`` or any ``float`` value.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    label: str
    declared_value: Decimal
    recomputed_value: Decimal

    @field_validator("declared_value", "recomputed_value", mode="before")
    # @classmethod removal is equivalent: pydantic v2 auto-wraps a @field_validator
    # as a classmethod, so dropping the explicit decorator is behaviourally identical.
    @classmethod  # pragma: no mutate
    def _no_float_values(cls, value: object) -> object:
        return reject_float_input(value)

    @field_validator("label")
    # @classmethod removal is equivalent: pydantic v2 auto-wraps a @field_validator
    # as a classmethod, so dropping the explicit decorator is behaviourally identical.
    @classmethod  # pragma: no mutate
    def _label_non_blank(cls, value: str) -> str:
        return require_non_blank(value, field="NumericClaim.label")


class NumericClaimSet(BaseModel):
    """The collection of numeric claims the NUMERIC_RECOMPUTE check verifies.

    Inputs
    ------
    * ``claims`` — one :class:`NumericClaim` per recomputed figure; at least one
      (an empty set has nothing to recompute — refused fail-closed).

    Failure modes
    -------------
    Raises :class:`OutputReviewError` on an empty ``claims`` or duplicate labels.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    claims: tuple[NumericClaim, ...]

    @model_validator(mode="after")
    def _non_empty_unique_labels(self) -> NumericClaimSet:
        if not self.claims:
            raise OutputReviewError("NumericClaimSet.claims must be non-empty")
        labels = [c.label for c in self.claims]
        if len(set(labels)) != len(labels):
            raise OutputReviewError("NumericClaimSet claim labels must be unique")
        return self
