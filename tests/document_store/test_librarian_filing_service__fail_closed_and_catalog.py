"""Fail-closed filing, append-only catalog, and retrieval tests for the librarian.

Proves: every filing resolves UNDER the store boundary (data separation); a
re-file of an existing (logical_id, version) is refused (never overwrite); a
different document colliding on a path is refused; the catalog is append-only and
complete; and find/list return exactly the matching documents. All over a
tmp_path boundary — NEVER the real ``.autofirm/``. Synthetic only.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from autofirm.access.workspace_data_boundary import (
    SENSITIVE_WORKSPACE_DIRNAME,
    WorkspaceDataBoundary,
)
from autofirm.document_store.canonical_document_path_scheme import (
    canonical_relative_path_for,
)
from autofirm.document_store.filed_document_record import DeliverableKind
from autofirm.document_store.librarian_filing_service import (
    LibrarianFilingError,
    LibrarianFilingService,
)
from tests.document_store.conftest import filed_document_records, make_record

# A synthetic, POSIX-absolute store root for the property tests, which build a
# fresh librarian per example (so they cannot share a function-scoped fixture).
# Pure-path only — no filesystem I/O, never the real .autofirm/.
_PBT_ROOT = f"/synthetic-store/pbt/workspace/{SENSITIVE_WORKSPACE_DIRNAME}"
_PBT_REPO = "/synthetic-store/pbt/code_repo"


def _fresh_librarian() -> tuple[LibrarianFilingService, str]:
    """Build a brand-new librarian over the synthetic store root (per example)."""
    boundary = WorkspaceDataBoundary(workspace_root=_PBT_ROOT, code_repo_root=_PBT_REPO)
    return LibrarianFilingService(boundary), _PBT_ROOT


@pytest.mark.unit
def test_filing_lands_under_the_sensitive_root(
    librarian: LibrarianFilingService, sensitive_root: str
) -> None:
    """A filed document's absolute path is under the gitignored .autofirm/ root."""
    entry = librarian.file(make_record())
    assert entry.absolute_path.startswith(sensitive_root + "/")
    assert entry.relative_path == canonical_relative_path_for(entry.record)


@pytest.mark.unit
def test_refile_same_version_is_refused(librarian: LibrarianFilingService) -> None:
    """Re-filing the same (logical_id, version) is refused (never overwrite)."""
    librarian.file(make_record(version=1))
    with pytest.raises(LibrarianFilingError, match="already filed"):
        librarian.file(make_record(version=1, canonical_name="Different Name"))


@pytest.mark.unit
def test_new_version_of_same_document_is_allowed(
    librarian: LibrarianFilingService,
) -> None:
    """A higher version of the same document files into its own folder."""
    librarian.file(make_record(version=1))
    entry2 = librarian.file(make_record(version=2))
    assert "/v2/" in entry2.relative_path
    assert len(librarian.list_all()) == 2


@pytest.mark.unit
def test_distinct_documents_never_share_a_path_via_scheme() -> None:
    """The scheme alone guarantees two distinct documents get distinct paths."""
    a = make_record(logical_id="alpha", version=1)
    b = make_record(logical_id="beta", version=1)
    assert canonical_relative_path_for(a) != canonical_relative_path_for(b)


@pytest.mark.security
def test_different_document_colliding_on_path_is_refused(
    monkeypatch: pytest.MonkeyPatch, librarian: LibrarianFilingService
) -> None:
    """A DIFFERENT logical document mapping onto a taken path is refused.

    The scheme makes this impossible normally (logical_id is in the path), so we
    force a path collision via monkeypatch to prove the reverse-index guard fires
    fail-closed (defence-in-depth) rather than silently clobbering the owner.
    """
    import autofirm.document_store.librarian_filing_service as svc

    shared = "acme/report/shared/v1/x.pdf"
    monkeypatch.setattr(svc, "canonical_relative_path_for", lambda _r: shared)
    librarian.file(make_record(logical_id="alpha", version=1))
    with pytest.raises(LibrarianFilingError, match="already owned by document"):
        librarian.file(make_record(logical_id="beta", version=1))


@pytest.mark.security
def test_boundary_escape_is_refused_as_filing_error(
    monkeypatch: pytest.MonkeyPatch, librarian: LibrarianFilingService
) -> None:
    """A path-scheme result that escapes the boundary is refused fail-closed.

    We force the path scheme to emit a traversal path; the boundary raises and the
    librarian must translate it into a LibrarianFilingError (never proceed).
    """
    import autofirm.document_store.librarian_filing_service as svc

    monkeypatch.setattr(svc, "canonical_relative_path_for", lambda _r: "../escape.pdf")
    with pytest.raises(LibrarianFilingError, match="breached the store boundary"):
        librarian.file(make_record())


