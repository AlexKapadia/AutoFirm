"""Teeth-tests for the docx title round-trip extractor (NO tautology).

Proves the extractor re-reads the title from the REAL file bytes — so a clean
build yields ``declared == extracted`` (a genuine round-trip), while a renderer
that dropped or mangled the title would yield a mismatch the SPEC_ROUND_TRIP check
blocks on. Also proves it fails closed on an unreadable / titleless file.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from autofirm.artifacts.business_document_builder import build_business_document
from autofirm.artifacts.business_document_spec import DocumentSection, DocumentSpec
from autofirm.e2e.docx_spec_round_trip_extractor import (
    TITLE_KEY,
    build_document_spec_round_trip,
    extract_document_title,
)
from autofirm.output_review.output_review_errors import OutputReviewError
from autofirm.output_review.reviewable_artifact_contract import (
    ArtifactKind,
    ReviewableArtifact,
)
from autofirm.output_review.spec_artifact_round_trip_check import SpecRoundTripCheck

_TITLE = "Brightcart (E-commerce Retail) Investor Update"


def _docx_with_title(tmp_path: Path, title: str) -> Path:
    spec = DocumentSpec(
        title=title,
        executive_summary="Summary.",
        sections=(DocumentSection("Body", ("a paragraph.",)),),
    )
    return build_business_document(spec, tmp_path / "doc.docx")


def test_extracts_the_exact_title_from_file_bytes(tmp_path: Path) -> None:
    docx = _docx_with_title(tmp_path, _TITLE)
    assert extract_document_title(docx) == _TITLE


def test_round_trip_is_genuine_and_matches(tmp_path: Path) -> None:
    docx = _docx_with_title(tmp_path, _TITLE)
    rt = build_document_spec_round_trip(_TITLE, docx)
    assert rt.declared_values == {TITLE_KEY: _TITLE}
    assert rt.extracted_values == {TITLE_KEY: _TITLE}  # re-read from disk, equal


def test_extracted_is_not_copied_from_declared(tmp_path: Path) -> None:
    # If the declared title differs from what is on disk, the round-trip records
    # the mismatch (extracted comes from the FILE, never from the declared arg).
    docx = _docx_with_title(tmp_path, _TITLE)
    rt = build_document_spec_round_trip("A Different Declared Title", docx)
    assert rt.declared_values == {TITLE_KEY: "A Different Declared Title"}
    assert rt.extracted_values == {TITLE_KEY: _TITLE}
    assert rt.declared_values != rt.extracted_values


def test_genuine_round_trip_passes_the_spec_check(tmp_path: Path) -> None:
    # End-to-end: a true round-trip yields a CLEAN SPEC_ROUND_TRIP verdict, and a
    # tampered declared value yields a BLOCKING finding — proving the round-trip is
    # load-bearing, not decorative.
    docx = _docx_with_title(tmp_path, _TITLE)
    clean = ReviewableArtifact(
        artifact_ref="r@v1",
        kind=ArtifactKind.BUSINESS_DOCUMENT,
        path=docx,
        spec_round_trip=build_document_spec_round_trip(_TITLE, docx),
    )
    assert SpecRoundTripCheck().run(clean) == ()
    tampered = ReviewableArtifact(
        artifact_ref="r@v1",
        kind=ArtifactKind.BUSINESS_DOCUMENT,
        path=docx,
        spec_round_trip=build_document_spec_round_trip("Wrong Title", docx),
    )
    findings = SpecRoundTripCheck().run(tampered)
    assert len(findings) == 1
    assert findings[0].locator == TITLE_KEY


def test_unicode_title_round_trips(tmp_path: Path) -> None:
    # A title with punctuation / non-ascii survives the zip+XML re-read exactly.
    title = "Solaris Grid — Renewable Energy (2026) Report"
    docx = _docx_with_title(tmp_path, title)
    assert extract_document_title(docx) == title


def test_non_docx_file_is_refused(tmp_path: Path) -> None:
    junk = tmp_path / "not.docx"
    junk.write_bytes(b"not a zip")
    with pytest.raises(OutputReviewError) as exc:
        extract_document_title(junk)
    assert "cannot read docx document part" in str(exc.value)


def test_titleless_docx_is_refused(tmp_path: Path) -> None:
    # A valid zip whose document.xml has no Title-styled paragraph -> refuse.
    path = tmp_path / "titleless.docx"
    body = (
        b'<?xml version="1.0"?>'
        b'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        b"<w:body><w:p><w:r><w:t>no title style here</w:t></w:r></w:p></w:body></w:document>"
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("[Content_Types].xml", b"<Types/>")
        archive.writestr("word/document.xml", body)
    with pytest.raises(OutputReviewError) as exc:
        extract_document_title(path)
    assert "no 'Title'-styled paragraph found" in str(exc.value)
