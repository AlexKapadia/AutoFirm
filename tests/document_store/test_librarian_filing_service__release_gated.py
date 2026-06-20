"""P4 teeth-tests: the librarian seam is GATED by an authorised ReleaseDecision.

These prove the review gate is LOAD-BEARING at the outbound artifact-delivery
chokepoint (``LibrarianFilingService.file``) — each would FAIL if the gate were not
wired in, none is tautological:

* ``release_decision=None`` is refused AND nothing is catalogued (the guard runs
  BEFORE any catalog/index mutation — fail-closed precedes side effects, §5.6).
* an UNAUTHORISED decision (built over a FAILING verdict) is refused, nothing
  catalogued — a blocked artifact cannot be filed.
* a decision whose ``artifact_ref`` does not bind to THIS record is refused — one
  authorised release cannot be replayed to file a different document (anti-swap).
* an authorised, ref-matching decision FILES successfully (happy path green).
* END-TO-END (the Phase-4 proof): a real ``ReviewableArtifact`` flows through the
  ``OutputReviewGate`` -> ``ReleaseDecisionGate`` -> ``file`` — delivery succeeds
  when the verdict passed and is BLOCKED when a planted defect fails it.

Synthetic only; no network; the boundary is a per-test tmp_path root.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from autofirm.document_store.filed_document_record import FiledDocumentRecord
from autofirm.document_store.librarian_filing_service import (
    LibrarianFilingService,
    release_artifact_ref_for,
)
from autofirm.output_review.default_output_review_gate_factory import (
    build_default_output_review_gate,
)
from autofirm.output_review.output_review_errors import OutputReviewError
from autofirm.output_review.release_decision_gate import (
    ReleaseAuditSink,
    ReleaseDecision,
    ReleaseDecisionGate,
)
from autofirm.output_review.review_finding_and_severity_contracts import (
    CheckSeverity,
    DefectClass,
    ReviewCheckId,
    ReviewFinding,
)
from autofirm.output_review.review_verdict_contract import ReviewVerdict
from autofirm.output_review.reviewable_artifact_contract import (
    ArtifactKind,
    ReviewableArtifact,
)
from autofirm.output_review.reviewable_artifact_facts import (
    BalanceSheetFigures,
    BalanceSheetPeriod,
    ModelLintFacts,
    NumericClaim,
    NumericClaimSet,
    SpecRoundTrip,
)
from tests.document_store.conftest import authorised_release_for, make_record

_FIXED_AT = datetime(2026, 6, 16, 12, 0, tzinfo=UTC)  # injected clock — never now()


# -- Direct-seam doubles (decisions built by hand) ------------------------------
def _unauthorised_for(record: FiledDocumentRecord) -> ReleaseDecision:
    """A ref-matching but BLOCKED release (a BLOCKING finding => authorised False)."""
    ref = release_artifact_ref_for(record)
    verdict = ReviewVerdict(
        artifact_ref=ref,
        findings=(
            ReviewFinding(
                check_id=ReviewCheckId.ACCOUNTING_IDENTITY,
                severity=CheckSeverity.BLOCKING,
                defect_class=DefectClass.PURE_LOGIC,
                message="A != L + E",
                locator="FY24",
            ),
        ),
        reviewed_at=_FIXED_AT,
    )
    return ReleaseDecision(
        artifact_ref=ref, final_verdict=verdict, reason="blocked", decided_at=_FIXED_AT
    )


# ================================================================================
# 1. None decision -> refused AND nothing catalogued (guard precedes mutation).
# ================================================================================
def test_none_release_is_refused_and_nothing_is_catalogued(
    librarian: LibrarianFilingService,
) -> None:
    with pytest.raises(OutputReviewError):
        librarian.file(make_record(), release_decision=None)
    # fail-closed PRECEDES side effects: the catalog and its indexes never grew.
    assert librarian.list_all() == ()
    assert librarian.find() == ()


# ================================================================================
# 2. Unauthorised decision -> refused, nothing catalogued.
# ================================================================================
def test_unauthorised_release_is_refused_and_nothing_is_catalogued(
    librarian: LibrarianFilingService,
) -> None:
    record = make_record()
    decision = _unauthorised_for(record)
    assert decision.authorised is False  # precondition: the verdict did NOT pass
    with pytest.raises(OutputReviewError):
        librarian.file(record, release_decision=decision)
    assert librarian.list_all() == ()


# ================================================================================
# 3. Ref mismatch -> refused (a release for a DIFFERENT document cannot file this).
# ================================================================================
def test_release_for_a_different_record_is_refused(
    librarian: LibrarianFilingService,
) -> None:
    record = make_record(logical_id="real-doc", version=1)
    # An authorised release whose ref binds to a DIFFERENT document/version.
    other_decision = authorised_release_for(make_record(logical_id="other-doc", version=1))
    with pytest.raises(OutputReviewError):
        librarian.file(record, release_decision=other_decision)
    assert librarian.list_all() == ()


def test_release_for_a_different_version_is_refused(
    librarian: LibrarianFilingService,
) -> None:
    # Same logical id, different version => different identity => refused (anti-swap).
    record = make_record(logical_id="doc", version=2)
    v1_decision = authorised_release_for(make_record(logical_id="doc", version=1))
    with pytest.raises(OutputReviewError):
        librarian.file(record, release_decision=v1_decision)
    assert librarian.list_all() == ()


# ================================================================================
# 4. Authorised + matching -> FILES successfully (happy path green).
# ================================================================================
def test_authorised_matching_release_files_successfully(
    librarian: LibrarianFilingService, sensitive_root: str
) -> None:
    record = make_record()
    entry = librarian.file(record, release_decision=authorised_release_for(record))
    assert entry.record is record
    assert entry.absolute_path.startswith(sensitive_root + "/")
    assert len(librarian.list_all()) == 1
    assert librarian.find(logical_id=record.logical_id) == (entry,)


# -- End-to-end fixtures (real gate -> real release authority -> seam) -----------
class _CleanProbe:
    """A file-open probe that always reports a clean open (synthetic, no real IO)."""

    def probe(self, path: Path, kind: ArtifactKind) -> tuple[bool, str]:
        return (True, "")


class _SpySink:
    """Records every audited release so the e2e can assert the decision was logged."""

    def __init__(self) -> None:
        self.calls: list[object] = []

    def record(
        self,
        *,
        artifact_ref: str,
        outcome: object,
        reason: str,
        decided_at: datetime,
    ) -> None:
        self.calls.append(artifact_ref)


def _financial_model(path: Path, ref: str, *, assets: str) -> ReviewableArtifact:
    """A financial-model artifact whose ref is the record's release identity.

    Every fact bundle is clean EXCEPT the balance sheet, whose ``assets`` the caller
    sets: ``"100"`` balances (L=60+E=40) so the whole artifact passes; any other
    value plants exactly one ACCOUNTING_IDENTITY blocking defect.
    """
    return ReviewableArtifact(
        artifact_ref=ref,
        kind=ArtifactKind.FINANCIAL_MODEL,
        path=path,
        balance_sheet=BalanceSheetFigures(
            periods=(
                BalanceSheetPeriod(
                    period="FY24",
                    assets=Decimal(assets),
                    liabilities=Decimal("60"),
                    equity=Decimal("40"),
                ),
            )
        ),
        numeric_claims=NumericClaimSet(
            claims=(
                NumericClaim(
                    label="rev",
                    declared_value=Decimal("10"),
                    recomputed_value=Decimal("10"),
                ),
            )
        ),
        spec_round_trip=SpecRoundTrip(
            declared_values={"title": "Q4"}, extracted_values={"title": "Q4"}
        ),
        model_lint=ModelLintFacts(orphan_constant_cells=()),
    )


def _release_gate(sink: ReleaseAuditSink) -> ReleaseDecisionGate:
    return ReleaseDecisionGate(sink=sink, clock=lambda: _FIXED_AT)


def test_end_to_end_passing_review_authorises_and_files(
    librarian: LibrarianFilingService, tmp_path: Path
) -> None:
    """Review (passes) -> decide (authorised) -> file SUCCEEDS — the full Phase-4 flow."""
    record = make_record(logical_id="e2e-pass", version=1)
    ref = release_artifact_ref_for(record)
    on_disk = tmp_path / "model.bin"
    on_disk.write_bytes(b"synthetic")

    review_gate = build_default_output_review_gate(_CleanProbe(), lambda: _FIXED_AT)
    verdict = review_gate.review(_financial_model(on_disk, ref, assets="100"))
    assert verdict.passed is True  # the gate cleared it

    sink = _SpySink()
    decision = _release_gate(sink).decide(verdict, reason="all checks green")
    assert decision.authorised is True

    entry = librarian.file(record, release_decision=decision)
    assert entry.record is record
    assert librarian.list_all() == (entry,)
    assert sink.calls == [ref]  # the release was audited at the authority


def test_end_to_end_failing_review_blocks_delivery(
    librarian: LibrarianFilingService, tmp_path: Path
) -> None:
    """Review (fails on a planted defect) -> decide (blocked) -> file is REFUSED."""
    record = make_record(logical_id="e2e-fail", version=1)
    ref = release_artifact_ref_for(record)
    on_disk = tmp_path / "model.bin"
    on_disk.write_bytes(b"synthetic")

    review_gate = build_default_output_review_gate(_CleanProbe(), lambda: _FIXED_AT)
    # Imbalanced assets (99 vs L+E=100) plants a BLOCKING accounting defect.
    verdict = review_gate.review(_financial_model(on_disk, ref, assets="99"))
    assert verdict.passed is False  # the gate caught the defect

    sink = _SpySink()
    decision = _release_gate(sink).decide(verdict, reason="blocking defect found")
    assert decision.authorised is False

    with pytest.raises(OutputReviewError):
        librarian.file(record, release_decision=decision)
    # Delivery blocked: nothing reached the store despite a real, audited decision.
    assert librarian.list_all() == ()
