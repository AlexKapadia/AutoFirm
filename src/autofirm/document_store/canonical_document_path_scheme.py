"""The deterministic, collision-free naming + foldering scheme for the store.

What this does
--------------
Maps a :class:`autofirm.document_store.filed_document_record.FiledDocumentRecord`
to a single canonical RELATIVE path within the store. The scheme is a pure
function of the record's identity fields, so it is deterministic (the same record
always maps to the same path — CLAUDE.md §3.11) and **collision-free**: two
records map to the same path IF AND ONLY IF they are the same logical document at
the same version, never otherwise.

The scheme
----------
``<company>/<kind>/<logical_id>/v<version>/<logical_id>__<slugified-name>.<ext>``

* ``company`` then ``kind`` then ``logical_id`` give a clean, browsable tree
  grouped by owner and deliverable type (DAMA-DMBOK organized store, A6.4 §07).
* ``v<version>`` isolates each version in its own folder — a new version is a new
  path, so a re-file NEVER overwrites a prior version (versioning, not clobber).
* The filename embeds the (already path-safe) ``logical_id`` plus a slugified,
  lossless-enough rendering of the human ``canonical_name`` for readability.

Why a separate module
----------------------
Isolating the path algebra from the filing service lets it be property-tested in
isolation (determinism + collision-freedom over arbitrary record batches) and
keeps each file single-responsibility and well under 300 lines (CLAUDE.md §5.7).

Security / compliance invariants upheld (CLAUDE.md §5.6)
-------------------------------------------------------
* The result is always a RELATIVE path with no ``..`` and no leading separator —
  it is built only from slug-validated identity fields, so it cannot escape the
  store. The workspace boundary re-checks this when the filing service resolves
  it (defence-in-depth — never trust a single layer).
"""

from __future__ import annotations

import re

from autofirm.document_store.filed_document_record import FiledDocumentRecord

__all__ = ["CanonicalPathError", "canonical_relative_path_for", "slugify_human_name"]

# Collapse any run of non-slug characters in a human name to a single hyphen, so
# the filename stays path-safe and stable regardless of punctuation/whitespace.
_NON_SLUG_RUN = re.compile(r"[^a-z0-9]+")


class CanonicalPathError(Exception):
    """Raised when a record cannot be mapped to a canonical path (fail-closed)."""


def slugify_human_name(name: str) -> str:
    """Render a human ``canonical_name`` into a stable, path-safe slug fragment.

    Lowercases, replaces every run of non-``[a-z0-9]`` characters with a single
    hyphen, and trims leading/trailing hyphens. Deterministic and idempotent.

    Raises:
        CanonicalPathError: If the name slugifies to empty (e.g. it was made up
            entirely of punctuation) — fail-closed, since an empty filename
            fragment would make two differently-named docs collide.
    """
    slug = _NON_SLUG_RUN.sub("-", name.strip().lower()).strip("-")
    if not slug:  # fail-closed: a name with no path-safe characters is unfileable
        raise CanonicalPathError(f"canonical_name {name!r} has no path-safe characters")
    return slug


def canonical_relative_path_for(record: FiledDocumentRecord) -> str:
    """Return the canonical RELATIVE store path for ``record`` (POSIX style).

    Pure function of the record's identity fields. Determinism and
    collision-freedom hold because the path is the version-qualified tuple
    ``(company, kind, logical_id, version)`` plus a name slug — equal tuples give
    equal paths, and unequal version-qualified tuples give distinct folders.

    Args:
        record: The validated deliverable record to place.

    Returns:
        A relative POSIX path such as
        ``acme/report/q3-board-memo/v2/q3-board-memo__q3-board-memo.pdf``.

    Raises:
        CanonicalPathError: If the human name cannot be slugified (fail-closed).
    """
    name_slug = slugify_human_name(record.canonical_name)
    filename = f"{record.logical_id}__{name_slug}.{record.extension}"
    # All segments below are slug-validated (record contract) or fixed literals,
    # so the joined path is relative, free of '..', and cannot escape the store.
    return "/".join(
        (
            record.company,
            record.kind.value,
            record.logical_id,
            f"v{record.version}",
            filename,
        )
    )
