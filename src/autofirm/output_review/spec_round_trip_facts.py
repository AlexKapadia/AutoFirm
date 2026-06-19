"""Spec-round-trip fact bundle for the SPEC_ROUND_TRIP check.

What this does
--------------
A frozen, by-value fact the SPEC_ROUND_TRIP check reads: two by-value maps,
``declared_values`` (from the spec) and ``extracted_values`` (re-read from the
rendered artifact); the check asserts they match (every declared key present &
equal).

Why it exists / where it sits
-----------------------------
One slice of the per-family split of the by-value fact surface (CLAUDE.md §5.7);
re-exported through :mod:`reviewable_artifact_facts` as the single stable import
point so importers are unchanged.

Security / compliance invariants upheld (CLAUDE.md §5.6, §3.11)
--------------------------------------------------------------
* **Fail closed on blanks / emptiness:** an empty value map (a vacuous round-trip)
  and a blank key are refused at construction via :func:`require_non_blank`.
* **Frozen & by-value:** ``frozen=True``/``extra="forbid"`` — checks share immutable
  data and cannot mutate each other's view.
* **No PII:** opaque, string-keyed scalars only — never raw artifact bytes.
"""

from __future__ import annotations

from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict, field_validator

from autofirm.output_review.fact_value_guards import require_non_blank
from autofirm.output_review.output_review_errors import OutputReviewError

__all__ = [
    "SpecRoundTrip",
]


class SpecRoundTrip(BaseModel):
    """Declared-vs-extracted value maps — the SPEC_ROUND_TRIP check's input.

    Inputs
    ------
    * ``declared_values`` — what the originating spec declared, by opaque key
      (string scalars, normalised by the caller — never floats, never raw bytes).
    * ``extracted_values`` — what was re-read from the rendered artifact, same keying;
      the check asserts the two maps match (every declared key present & equal).

    Failure modes
    -------------
    Raises :class:`OutputReviewError` if either map is empty (an empty spec round-trip
    is a vacuous pass — refuse it) or carries a blank key.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    declared_values: Mapping[str, str]
    extracted_values: Mapping[str, str]

    @field_validator("declared_values", "extracted_values")
    @classmethod
    def _non_empty_keys_non_blank(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        if not value:
            # fail-closed: an empty map means "nothing to round-trip" — a check over
            # it would vacuously pass and let a dropped artifact slip through.
            raise OutputReviewError("SpecRoundTrip value maps must be non-empty")
        for key in value:
            require_non_blank(key, field="SpecRoundTrip map key")
        return value
