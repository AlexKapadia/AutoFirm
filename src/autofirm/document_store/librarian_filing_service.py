"""The librarian: fail-closed filing + append-only catalog + retrieval.

What this does
--------------
:class:`LibrarianFilingService` is the single entry point that FILES a
:class:`autofirm.document_store.filed_document_record.FiledDocumentRecord` into
the sensitive store. For each filing it:

1. Computes the canonical relative path (``canonical_document_path_scheme``).
2. Resolves it to an absolute path UNDER the gitignored ``.autofirm/`` root via
   :class:`autofirm.access.workspace_data_boundary.WorkspaceDataBoundary` — the
   reused boundary primitive, NOT a reimplementation.
3. REFUSES (fail-closed) the filing if it would escape the store boundary,
   collide with a *different* logical document at the same path, or re-file an
   already-catalogued ``(logical_id, version)`` (a clobber).
4. Appends an immutable :class:`CatalogEntry` to the append-only catalog.

It also offers ``find``/``list`` retrieval (by company / owner / kind / logical
id) returning exactly the matching catalog entries.

Why it sits here
----------------
This is the librarian role from the org model: it owns the catalog and enforces
organization so the store can never drift into an unindexed or clobbered state.
Filing and the catalog are deliberately one cohesive responsibility (kept under
300 lines — CLAUDE.md §5.7); the path algebra and record contract live in their
own files.

Security / compliance invariants upheld (CLAUDE.md §5.6)
-------------------------------------------------------
* **Data separation, fail-closed:** every path is resolved through the workspace
  boundary, so a filed document ALWAYS lands under ``.autofirm/`` and never the
  public code tree; a boundary breach raises, never relocates.
* **Never overwrite:** a re-file of an existing ``(logical_id, version)`` is
  refused; a different logical document resolving to an existing path is refused.
  New content means a new version (versioning, not clobber).
* **Append-only catalog:** entries are only ever appended; the catalog exposes no
  update/delete, so the filing history is tamper-evident by construction.
"""

from __future__ import annotations

from dataclasses import dataclass

from autofirm.access.workspace_data_boundary import (
    WorkspaceBoundaryError,
    WorkspaceDataBoundary,
)
from autofirm.document_store.canonical_document_path_scheme import (
    canonical_relative_path_for,
)
from autofirm.document_store.filed_document_record import (
    DeliverableKind,
    FiledDocumentRecord,
)

__all__ = ["CatalogEntry", "LibrarianFilingError", "LibrarianFilingService"]


class LibrarianFilingError(Exception):
    """Raised when a filing is refused by the librarian (fail-closed)."""


@dataclass(frozen=True, slots=True)
class CatalogEntry:
    """One immutable catalog entry: the record plus where it was filed.

    Frozen so a catalogued filing cannot be mutated after the fact, preserving
    the append-only guarantee (the entry is a permanent fact about the store).

    Args:
        record: The validated deliverable record that was filed.
        relative_path: Its canonical relative path within the store.
        absolute_path: Its boundary-resolved absolute path under ``.autofirm/``.
    """

    record: FiledDocumentRecord
    relative_path: str
    absolute_path: str


class LibrarianFilingService:
    """Files deliverables fail-closed and maintains the append-only catalog.

    Args:
        boundary: The workspace boundary that resolves every path UNDER the
            gitignored sensitive root. Injected (the root is the test's
            ``tmp_path`` in tests, the real ``.autofirm/`` in production), so the
            service never reimplements the boundary and never hard-codes a root.
    """

    def __init__(self, boundary: WorkspaceDataBoundary) -> None:
        """Bind to the reused boundary primitive and start an empty catalog."""
        self._boundary = boundary
        # Append-only catalog: only ``file`` ever appends; nothing mutates/removes.
        self._catalog: list[CatalogEntry] = []
        # Index of filed (logical_id, version) -> relative path, for O(1)
        # clobber/collision detection. Mirrors the catalog; never independently
        # mutated to remove entries.
        self._filed_versions: dict[tuple[str, int], str] = {}
        # Reverse index: relative path -> the logical_id that owns it, so a
        # *different* document resolving to an existing path is caught fail-closed.
        self._path_owner: dict[str, str] = {}

    def file(self, record: FiledDocumentRecord) -> CatalogEntry:
        """File ``record`` into the store, fail-closed, and catalog it.

        Args:
            record: The validated deliverable to file.

        Returns:
            The immutable :class:`CatalogEntry` appended to the catalog.

        Raises:
            LibrarianFilingError: If the filing would escape the store boundary,
                clobber an already-filed ``(logical_id, version)``, or collide
                with a *different* logical document at the same path.
        """
        version_key = (record.logical_id, record.version)
        # fail-closed: never overwrite an existing version of this document.
        if version_key in self._filed_versions:
            raise LibrarianFilingError(
                f"document {record.logical_id!r} version {record.version} already filed"
            )

        relative_path = canonical_relative_path_for(record)

        # fail-closed: a different logical document must never map onto a path
        # already owned by another document (would silently clobber it).
        owner = self._path_owner.get(relative_path)
        if owner is not None and owner != record.logical_id:
            raise LibrarianFilingError(
                f"path {relative_path!r} already owned by document {owner!r}"
            )

        # Resolve UNDER the gitignored sensitive root via the reused boundary.
        # A traversal/escape attempt raises WorkspaceBoundaryError -> we refuse.
        try:
            absolute_path = self._boundary.resolve_sensitive_path(relative_path)
        except WorkspaceBoundaryError as exc:  # fail-closed: boundary breach -> refuse
            raise LibrarianFilingError(f"filing breached the store boundary: {exc}") from exc

        entry = CatalogEntry(
            record=record,
            relative_path=relative_path,
            absolute_path=absolute_path,
        )
        # Append-only: commit the entry and update the two indexes together.
        self._catalog.append(entry)
        self._filed_versions[version_key] = relative_path
        self._path_owner[relative_path] = record.logical_id
        return entry

    def list_all(self) -> tuple[CatalogEntry, ...]:
        """Return every catalogued entry in filing order (read-only snapshot)."""
        # Tuple copy so callers cannot mutate the append-only catalog.
        return tuple(self._catalog)

    def find(
        self,
        *,
        company: str | None = None,
        kind: DeliverableKind | None = None,
        logical_id: str | None = None,
    ) -> tuple[CatalogEntry, ...]:
        """Return exactly the entries matching every provided filter (AND).

        Any filter left ``None`` is not applied; with no filters this returns the
        whole catalog. Matching is exact on the record's identity fields, so the
        result is precisely the documents for that company/owner/kind/id.

        Args:
            company: If set, keep only entries whose record's company matches.
            kind: If set, keep only entries of this deliverable kind.
            logical_id: If set, keep only entries for this logical document.

        Returns:
            The matching entries in filing order (possibly empty).
        """
        return tuple(
            entry
            for entry in self._catalog
            if (company is None or entry.record.company == company)
            and (kind is None or entry.record.kind == kind)
            and (logical_id is None or entry.record.logical_id == logical_id)
        )
