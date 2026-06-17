"""The document store: files every human-facing deliverable into a sensitive store.

This package is the librarian + organized document/artifact store. It takes the
deliverables that :mod:`autofirm.artifacts` produces (reports / models / decks /
docs / images) and FILES each one into an impeccably-organized store that lives
ONLY under the gitignored ``.autofirm/`` sensitive root (never the public code
tree), enforcing a deterministic naming/foldering scheme fail-closed.

Where it sits
-------------
* :mod:`.filed_document_record` — the typed pydantic record for one deliverable.
* :mod:`.canonical_document_path_scheme` — deterministic, collision-free path.
* :mod:`.librarian_filing_service` — fail-closed filing + the append-only catalog
  and retrieval (``find``/``list``).

Security / compliance invariants (CLAUDE.md §5.6)
-------------------------------------------------
Everything filed resolves under the gitignored ``.autofirm/`` root via
:class:`autofirm.access.workspace_data_boundary.WorkspaceDataBoundary` — the
single boundary primitive — so the public-code vs. sensitive-data separation is
enforced in the data layer, fail-closed, and never left to convention.
"""

from __future__ import annotations

from autofirm.document_store.canonical_document_path_scheme import (
    CanonicalPathError,
    canonical_relative_path_for,
)
from autofirm.document_store.filed_document_record import (
    DeliverableKind,
    FiledDocumentRecord,
)
from autofirm.document_store.librarian_filing_service import (
    CatalogEntry,
    LibrarianFilingError,
    LibrarianFilingService,
)

__all__ = [
    "CanonicalPathError",
    "CatalogEntry",
    "DeliverableKind",
    "FiledDocumentRecord",
    "LibrarianFilingError",
    "LibrarianFilingService",
    "canonical_relative_path_for",
]
