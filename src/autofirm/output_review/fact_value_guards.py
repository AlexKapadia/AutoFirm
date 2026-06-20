"""Shared by-value field guards every output-review fact model validates through.

What this does
--------------
Two package-internal validators reused by every fact family so the exactness and
fail-closed rules live in ONE place instead of being copy-pasted per model:

* :func:`reject_float_input` — refuses ``float``/``bool`` before pydantic coerces a
  monetary/numeric field, so no float drift can enter an exact-to-the-unit check.
* :func:`require_non_blank` — refuses a blank label/key/name, so a fact can never be
  constructed with an unnameable, un-actionable identifier.

Why it exists / where it sits
-----------------------------
The by-value fact surface is split per check-family (see
:mod:`reviewable_artifact_facts`) to stay under the CLAUDE.md §5.7 300-line limit;
these two guards are the cross-family primitives those modules share, so they live
here as one stable import point rather than being duplicated in each family file.

Security / compliance invariants upheld (CLAUDE.md §5.6, §3.11)
--------------------------------------------------------------
* **Decimal-only money, NO float drift:** ``float`` (and ``bool``, an ``int``
  subclass that has no place in a money field) is refused fail-closed — a ``float``
  cannot represent ``0.1`` exactly and would silently break an exact check.
* **Fail closed on blanks:** an empty/whitespace label, key, or name is refused at
  construction — a check can never be handed a fact it cannot point at.
"""

from __future__ import annotations

from autofirm.output_review.output_review_errors import OutputReviewError


def reject_float_input(value: object) -> object:
    """Refuse ``float`` before pydantic coerces it (the exactness guard).

    A ``float`` cannot represent most decimals exactly (e.g. ``0.1``), so accepting
    one would silently inject drift into an exact-to-the-unit check. Decimal / int /
    str are passed through for normal :class:`~decimal.Decimal` validation; a
    ``float`` (and ``bool``, which is an ``int`` subclass that has no place in a money
    field) is refused fail-closed (CLAUDE.md §3.11, §5.6).

    Inputs: ``value`` — the raw field value before coercion.
    Outputs: the same ``value`` unchanged when accepted.
    Failure modes: raises :class:`OutputReviewError` on a ``bool`` or ``float``.
    """
    if isinstance(value, bool | float):
        raise OutputReviewError(
            "monetary/numeric fields forbid float/bool input (exactness, §3.11); "
            "pass Decimal, int, or a numeric string"
        )
    return value


def require_non_blank(value: str, *, field: str) -> str:
    """Refuse a blank label/key/name (fail-closed — an unnameable fact is useless).

    Inputs: ``value`` — the candidate string; ``field`` — its name, for the message.
    Outputs: the same ``value`` unchanged when non-blank.
    Failure modes: raises :class:`OutputReviewError` on an empty/whitespace string.
    """
    if not value or not value.strip():
        raise OutputReviewError(f"{field} must be non-blank")
    return value
