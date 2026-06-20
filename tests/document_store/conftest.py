"""Synthetic fixtures + Hypothesis strategies for the document-store suite.

Provides a deterministic clock, a boundary bound to a per-test ``tmp_path``
sensitive root (so tests NEVER write into the real ``.autofirm/``), a librarian
service over that boundary, and strategies that build valid/varied
:class:`FiledDocumentRecord` batches for property-based testing.

Synthetic only — no network, no real PII/company-confidential data, no real
store root. The boundary's sensitive root and code-repo anchor are both fabricated
under ``tmp_path``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import PurePosixPath

import pytest
from hypothesis import strategies as st

from autofirm.access.workspace_data_boundary import (
    SENSITIVE_WORKSPACE_DIRNAME,
    WorkspaceDataBoundary,
)
from autofirm.document_store.filed_document_record import (
    DeliverableKind,
    FiledDocumentRecord,
)
from autofirm.document_store.librarian_filing_service import (
    LibrarianFilingService,
    release_artifact_ref_for,
)
from autofirm.output_review.release_decision_gate import ReleaseDecision
from autofirm.output_review.review_verdict_contract import ReviewVerdict

# A fixed UTC instant so created_at is deterministic in assertions.
FIXED_NOW = datetime(2026, 6, 16, 12, 0, 0, tzinfo=UTC)


def authorised_release_for(record: FiledDocumentRecord) -> ReleaseDecision:
    """An authorised release bound to ``record``'s identity (synthetic, no review IO).

    Builds a clean (no-finding => passing) verdict over the record's release ref and
    derives an authorised decision from it, so the librarian's admission guard admits
    a genuine, ref-matching release. Used by the suite to file the happy path; the
    P4 seam tests build deliberately-wrong decisions inline to prove the refusals.
    """
    ref = release_artifact_ref_for(record)
    verdict = ReviewVerdict(artifact_ref=ref, findings=(), reviewed_at=FIXED_NOW)
    return ReleaseDecision(
        artifact_ref=ref,
        final_verdict=verdict,
        reason="synthetic authorised release for filing test",
        decided_at=FIXED_NOW,
    )


@pytest.fixture
def _unique_segment(tmp_path: object) -> str:
    """A per-test-unique, slug-safe segment derived from tmp_path's basename.

    Used to isolate each test's synthetic store root from every other test's,
    without ever using the real on-disk ``.autofirm/`` location.
    """
    return PurePosixPath(str(tmp_path).replace("\\", "/")).name


@pytest.fixture
def sensitive_root(_unique_segment: str) -> str:
    """A fabricated, POSIX-absolute, gitignored sensitive store root (synthetic).

    The boundary reasons over pure POSIX paths and performs NO filesystem I/O, so
    a synthetic ``/.../.autofirm`` root that ends in the required dir name and is
    unique per test keeps every test fully isolated from the real workspace while
    satisfying the boundary contract. Nothing is ever written to disk here.
    """
    return f"/synthetic-store/{_unique_segment}/workspace/{SENSITIVE_WORKSPACE_DIRNAME}"


@pytest.fixture
def code_repo_root(_unique_segment: str) -> str:
    """A fabricated POSIX-absolute code-repo anchor that does NOT contain the root."""
    return f"/synthetic-store/{_unique_segment}/code_repo"


@pytest.fixture
def boundary(sensitive_root: str, code_repo_root: str) -> WorkspaceDataBoundary:
    """A boundary bound to the per-test fabricated roots (reused primitive)."""
    return WorkspaceDataBoundary(workspace_root=sensitive_root, code_repo_root=code_repo_root)


@pytest.fixture
def librarian(boundary: WorkspaceDataBoundary) -> LibrarianFilingService:
    """A librarian filing service over the per-test tmp_path boundary."""
    return LibrarianFilingService(boundary)


# -- Hypothesis strategies (valid, varied synthetic records) ------------------

# Slug-safe identity strings: start with alnum, then alnum/-/_, bounded length.
_slug = st.from_regex(r"[a-z0-9][a-z0-9_-]{0,15}", fullmatch=True)
_ext = st.from_regex(r"[a-z0-9]{1,6}", fullmatch=True)
# Human names that always contain at least one path-safe char so slugify works.
_human_name = st.from_regex(r"[A-Za-z0-9][ A-Za-z0-9.,()&'-]{0,40}", fullmatch=True)


def make_record(  # noqa: PLR0913 — a test factory mirroring every record field
    *,
    logical_id: str = "doc-1",
    company: str = "acme",
    kind: DeliverableKind = DeliverableKind.REPORT,
    canonical_name: str = "Q3 Board Memo",
    extension: str = "pdf",
    version: int = 1,
    provenance: str = "business_document_builder:run-1",
) -> FiledDocumentRecord:
    """Build a valid record with sane defaults (overridable per field)."""
    return FiledDocumentRecord(
        logical_id=logical_id,
        company=company,
        kind=kind,
        canonical_name=canonical_name,
        extension=extension,
        version=version,
        provenance=provenance,
        created_at=FIXED_NOW,
    )


@st.composite
def filed_document_records(draw: st.DrawFn) -> FiledDocumentRecord:
    """Draw an arbitrary VALID FiledDocumentRecord (synthetic, varied)."""
    return make_record(
        logical_id=draw(_slug),
        company=draw(_slug),
        kind=draw(st.sampled_from(list(DeliverableKind))),
        canonical_name=draw(_human_name),
        extension=draw(_ext),
        version=draw(st.integers(min_value=1, max_value=50)),
        provenance=draw(st.text(min_size=1, max_size=30).filter(lambda s: s.strip())),
    )
