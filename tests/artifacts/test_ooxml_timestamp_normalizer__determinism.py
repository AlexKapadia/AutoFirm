"""Tests for the OOXML timestamp normaliser (the determinism backstop).

These assert the normaliser actually pins the ``modified`` field and ZIP member
dates, leaves content untouched, and is idempotent — the property the xlsx/docx
builders rely on for byte-stable output (CLAUDE.md §3.6).
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from autofirm.artifacts.deterministic_document_properties import FIXED_TIMESTAMP
from autofirm.artifacts.ooxml_timestamp_normalizer import (
    _FIXED_ZIP_DATE,
    normalize_ooxml_timestamps,
)

_CORE_BEFORE = (
    b'<cp:coreProperties xmlns:cp="x" xmlns:dcterms="y">'
    b"<dcterms:created>2024-01-01T00:00:00Z</dcterms:created>"
    b"<dcterms:modified>2099-12-31T23:59:59Z</dcterms:modified>"
    b"</cp:coreProperties>"
)


def _make_package(path: Path, *, modified_payload: bytes = _CORE_BEFORE) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as out:
        info = zipfile.ZipInfo("docProps/core.xml", date_time=(2030, 5, 5, 5, 5, 5))
        out.writestr(info, modified_payload)
        body = zipfile.ZipInfo("word/document.xml", date_time=(2030, 5, 5, 5, 5, 5))
        out.writestr(body, b"<body>content</body>")


def test_modified_field_pinned_to_fixed_epoch(tmp_path: Path) -> None:
    pkg = tmp_path / "p.docx"
    _make_package(pkg)
    normalize_ooxml_timestamps(pkg)
    core = zipfile.ZipFile(pkg).read("docProps/core.xml")
    fixed = FIXED_TIMESTAMP.strftime("%Y-%m-%dT%H:%M:%SZ").encode()
    assert b"<dcterms:modified>" + fixed + b"</dcterms:modified>" in core
    assert b"2099-12-31" not in core  # the old value is gone


def test_created_field_left_untouched(tmp_path: Path) -> None:
    pkg = tmp_path / "p.docx"
    _make_package(pkg)
    normalize_ooxml_timestamps(pkg)
    core = zipfile.ZipFile(pkg).read("docProps/core.xml")
    # Only `modified` is rewritten — the created value must survive verbatim.
    assert b"<dcterms:created>2024-01-01T00:00:00Z</dcterms:created>" in core


def test_content_parts_left_untouched(tmp_path: Path) -> None:
    pkg = tmp_path / "p.docx"
    _make_package(pkg)
    normalize_ooxml_timestamps(pkg)
    assert zipfile.ZipFile(pkg).read("word/document.xml") == b"<body>content</body>"


def test_zip_member_dates_pinned(tmp_path: Path) -> None:
    pkg = tmp_path / "p.docx"
    _make_package(pkg)
    normalize_ooxml_timestamps(pkg)
    for info in zipfile.ZipFile(pkg).infolist():
        assert info.date_time == _FIXED_ZIP_DATE


def test_idempotent(tmp_path: Path) -> None:
    pkg = tmp_path / "p.docx"
    _make_package(pkg)
    normalize_ooxml_timestamps(pkg)
    first = pkg.read_bytes()
    normalize_ooxml_timestamps(pkg)
    assert pkg.read_bytes() == first  # a second pass changes nothing


def test_package_without_core_part_is_handled(tmp_path: Path) -> None:
    # A package lacking docProps/core.xml must still normalise (member dates) and
    # not raise — the core-rewrite branch is simply skipped.
    pkg = tmp_path / "p.xlsx"
    with zipfile.ZipFile(pkg, "w") as out:
        out.writestr(
            zipfile.ZipInfo("xl/workbook.xml", date_time=(2030, 1, 1, 1, 1, 1)), b"<wb/>"
        )
    normalize_ooxml_timestamps(pkg)
    info = zipfile.ZipFile(pkg).infolist()[0]
    assert info.date_time == _FIXED_ZIP_DATE


@pytest.mark.parametrize(
    "modified_payload",
    [
        b'<cp:coreProperties xmlns:dcterms="y">'
        b'<dcterms:modified xsi:type="dcterms:W3CDTF">2050-01-01T00:00:00Z</dcterms:modified>'
        b"</cp:coreProperties>",
    ],
)
def test_modified_with_attributes_still_pinned(tmp_path: Path, modified_payload: bytes) -> None:
    # The modified element carries attributes in real OOXML — the regex must still
    # match and rewrite only the inner text, preserving the attributes.
    pkg = tmp_path / "p.docx"
    _make_package(pkg, modified_payload=modified_payload)
    normalize_ooxml_timestamps(pkg)
    core = zipfile.ZipFile(pkg).read("docProps/core.xml")
    assert b'xsi:type="dcterms:W3CDTF"' in core  # attribute survives
    assert b"2050-01-01" not in core  # value rewritten
