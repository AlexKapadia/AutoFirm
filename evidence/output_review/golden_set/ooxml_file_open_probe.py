"""A real, deterministic FileOpenProbe for the golden-set efficacy harness.

What this does
--------------
Implements :class:`OoxmlFileOpenProbe`, a concrete
:class:`~autofirm.output_review.file_opens_clean_check.FileOpenProbe` the efficacy
harness injects into the default gate. Unlike a unit-test stub that returns a
canned boolean, this probe *actually opens the bytes on disk* and decides validity
structurally, so the FILE_OPENS_CLEAN detection rate the harness reports is a real
measurement, not a hand-asserted constant:

* OOXML kinds (FINANCIAL_MODEL -> xlsx, SLIDE_DECK -> pptx, BUSINESS_DOCUMENT ->
  docx): valid iff the file is a readable ZIP container that holds the mandatory
  ``[Content_Types].xml`` part every OOXML package must carry (ECMA-376 §10). A
  truncated / garbage file fails :func:`zipfile.is_zipfile` or lacks the part.

Why it lives in evidence/, not src/
-----------------------------------
This is analysis-only scaffolding (CLAUDE.md §3.10): it exercises the *runtime*
gate over a synthetic corpus but is never imported by any runtime module, so it
stays outside the import-linter runtime closure. It uses only the standard library
(no plotting deps), so it imports cleanly wherever the harness runs.

No real data (CLAUDE.md §3.12)
------------------------------
The files it opens are synthetic minimal OOXML containers the corpus builder
writes; it never reads real client artifacts.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

from autofirm.output_review.reviewable_artifact_contract import ArtifactKind

__all__ = ["OoxmlFileOpenProbe", "write_valid_ooxml", "write_corrupt_ooxml"]

# The one part every OOXML package MUST contain (ECMA-376 / ISO-29500 §10). Its
# presence is the cheapest deterministic proxy for "a real office app would open
# this without a repair dialog" — exactly what FILE_OPENS_CLEAN must catch.
_CONTENT_TYPES_PART = "[Content_Types].xml"

# A minimal but structurally-valid [Content_Types].xml body. Synthetic, fixed bytes
# -> the corpus is byte-for-byte reproducible (determinism, CLAUDE.md §3.11).
_MINIMAL_CONTENT_TYPES = (
    b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    b'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    b'<Default Extension="xml" ContentType="application/xml"/>'
    b"</Types>"
)


class OoxmlFileOpenProbe:
    """Open an artifact file and report whether it is a clean OOXML container.

    Satisfies the runtime ``FileOpenProbe`` protocol. Pure and deterministic: the
    same bytes always yield the same ``(opens_clean, detail)`` pair, so repeated
    gate runs over one corpus produce byte-identical verdicts.
    """

    def probe(self, path: Path, kind: ArtifactKind) -> tuple[bool, str]:
        """Return ``(opens_clean, detail)`` by structurally opening ``path``.

        Args:
            path: On-disk location of the synthetic artifact (the check guarantees
                it exists before calling, so a missing file is not handled here).
            kind: The artifact kind (all three supported kinds are OOXML packages).

        Returns:
            ``(True, "")`` when the file is a readable ZIP carrying the mandatory
            ``[Content_Types].xml`` part; ``(False, <reason>)`` otherwise. Any
            exception is converted to a ``False`` result with a bounded reason, so
            the probe never raises (the check would block on a raise anyway, but a
            clean boolean keeps the measured signal precise).
        """
        try:
            if not zipfile.is_zipfile(path):
                return (False, f"not a valid OOXML/ZIP container: {path.name}")
            with zipfile.ZipFile(path) as bundle:
                names = set(bundle.namelist())
                if _CONTENT_TYPES_PART not in names:
                    return (False, f"OOXML package missing {_CONTENT_TYPES_PART}")
                bad = bundle.testzip()  # CRC-checks every member; None == all intact
                if bad is not None:
                    return (False, f"corrupt member in OOXML package: {bad}")
        except (OSError, zipfile.BadZipFile) as exc:  # bounded, never re-raised
            return (False, f"{type(exc).__name__} opening {path.name}")
        return (True, "")


def write_valid_ooxml(path: Path) -> None:
    """Write a minimal, structurally-valid OOXML container to ``path``.

    A ZIP holding ``[Content_Types].xml`` — enough for the probe to read it as a
    clean package, standing in for any well-formed xlsx/pptx/docx the builders emit.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, mode="w", compression=zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr(_CONTENT_TYPES_PART, _MINIMAL_CONTENT_TYPES)


def write_corrupt_ooxml(path: Path) -> None:
    """Write deliberately corrupt bytes (a planted FILE_OPENS_CLEAN defect).

    Not a ZIP at all — the bytes a truncated render or a half-flushed write would
    leave on disk, which a real office app would refuse to open without repair.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    # Leading "PK" mimics a ZIP signature so the corruption is non-trivial, then the
    # stream is truncated garbage -> is_zipfile / ZipFile both reject it.
    path.write_bytes(b"PK\x03\x04 truncated-render-not-a-real-ooxml-package \x00\xff")
