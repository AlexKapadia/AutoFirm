"""Shared fail-closed error type for malformed artifact specifications.

What this does
--------------
Defines :class:`ArtifactSpecError`, the single exception every builder raises
when a content spec is malformed (empty, structurally invalid, or internally
inconsistent). Centralising it lets callers catch one type across all three
builders.

Why it exists / where it sits
-----------------------------
CLAUDE.md §5.6 requires fail-closed behaviour: a bad spec must be *refused*
before any partial file is written. A distinct exception (not a bare
``ValueError``) makes the refusal unambiguous and testable, and keeps the
contract explicit at every builder boundary.
"""

from __future__ import annotations

__all__ = ["ArtifactSpecError"]


class ArtifactSpecError(ValueError):
    """Raised when an artifact content spec is malformed or inconsistent.

    Subclasses :class:`ValueError` so existing ``except ValueError`` handlers
    still catch it, while giving callers a precise type to match on. Builders
    raise this *before* writing any bytes (fail-closed — CLAUDE.md §5.6).
    """
