"""Shared fail-closed error type for the output-review gate.

What this does
--------------
Defines :class:`OutputReviewError`, the single exception every output-review
contract and check raises when an input is malformed (an empty/blank identifier,
an impossible verdict construction, a duplicate or unknown check registration).
Centralising it lets callers catch one type across the whole gate.

Why it exists / where it sits
-----------------------------
CLAUDE.md §5.6 requires fail-closed behaviour: when a permission, value, or check
is missing or ambiguous, the action is *refused* rather than proceeding. A distinct
exception makes that refusal unambiguous and testable, and keeps the gate's contract
explicit at every boundary.

Why it does NOT subclass ``ValueError``
---------------------------------------
These contracts are Pydantic v2 frozen models, and pydantic *re-wraps* any
``ValueError``/``AssertionError`` raised inside a validator into a ``ValidationError``
— which would erase the precise type a caller must catch (the false-pass guard's
distinguishing signal). Pydantic instead lets any *other* exception propagate
unchanged, so :class:`OutputReviewError` subclasses :class:`Exception` directly:
the fail-closed refusal surfaces as exactly ``OutputReviewError`` whether it is
raised from a plain function (the registry) or from a model validator (the verdict
guard), giving every boundary one catchable type. (Contrast the artifacts lane's
``ArtifactSpecError``, which subclasses ``ValueError`` because those specs are plain
dataclasses, not pydantic models.)
"""

from __future__ import annotations

__all__ = ["OutputReviewError"]


class OutputReviewError(Exception):
    """Raised when an output-review contract input is malformed or ambiguous.

    Subclasses :class:`Exception` (not :class:`ValueError`) so that when it is raised
    inside a pydantic validator it propagates *as itself* rather than being re-wrapped
    in a ``ValidationError`` — preserving the precise, catchable fail-closed signal at
    every boundary. Raised *before* any verdict is treated as authoritative
    (fail-closed — CLAUDE.md §5.6): a structurally impossible state (e.g. a passed
    verdict that still holds a blocking finding) can never be constructed.
    """
