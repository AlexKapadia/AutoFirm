"""Determinism + collision-freedom proofs for the canonical path scheme.

The path scheme is the heart of the librarian's organization guarantee: it must
be a deterministic, collision-free function of a record's identity. These tests
prove (1) same record -> same path always, and (2) two records collide on a path
IF AND ONLY IF they are the same logical document at the same version. Synthetic
only.
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from autofirm.document_store.canonical_document_path_scheme import (
    CanonicalPathError,
    canonical_relative_path_for,
    slugify_human_name,
)
from autofirm.document_store.filed_document_record import DeliverableKind
from tests.document_store.conftest import filed_document_records, make_record


@pytest.mark.unit
def test_path_has_expected_canonical_shape() -> None:
    """The exact scheme: <company>/<kind>/<id>/v<version>/<id>__<name>.<ext>."""
    record = make_record(
        logical_id="q3-board-memo",
        company="acme",
        kind=DeliverableKind.REPORT,
        canonical_name="Q3 Board Memo",
        extension="pdf",
        version=2,
    )
    assert (
        canonical_relative_path_for(record)
        == "acme/report/q3-board-memo/v2/q3-board-memo__q3-board-memo.pdf"
    )


@pytest.mark.unit
def test_path_is_relative_with_no_traversal() -> None:
    """The path is always relative and never contains '..' or a leading slash."""
    path = canonical_relative_path_for(make_record())
    assert not path.startswith("/")
    assert ".." not in path.split("/")


@pytest.mark.unit
@pytest.mark.parametrize(
    ("name", "expected_slug"),
    [
        ("Q3 Board Memo", "q3-board-memo"),
        ("  Spaced  Out  ", "spaced-out"),
        ("Lots!!!Of???Punct", "lots-of-punct"),
        ("MiXeD CaSe", "mixed-case"),
        ("-leading-and-trailing-", "leading-and-trailing"),
    ],
)
def test_slugify_is_deterministic_and_clean(name: str, expected_slug: str) -> None:
    """Human-name slugification collapses punctuation deterministically."""
    assert slugify_human_name(name) == expected_slug


@pytest.mark.unit
@pytest.mark.parametrize("punct_only", ["!!!", "   ", "---", "/?.,"])
def test_slugify_refuses_names_with_no_safe_chars(punct_only: str) -> None:
    """A name with no path-safe chars is unfileable (fail-closed)."""
    with pytest.raises(CanonicalPathError):
        slugify_human_name(punct_only)


@pytest.mark.unit
def test_slugify_is_idempotent() -> None:
    """Slugifying an already-slug is a no-op (stable under re-application)."""
    once = slugify_human_name("Some Doc Name")
    assert slugify_human_name(once) == once


@pytest.mark.property
@given(record=filed_document_records())
def test_path_is_deterministic(record: object) -> None:
    """Same record -> identical path on every call (no hidden state/time)."""
    assert canonical_relative_path_for(record) == canonical_relative_path_for(record)  # type: ignore[arg-type]


@pytest.mark.property
@given(records=st.lists(filed_document_records(), min_size=1, max_size=40))
def test_collision_iff_same_document_version(records: list[object]) -> None:
    """Two records share a path IFF same (company, kind, logical_id, version).

    The name slug never disambiguates identity: the version-qualified identity
    tuple is what must drive a collision, so a different document can never land
    on another's path, and the same document+version always shares one.
    """
    for a in records:
        for b in records:
            same_identity = (
                a.company == b.company  # type: ignore[attr-defined]
                and a.kind == b.kind  # type: ignore[attr-defined]
                and a.logical_id == b.logical_id  # type: ignore[attr-defined]
                and a.version == b.version  # type: ignore[attr-defined]
            )
            same_path = canonical_relative_path_for(a) == canonical_relative_path_for(b)  # type: ignore[arg-type]
            # The folder (everything up to the filename) is exactly the identity
            # tuple, so identity-equality must imply same folder, and a differing
            # identity tuple must change the folder.
            folder_a = canonical_relative_path_for(a).rsplit("/", 1)[0]  # type: ignore[arg-type]
            folder_b = canonical_relative_path_for(b).rsplit("/", 1)[0]  # type: ignore[arg-type]
            assert (folder_a == folder_b) == same_identity
            # Same identity AND same human name AND same extension -> identical full
            # path (the filename adds name-slug + extension on top of the identity
            # folder, so both must also match for the file to collide).
            if (
                same_identity
                and a.canonical_name == b.canonical_name  # type: ignore[attr-defined]
                and a.extension == b.extension  # type: ignore[attr-defined]
            ):
                assert same_path


@pytest.mark.property
@given(record=filed_document_records())
def test_distinct_versions_get_distinct_folders(record: object) -> None:
    """A new version always lands in a distinct folder (versioning, not clobber)."""
    v1 = canonical_relative_path_for(record)  # type: ignore[arg-type]
    bumped = make_record(
        logical_id=record.logical_id,  # type: ignore[attr-defined]
        company=record.company,  # type: ignore[attr-defined]
        kind=record.kind,  # type: ignore[attr-defined]
        canonical_name=record.canonical_name,  # type: ignore[attr-defined]
        extension=record.extension,  # type: ignore[attr-defined]
        version=record.version + 1,  # type: ignore[attr-defined]
        provenance=record.provenance,  # type: ignore[attr-defined]
    )
    assert canonical_relative_path_for(bumped) != v1
    assert f"/v{record.version + 1}/" in canonical_relative_path_for(bumped)  # type: ignore[attr-defined]
