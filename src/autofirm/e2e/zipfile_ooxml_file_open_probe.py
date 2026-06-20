"""A stdlib-only FileOpenProbe that proves an OOXML artifact opens un-corrupt.

What this does
--------------
Implements :class:`ZipfileOoxmlFileOpenProbe`, the real
:class:`~autofirm.output_review.file_opens_clean_check.FileOpenProbe` the e2e
delivery gate injects into the FILE_OPENS_CLEAN check. It proves a built ``.docx``
/ ``.xlsx`` / ``.pptx`` actually opens — i.e. the bytes on disk form a valid OOXML
container — *structurally*, using only the standard-library :mod:`zipfile`:

1. the file is a well-formed ZIP whose central directory is intact
   (``zipfile.testzip()`` reports no corrupt member), and
2. it carries the OOXML package marker ``[Content_Types].xml`` AND the part the
   kind's primary document lives in (``word/document.xml`` for a document,
   ``xl/workbook.xml`` for a workbook, ``ppt/presentation.xml`` for a deck).

Why stdlib zipfile, not python-docx
-----------------------------------
This probe needs no OOXML library at all. An OOXML file IS a ZIP, so its
structural validity — "does it open without a repair dialog?" — is fully
checkable with :mod:`zipfile` alone, needing no python-docx/openpyxl/python-pptx
import. Staying stdlib-only keeps the probe portable, network-free, and
dependency-light, which is why it is implemented this way rather than reaching for
a heavy OOXML reader.

Security / compliance invariants upheld (CLAUDE.md §5.6, §3.11)
--------------------------------------------------------------
* **Never raises:** ANY error (not-a-zip, truncated central directory, OS error,
  unknown kind) is caught and returned as ``(False, detail)`` — the check treats a
  raising probe as a defect, and a probe that swallows its own errors keeps that
  contract honest (uncertainty == invalid, never a silent pass).
* **Deterministic:** the same bytes always yield the same ``(opens_clean, detail)``
  — it reads the ZIP directory and a fixed member set, no clock, no randomness.
* **No raw content leaked:** the detail string names the missing member / error
  type only, never the artifact's bytes.
"""

from __future__ import annotations

import zipfile
from typing import TYPE_CHECKING

from autofirm.output_review.reviewable_artifact_contract import ArtifactKind

if TYPE_CHECKING:
    from pathlib import Path

__all__ = ["ZipfileOoxmlFileOpenProbe"]

# Every OOXML package (docx/xlsx/pptx) MUST carry this content-types part; its
# absence means the ZIP is not a valid Office Open XML container at all.
_CONTENT_TYPES_PART = "[Content_Types].xml"

# The primary document part per artifact kind. Presence of this part proves the
# container holds the expected primary document, not merely an arbitrary ZIP.
_PRIMARY_PART_FOR_KIND: dict[ArtifactKind, str] = {
    ArtifactKind.BUSINESS_DOCUMENT: "word/document.xml",
    ArtifactKind.FINANCIAL_MODEL: "xl/workbook.xml",
    ArtifactKind.SLIDE_DECK: "ppt/presentation.xml",
}


class ZipfileOoxmlFileOpenProbe:
    """Structurally verify an OOXML artifact opens clean using only :mod:`zipfile`.

    Satisfies the runtime-checkable
    :class:`~autofirm.output_review.file_opens_clean_check.FileOpenProbe` Protocol.
    Holds no state, so a single instance is safely shared across every review.
    """

    def probe(self, path: Path, kind: ArtifactKind) -> tuple[bool, str]:  # noqa: PLR0911 -- each return is a distinct fail-closed branch; merging them would blur the failure detail
        """Report whether ``path`` opens clean as an OOXML container of ``kind``.

        Args:
            path: On-disk location of the built artifact (the caller guarantees it
                exists before probing).
            kind: The :class:`ArtifactKind`, selecting the required primary part.

        Returns:
            ``(True, "")`` when the file is a valid, non-corrupt OOXML container
            holding both the content-types part and the kind's primary document
            part; otherwise ``(False, detail)`` naming the first failure. NEVER
            raises — any exception becomes ``(False, detail)`` (fail-closed §5.6).
        """
        # fail-closed: an unmappable kind has no known primary part to require, so
        # we cannot affirm it opens clean — refuse rather than guess a member.
        primary_part = _PRIMARY_PART_FOR_KIND.get(kind)
        if primary_part is None:
            return (False, f"no OOXML primary part defined for kind {kind!r}")

        try:
            # fail-closed: a non-ZIP file is not an OOXML package — reject without
            # attempting to open it (open() would raise BadZipFile otherwise).
            if not zipfile.is_zipfile(path):
                return (False, f"{path.name} is not a valid OOXML (zip) container")
            with zipfile.ZipFile(path) as archive:
                # testzip() returns the name of the FIRST corrupt member (bad CRC /
                # truncated), or None when every member's bytes are intact.
                corrupt_member = archive.testzip()
                if corrupt_member is not None:
                    return (False, f"corrupt zip member: {corrupt_member}")
                names = set(archive.namelist())
        except Exception as exc:  # fail-closed: ANY read/parse error == not clean
            # A truncated central directory, an OS error, or any other failure
            # leaves validity unknown — treat unknown as invalid, never as a pass.
            return (False, f"{type(exc).__name__}: {exc}")

        if _CONTENT_TYPES_PART not in names:
            return (False, f"missing OOXML package part {_CONTENT_TYPES_PART}")
        if primary_part not in names:
            return (False, f"missing primary document part {primary_part}")
        return (True, "")
