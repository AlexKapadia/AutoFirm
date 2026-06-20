"""Teeth-tests for the stdlib OOXML file-open probe (FILE_OPENS_CLEAN's eyes).

These prove the probe actually distinguishes a clean OOXML container from a
corrupt / non-OOXML one, and — critically — that it NEVER raises (uncertainty
must surface as ``(False, detail)``, the contract FILE_OPENS_CLEAN relies on to
fail closed). Inputs are synthetic zips and a real built ``.docx``; no network.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from autofirm.artifacts.business_document_builder import build_business_document
from autofirm.artifacts.business_document_spec import DocumentSection, DocumentSpec
from autofirm.e2e.zipfile_ooxml_file_open_probe import ZipfileOoxmlFileOpenProbe
from autofirm.output_review.file_opens_clean_check import FileOpenProbe
from autofirm.output_review.reviewable_artifact_contract import ArtifactKind

_CONTENT_TYPES = "[Content_Types].xml"


def _real_docx(tmp_path: Path) -> Path:
    """Render a genuine, non-empty .docx via the real builder."""
    spec = DocumentSpec(
        title="Probe Subject",
        sections=(DocumentSection("Body", ("paragraph one.",)),),
    )
    return build_business_document(spec, tmp_path / "real.docx")


def _zip_with(path: Path, members: dict[str, bytes]) -> Path:
    """Write a zip carrying exactly ``members`` (name -> bytes)."""
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in members.items():
            archive.writestr(name, data)
    return path


def test_real_docx_opens_clean() -> None:
    # A genuinely-built docx is a valid OOXML container -> clean, empty detail.
    import tempfile

    docx = _real_docx(Path(tempfile.mkdtemp()))
    opens_clean, detail = ZipfileOoxmlFileOpenProbe().probe(docx, ArtifactKind.BUSINESS_DOCUMENT)
    assert opens_clean is True
    assert detail == ""


def test_minimal_valid_ooxml_zip_opens_clean(tmp_path: Path) -> None:
    # The minimum a docx needs: the content-types part AND word/document.xml.
    docx = _zip_with(
        tmp_path / "min.docx",
        {_CONTENT_TYPES: b"<Types/>", "word/document.xml": b"<w:document/>"},
    )
    assert ZipfileOoxmlFileOpenProbe().probe(docx, ArtifactKind.BUSINESS_DOCUMENT) == (True, "")


def test_missing_primary_part_is_not_clean(tmp_path: Path) -> None:
    # Has the package marker but NOT the document body part -> blocked, named.
    docx = _zip_with(tmp_path / "noprimary.docx", {_CONTENT_TYPES: b"<Types/>"})
    opens_clean, detail = ZipfileOoxmlFileOpenProbe().probe(docx, ArtifactKind.BUSINESS_DOCUMENT)
    assert opens_clean is False
    assert detail == "missing primary document part word/document.xml"


def test_missing_content_types_is_not_clean(tmp_path: Path) -> None:
    # Has the body part but NOT the OOXML package marker -> blocked, named.
    docx = _zip_with(tmp_path / "noct.docx", {"word/document.xml": b"<w:document/>"})
    opens_clean, detail = ZipfileOoxmlFileOpenProbe().probe(docx, ArtifactKind.BUSINESS_DOCUMENT)
    assert opens_clean is False
    assert detail == "missing OOXML package part [Content_Types].xml"


def test_garbage_bytes_handled_not_raised(tmp_path: Path) -> None:
    # A non-zip file must be reported as not-clean, NEVER raise (fail-closed).
    junk = tmp_path / "garbage.docx"
    junk.write_bytes(b"this is plainly not a zip archive at all")
    opens_clean, detail = ZipfileOoxmlFileOpenProbe().probe(junk, ArtifactKind.BUSINESS_DOCUMENT)
    assert opens_clean is False
    assert detail == "garbage.docx is not a valid OOXML (zip) container"


def test_truncated_zip_handled_not_raised(tmp_path: Path) -> None:
    # Build a valid zip then chop its tail (destroying the central directory).
    full = _zip_with(
        tmp_path / "trunc.docx",
        {_CONTENT_TYPES: b"<Types/>", "word/document.xml": b"<w:document/>"},
    )
    data = full.read_bytes()
    full.write_bytes(data[: len(data) // 2])  # truncate -> no readable EOCD
    opens_clean, detail = ZipfileOoxmlFileOpenProbe().probe(full, ArtifactKind.BUSINESS_DOCUMENT)
    assert opens_clean is False
    assert detail != ""  # a reason is always given


def test_corrupt_member_is_not_clean(tmp_path: Path) -> None:
    # A valid central directory but a member whose stored CRC does not match its
    # bytes -> testzip() names it -> blocked with that member name in the detail.
    path = tmp_path / "badcrc.docx"
    with zipfile.ZipFile(path, "w") as archive:
        info = zipfile.ZipInfo("word/document.xml")
        archive.writestr(info, b"original-bytes")
        archive.writestr(_CONTENT_TYPES, b"<Types/>")
    raw = bytearray(path.read_bytes())
    # Flip a byte inside the first (stored) member's data region to break its CRC.
    raw[40] ^= 0xFF
    path.write_bytes(bytes(raw))
    opens_clean, detail = ZipfileOoxmlFileOpenProbe().probe(path, ArtifactKind.BUSINESS_DOCUMENT)
    assert opens_clean is False
    # testzip() names the corrupt member; the detail pins it exactly.
    assert detail == "corrupt zip member: word/document.xml"


def test_corrupt_central_directory_handled_not_raised(tmp_path: Path) -> None:
    # A valid EOCD (is_zipfile True) but a broken central-directory header makes
    # ZipFile() raise BadZipFile -> the probe catches it and returns it as the
    # detail, NEVER letting the exception escape (the fail-closed except branch).
    path = tmp_path / "badcd.docx"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(_CONTENT_TYPES, b"<Types/>")
        archive.writestr("word/document.xml", b"<w:document/>")
    raw = bytearray(path.read_bytes())
    cd_header = raw.find(b"PK\x01\x02")  # central-directory file header signature
    assert cd_header != -1
    raw[cd_header + 2] = 0xFF  # corrupt the signature so ZipFile() rejects the CD
    path.write_bytes(bytes(raw))
    opens_clean, detail = ZipfileOoxmlFileOpenProbe().probe(path, ArtifactKind.BUSINESS_DOCUMENT)
    assert opens_clean is False
    assert detail == "BadZipFile: Bad magic number for central directory"


def test_missing_file_reported_not_raised(tmp_path: Path) -> None:
    # A path that does not exist must not raise; is_zipfile -> False -> not-clean.
    missing = tmp_path / "nope.docx"
    opens_clean, detail = ZipfileOoxmlFileOpenProbe().probe(missing, ArtifactKind.BUSINESS_DOCUMENT)
    assert opens_clean is False
    assert detail == "nope.docx is not a valid OOXML (zip) container"


@pytest.mark.parametrize(
    ("kind", "primary"),
    [
        (ArtifactKind.FINANCIAL_MODEL, "xl/workbook.xml"),
        (ArtifactKind.SLIDE_DECK, "ppt/presentation.xml"),
    ],
)
def test_kind_specific_primary_part_required(
    tmp_path: Path, kind: ArtifactKind, primary: str
) -> None:
    # The probe requires the PRIMARY part for the requested kind, not docx's.
    ok_zip = _zip_with(tmp_path / f"{kind.value}.zip", {_CONTENT_TYPES: b"<x/>", primary: b"<x/>"})
    assert ZipfileOoxmlFileOpenProbe().probe(ok_zip, kind) == (True, "")
    wrong = _zip_with(
        tmp_path / f"{kind.value}-wrong.zip",
        {_CONTENT_TYPES: b"<x/>", "word/document.xml": b"<x/>"},
    )
    opens_clean, detail = ZipfileOoxmlFileOpenProbe().probe(wrong, kind)
    assert opens_clean is False
    assert detail == f"missing primary document part {primary}"


def test_unknown_kind_is_refused_not_clean(tmp_path: Path) -> None:
    # A kind with no known primary part cannot be affirmed clean (fail-closed).
    valid = _zip_with(tmp_path / "x.zip", {_CONTENT_TYPES: b"<x/>", "word/document.xml": b"<x/>"})
    opens_clean, detail = ZipfileOoxmlFileOpenProbe().probe(valid, "PDF_LIKE")  # type: ignore[arg-type]
    assert opens_clean is False
    assert detail == "no OOXML primary part defined for kind 'PDF_LIKE'"


def test_probe_satisfies_runtime_checkable_protocol() -> None:
    # The probe structurally satisfies the FileOpenProbe seam the gate injects.
    assert isinstance(ZipfileOoxmlFileOpenProbe(), FileOpenProbe)