@pytest.mark.security
def test_absolute_path_from_scheme_is_refused(
    monkeypatch: pytest.MonkeyPatch, librarian: LibrarianFilingService
) -> None:
    """An absolute path from the scheme is refused by the boundary, fail-closed."""
    import autofirm.document_store.librarian_filing_service as svc

    monkeypatch.setattr(svc, "canonical_relative_path_for", lambda _r: "/etc/passwd")
    with pytest.raises(LibrarianFilingError):
        librarian.file(make_record())


@pytest.mark.unit
def test_catalog_is_append_only_snapshot(librarian: LibrarianFilingService) -> None:
    """list_all returns a snapshot tuple that cannot mutate the catalog."""
    librarian.file(make_record(logical_id="a", version=1))
    snapshot = librarian.list_all()
    assert isinstance(snapshot, tuple)
    librarian.file(make_record(logical_id="b", version=1))
    # The earlier snapshot is unchanged; the live catalog grew.
    assert len(snapshot) == 1
    assert len(librarian.list_all()) == 2


@pytest.mark.unit
def test_find_filters_by_company_kind_and_id(librarian: LibrarianFilingService) -> None:
    """Find returns exactly the entries matching every provided filter (AND)."""
    librarian.file(make_record(logical_id="r1", company="acme", kind=DeliverableKind.REPORT))
    librarian.file(make_record(logical_id="m1", company="acme", kind=DeliverableKind.MODEL))
    librarian.file(make_record(logical_id="r2", company="globex", kind=DeliverableKind.REPORT))

    acme = librarian.find(company="acme")
    assert {e.record.logical_id for e in acme} == {"r1", "m1"}

    acme_reports = librarian.find(company="acme", kind=DeliverableKind.REPORT)
    assert {e.record.logical_id for e in acme_reports} == {"r1"}

    just_r2 = librarian.find(logical_id="r2")
    assert {e.record.logical_id for e in just_r2} == {"r2"}

    assert librarian.find() == librarian.list_all()
    assert librarian.find(company="nobody") == ()


@pytest.mark.property
@settings(max_examples=120)
@given(records=st.lists(filed_document_records(), min_size=0, max_size=25))
def test_append_only_and_complete_over_batches(records: list[object]) -> None:
    """Property: catalog grows by exactly the records accepted, in order, complete.

    Filing an arbitrary batch (with possible duplicate identities) yields a
    catalog whose entries are exactly the ACCEPTED filings in filing order, every
    one resolved under the store, and never an overwrite of a prior version.
    """
    librarian, _ = _fresh_librarian()
    accepted: list[object] = []
    seen_versions: set[tuple[str, int]] = set()
    for record in records:
        key = (record.logical_id, record.version)  # type: ignore[attr-defined]
        if key in seen_versions:
            # Duplicate identity+version must be refused (never overwrite).
            with pytest.raises(LibrarianFilingError):
                librarian.file(record)  # type: ignore[arg-type]
            continue
        entry = librarian.file(record)  # type: ignore[arg-type]
        seen_versions.add(key)
        accepted.append(record)
        # Data separation: every accepted filing resolves under the store.
        assert entry.relative_path == canonical_relative_path_for(record)  # type: ignore[arg-type]

    catalog = librarian.list_all()
    # Complete + ordered: the catalog is exactly the accepted records, in order.
    assert [e.record for e in catalog] == accepted
    # Retrieval completeness: every accepted record is findable by its id.
    for record in accepted:
        found = librarian.find(logical_id=record.logical_id)  # type: ignore[attr-defined]
        assert any(e.record is record for e in found)


@pytest.mark.property
@given(records=st.lists(filed_document_records(), min_size=1, max_size=25))
def test_every_filing_resolves_under_store_or_is_refused(records: list[object]) -> None:
    """Property: an accepted filing is ALWAYS under the store; nothing escapes."""
    librarian, sensitive_root = _fresh_librarian()
    for record in records:
        try:
            entry = librarian.file(record)  # type: ignore[arg-type]
        except LibrarianFilingError:
            continue  # refused filings never land anywhere — acceptable
        assert entry.absolute_path.startswith(sensitive_root + "/")
        assert ".." not in entry.absolute_path.split("/")
