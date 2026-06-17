"""Boundary-exact, fail-closed validation tests for FiledDocumentRecord.

Proves the record contract refuses malformed identity/content fields at
construction (so a bad record can never reach the librarian) and accepts exactly
the valid shapes. Synthetic only.
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from autofirm.document_store.filed_document_record import (
    DeliverableKind,
    FiledDocumentRecord,
)
from tests.document_store.conftest import FIXED_NOW, filed_document_records, make_record


@pytest.mark.unit
def test_valid_record_constructs_and_is_frozen() -> None:
    """A well-formed record builds and is immutable (frozen)."""
    record = make_record()
    assert record.logical_id == "doc-1"
    assert record.kind is DeliverableKind.REPORT
    with pytest.raises(ValidationError):  # frozen: identity cannot mutate
        record.version = 2


@pytest.mark.unit
@pytest.mark.parametrize(
    "bad",
    [
        "Doc-1",  # uppercase not allowed in a slug
        "-leading",  # must start with alnum
        "_leading",  # must start with alnum
        "a/b",  # separator: path-injection guard
        "a..b",  # dot-dot fragment: traversal guard
        "a b",  # whitespace
        "",  # empty
    ],
)
def test_logical_id_rejects_non_slug(bad: str) -> None:
    """Identity fields that form a path are constrained to safe slugs (fail-closed)."""
    with pytest.raises(ValidationError):
        make_record(logical_id=bad)


@pytest.mark.unit
@pytest.mark.parametrize("bad", ["a/b", "..", "x ", "Up", ""])
def test_company_rejects_non_slug(bad: str) -> None:
    """Company is a path segment too — same slug guard."""
    with pytest.raises(ValidationError):
        make_record(company=bad)


@pytest.mark.unit
@pytest.mark.parametrize("bad", ["", "   ", "\t\n"])
def test_blank_canonical_name_and_provenance_refused(bad: str) -> None:
    """Free-text fields refuse blank/whitespace-only values (content gap)."""
    with pytest.raises(ValidationError):
        make_record(canonical_name=bad)
    with pytest.raises(ValidationError):
        make_record(provenance=bad)


@pytest.mark.unit
@pytest.mark.parametrize("bad_version", [0, -1, -100])
def test_version_must_be_positive(bad_version: int) -> None:
    """Version is 1-based; zero/negative is refused (boundary-exact: ge=1)."""
    with pytest.raises(ValidationError):
        make_record(version=bad_version)


@pytest.mark.unit
def test_version_one_is_the_accepted_lower_boundary() -> None:
    """Just-on-the-boundary: version 1 is valid."""
    assert make_record(version=1).version == 1


@pytest.mark.unit
@pytest.mark.parametrize("bad_ext", ["", "PDF", "a.b", "x" * 13, "do/c"])
def test_extension_must_be_short_lowercase_alnum(bad_ext: str) -> None:
    """Extension is a slug-safe, <=12-char fragment (path-safe filename)."""
    with pytest.raises(ValidationError):
        make_record(extension=bad_ext)


@pytest.mark.unit
def test_unknown_kind_is_refused() -> None:
    """Kind is a closed enum — an unknown bucket is refused (fail-closed)."""
    with pytest.raises(ValidationError):
        FiledDocumentRecord(
            logical_id="d",
            company="c",
            kind="spreadsheet",  # type: ignore[arg-type]
            canonical_name="X",
            extension="pdf",
            version=1,
            provenance="p",
            created_at=FIXED_NOW,
        )


@pytest.mark.unit
def test_extra_fields_forbidden() -> None:
    """extra='forbid': an unexpected field is refused, not silently dropped."""
    with pytest.raises(ValidationError):
        FiledDocumentRecord(
            logical_id="d",
            company="c",
            kind=DeliverableKind.DOC,
            canonical_name="X",
            extension="pdf",
            version=1,
            provenance="p",
            created_at=FIXED_NOW,
            unexpected="boom",  # type: ignore[call-arg]
        )


@pytest.mark.property
@given(record=filed_document_records())
def test_arbitrary_valid_records_construct(record: FiledDocumentRecord) -> None:
    """Every drawn record from the valid strategy actually constructs."""
    assert record.version >= 1
    assert record.kind in set(DeliverableKind)


@pytest.mark.property
@given(version=st.integers(max_value=0))
def test_no_nonpositive_version_ever_constructs(version: int) -> None:
    """Property: no version <= 0 is ever accepted."""
    with pytest.raises(ValidationError):
        make_record(version=version)
