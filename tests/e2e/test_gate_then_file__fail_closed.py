"""Teeth-tests for the gate_then_file seam — nothing files without an authorised release.

These exercise the four delivery outcomes that each would let an un-reviewed or
blocked artifact reach a human if the seam were wrong:

1. a clean artifact -> reviewed, released (SUCCESS audited), and catalogued;
2. a missing file -> FILE_OPENS_CLEAN blocks -> DENY audited -> filing refused,
   nothing catalogued;
3. a tampered title -> SPEC_ROUND_TRIP blocks -> DENY audited -> refused;
4. a ref-swapped artifact -> refused BEFORE any review (anti-swap binding).

All inputs are synthetic real files under a deletable workspace; no network. The
gates are built by hand so the test can inspect the audit sink directly.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from autofirm.artifacts.business_document_builder import build_business_document
from autofirm.artifacts.business_document_spec import DocumentSection, DocumentSpec
from autofirm.audit.audit_record_contract import AuditOutcome
from autofirm.document_store.filed_document_record import DeliverableKind, FiledDocumentRecord
from autofirm.document_store.librarian_filing_service import (
    CatalogEntry,
    LibrarianFilingService,
    release_artifact_ref_for,
)
from autofirm.e2e.docx_spec_round_trip_extractor import build_document_spec_round_trip
from autofirm.e2e.gate_then_file import gate_then_file
from autofirm.e2e.in_memory_release_audit_sink import InMemoryReleaseAuditSink
from autofirm.e2e.isolated_company_workspace import create_isolated_company_workspace
from autofirm.e2e.zipfile_ooxml_file_open_probe import ZipfileOoxmlFileOpenProbe
from autofirm.output_review.default_output_review_gate_factory import (
    build_default_output_review_gate,
)
from autofirm.output_review.output_review_errors import OutputReviewError
from autofirm.output_review.output_review_gate import OutputReviewGate
from autofirm.output_review.release_decision_gate import ReleaseDecisionGate
from autofirm.output_review.reviewable_artifact_contract import (
    ArtifactKind,
    ReviewableArtifact,
)

_AT = datetime(2026, 1, 1, tzinfo=UTC)
_TITLE = "Acme Quarterly Report"


def _gates() -> tuple[OutputReviewGate, ReleaseDecisionGate, InMemoryReleaseAuditSink]:
    """A real review gate + release gate, returning the sink for inspection."""
    sink = InMemoryReleaseAuditSink()
    review_gate = build_default_output_review_gate(ZipfileOoxmlFileOpenProbe(), lambda: _AT)
    release_gate = ReleaseDecisionGate(sink, lambda: _AT)
    return review_gate, release_gate, sink


def _record() -> FiledDocumentRecord:
    return FiledDocumentRecord(
        logical_id="acme-report",
        company="acme",
        kind=DeliverableKind.REPORT,
        canonical_name=_TITLE,
        extension="docx",
        version=1,
        provenance="test.gate_then_file",
        created_at=_AT,
    )


def _written_docx(corpus_dir: Path) -> tuple[LibrarianFilingService, Path]:
    workspace = create_isolated_company_workspace(company_slug="acme", corpus_dir=corpus_dir)
    librarian = LibrarianFilingService(workspace.boundary)
    spec = DocumentSpec(title=_TITLE, sections=(DocumentSection("Body", ("a line.",)),))
    written = build_business_document(spec, workspace.deliverables_dir() / "acme.docx")
    return librarian, written


def test_clean_artifact_is_reviewed_released_and_filed(corpus_dir: Path) -> None:
    librarian, written = _written_docx(corpus_dir)
    record = _record()
    review_gate, release_gate, sink = _gates()
    artifact = ReviewableArtifact(
        artifact_ref=release_artifact_ref_for(record),
        kind=ArtifactKind.BUSINESS_DOCUMENT,
        path=written,
        spec_round_trip=build_document_spec_round_trip(_TITLE, written),
    )

    entry = gate_then_file(
        librarian,
        record,
        artifact=artifact,
        gate=review_gate,
        release_gate=release_gate,
        reason="all floor checks clean",
    )

    assert isinstance(entry, CatalogEntry)
    assert entry.record.logical_id == "acme-report"
    assert len(librarian.find(company="acme")) == 1  # catalogued exactly once
    # exactly one audit entry, a SUCCESS bound to this record's ref.
    assert len(sink.entries()) == 1
    assert sink.entries()[0].outcome is AuditOutcome.SUCCESS
    assert sink.entries()[0].artifact_ref == "acme-report@v1"


def test_missing_file_blocks_denies_and_files_nothing(corpus_dir: Path) -> None:
    librarian, written = _written_docx(corpus_dir)
    record = _record()
    review_gate, release_gate, sink = _gates()
    # Round-trip facts re-read from the REAL file, but the artifact points FILE_OPENS_CLEAN
    # at a path that does not exist -> that check blocks -> the verdict fails.
    artifact = ReviewableArtifact(
        artifact_ref=release_artifact_ref_for(record),
        kind=ArtifactKind.BUSINESS_DOCUMENT,
        path=written.parent / "vanished.docx",
        spec_round_trip=build_document_spec_round_trip(_TITLE, written),
    )

    with pytest.raises(OutputReviewError):
        gate_then_file(
            librarian,
            record,
            artifact=artifact,
            gate=review_gate,
            release_gate=release_gate,
            reason="should be denied",
        )

    assert librarian.find(company="acme") == ()  # NOTHING catalogued
    # the denial was LOGGED, not dropped (the verdict was decided then refused).
    assert len(sink.entries()) == 1
    assert sink.entries()[0].outcome is AuditOutcome.DENY


def test_tampered_title_blocks_denies_and_files_nothing(corpus_dir: Path) -> None:
    librarian, written = _written_docx(corpus_dir)
    record = _record()
    review_gate, release_gate, sink = _gates()
    # The file opens clean, but the declared title disagrees with the re-read one ->
    # SPEC_ROUND_TRIP blocks -> verdict fails -> release denied -> filing refused.
    artifact = ReviewableArtifact(
        artifact_ref=release_artifact_ref_for(record),
        kind=ArtifactKind.BUSINESS_DOCUMENT,
        path=written,
        spec_round_trip=build_document_spec_round_trip("A Forged Title", written),
    )

    with pytest.raises(OutputReviewError):
        gate_then_file(
            librarian,
            record,
            artifact=artifact,
            gate=review_gate,
            release_gate=release_gate,
            reason="should be denied",
        )

    assert librarian.find(company="acme") == ()
    assert len(sink.entries()) == 1
    assert sink.entries()[0].outcome is AuditOutcome.DENY


def test_ref_swapped_artifact_is_refused_before_review(corpus_dir: Path) -> None:
    librarian, written = _written_docx(corpus_dir)
    record = _record()
    review_gate, release_gate, sink = _gates()
    # An authorised release for a DIFFERENT artifact must never file THIS record.
    artifact = ReviewableArtifact(
        artifact_ref="some-other-doc@v9",
        kind=ArtifactKind.BUSINESS_DOCUMENT,
        path=written,
        spec_round_trip=build_document_spec_round_trip(_TITLE, written),
    )

    with pytest.raises(OutputReviewError) as exc:
        gate_then_file(
            librarian,
            record,
            artifact=artifact,
            gate=review_gate,
            release_gate=release_gate,
            reason="ref mismatch",
        )

    assert str(exc.value) == (
        "gate_then_file: artifact ref 'some-other-doc@v9' does not bind to record ref "
        "'acme-report@v1'"
    )
    assert librarian.find(company="acme") == ()  # refused before any side effect
    assert sink.entries() == ()  # no review ran, so nothing was audited
