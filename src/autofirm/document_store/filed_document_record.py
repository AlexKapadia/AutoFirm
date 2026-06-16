"""The typed record for one human-facing deliverable filed into the store.

What this does
--------------
Defines :class:`DeliverableKind` (the closed set of deliverable types the store
files) and :class:`FiledDocumentRecord`, the immutable, validated pydantic record
that describes one filed deliverable: its stable logical identity, the owning
company/owner, its kind, a human canonical name, a version, provenance (which
artifact/run produced it), and a timestamp injected from a clock.

Why it exists / where it sits
-----------------------------
The store reasons over records, not loose strings: a record is the unit the
librarian files, versions, catalogs, and retrieves. Keeping the contract separate
from the filing service keeps it reusable and forces every field to be validated
at the boundary (fail-closed — CLAUDE.md §5.6) before any path is computed.

Security / compliance invariants upheld (CLAUDE.md §5.6)
-------------------------------------------------------
* **Validate at the boundary:** blank/whitespace identifiers, owners, names, or
  provenance, and a non-positive version, are refused at construction — a
  malformed record can never be filed.
* **No path injection via identity fields:** ``logical_id``, ``company``, and
  ``kind`` form the foldering key, so they are constrained to a safe slug pattern
  (lowercase alnum + ``-``/``_``) here, before they ever reach the path scheme.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

__all__ = ["DeliverableKind", "FiledDocumentRecord", "SLUG_PATTERN"]

# Identity fields that become folder/file path segments must be safe slugs: only
# lowercase letters, digits, hyphen and underscore. This blocks path traversal,
# separators, drive letters and whitespace from ever entering a computed path
# (defence-in-depth alongside the workspace boundary — CLAUDE.md §5.6).
SLUG_PATTERN = r"^[a-z0-9][a-z0-9_-]*$"

# A constrained slug string reused for the identity (path-forming) fields.
SlugStr = Annotated[
    str,
    StringConstraints(pattern=SLUG_PATTERN, min_length=1, max_length=128),
]


class DeliverableKind(StrEnum):
    """The closed set of human-facing deliverable kinds the store files.

    A closed enum (not a free string) means the foldering scheme has a fixed,
    audited set of top-level kind buckets — an unknown kind is refused at the
    boundary rather than silently creating a stray folder (fail-closed).
    """

    REPORT = "report"
    MODEL = "model"
    DECK = "deck"
    DOC = "doc"
    IMAGE = "image"


class FiledDocumentRecord(BaseModel):
    """One human-facing deliverable, validated for filing into the store.

    The record is frozen once built (immutable) so that, like the artifacts it
    describes, a filed deliverable's identity cannot mutate underneath the
    catalog. ``logical_id`` is the *stable* identity across versions: re-filing
    the same ``logical_id`` with a higher ``version`` is a new version of the
    SAME document, never a clobber of a different one.

    Args:
        logical_id: Stable slug identifying the document across versions.
        company: Slug of the owning company/owner the deliverable belongs to.
        kind: The :class:`DeliverableKind` bucket.
        canonical_name: Human-readable deliverable name (non-empty, free text).
        extension: File extension without the dot (e.g. ``xlsx``); slug-safe.
        version: 1-based version number; monotonically increasing per document.
        provenance: What produced it (builder/run id) — non-empty, for audit.
        created_at: Timestamp injected from a clock (never ``now()`` internally,
            so filing is deterministic and testable — CLAUDE.md §3.11).

    Raises:
        pydantic.ValidationError: If any field violates its constraint
            (fail-closed — a malformed record never reaches the librarian).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    logical_id: SlugStr
    company: SlugStr
    kind: DeliverableKind
    canonical_name: Annotated[str, StringConstraints(min_length=1, max_length=256)]
    extension: Annotated[
        str, StringConstraints(pattern=r"^[a-z0-9]{1,12}$", min_length=1, max_length=12)
    ]
    version: int = Field(ge=1)
    provenance: Annotated[str, StringConstraints(min_length=1, max_length=512)]
    created_at: datetime

    @field_validator("canonical_name", "provenance")
    @classmethod
    def _reject_blank_freetext(cls, value: str) -> str:
        """Refuse all-whitespace free-text fields (pattern can't catch this)."""
        if not value.strip():  # fail-closed: a blank name/provenance is a content gap
            raise ValueError("must not be blank or whitespace-only")
        return value
