"""Integration: both e2e delivery paths are genuinely reviewed, released, and audited.

Drives the real build + operate flow with an INSPECTABLE gate pair (its audit sink
exposed) and proves the two deliverables — the build-time founding charter and the
operate-time investor update — each reach the store only via an authorised, SUCCESS-
audited release over a real ``.docx`` that opens clean. Also proves an un-gated
filing is impossible and the gated flow is deterministic across runs.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from autofirm.audit.audit_record_contract import AuditOutcome
from autofirm.document_store.librarian_filing_service import release_artifact_ref_for
from autofirm.e2e.company_build_flow import FOUNDING_EPOCH, build_company
from autofirm.e2e.company_operate_flow import operate_company
from autofirm.e2e.e2e_delivery_gates import E2eDeliveryGates
from autofirm.e2e.in_memory_release_audit_sink import InMemoryReleaseAuditSink
from autofirm.e2e.isolated_company_workspace import create_isolated_company_workspace
from autofirm.e2e.public_company_scenarios import (
    PublicCompanyScenario,
    public_company_scenarios,
)
from autofirm.e2e.scenario_result_contract import FeatureName, FeatureStatus
from autofirm.e2e.zipfile_ooxml_file_open_probe import ZipfileOoxmlFileOpenProbe
from autofirm.output_review.default_output_review_gate_factory import (
    build_default_output_review_gate,
)
from autofirm.output_review.output_review_errors import OutputReviewError
from autofirm.output_review.release_decision_gate import ReleaseDecisionGate

_SCENARIOS = public_company_scenarios()
_IDS = [s.slug for s in _SCENARIOS]


def _inspectable_gates() -> tuple[E2eDeliveryGates, InMemoryReleaseAuditSink]:
    """A real gate pair on the deterministic founding clock, exposing its sink."""
    sink = InMemoryReleaseAuditSink()
    review_gate = build_default_output_review_gate(
        ZipfileOoxmlFileOpenProbe(), lambda: FOUNDING_EPOCH
    )
    release_gate = ReleaseDecisionGate(sink, lambda: FOUNDING_EPOCH)
    return E2eDeliveryGates(review_gate=review_gate, release_gate=release_gate), sink


def _run(scenario: PublicCompanyScenario, corpus_dir: Path, gates: E2eDeliveryGates):  # type: ignore[no-untyped-def]
    workspace = create_isolated_company_workspace(
        company_slug=scenario.slug, corpus_dir=corpus_dir
    )
    built = build_company(scenario, workspace, gates)
    operate_checks = operate_company(
        scenario, built.recording_org, built.librarian, workspace, gates
    )
    return built, operate_checks, workspace


@pytest.mark.parametrize("scenario", _SCENARIOS, ids=_IDS)
def test_both_deliverables_are_gated_filed_and_open_clean(
    scenario: PublicCompanyScenario, corpus_dir: Path
) -> None:
    gates, sink = _inspectable_gates()
    built, operate_checks, workspace = _run(scenario, corpus_dir, gates)

    # Both deliverables are catalogued for this company (charter + investor update).
    filed = {e.record.logical_id for e in built.librarian.find(company=scenario.slug)}
    assert filed == {"founding-charter", "investor-update"}

    # Both are real .docx files on disk that OPEN CLEAN (proving Site-2's charter is
    # now a genuine rendered document, not the old un-written .md).
    probe = ZipfileOoxmlFileOpenProbe()
    from autofirm.output_review.reviewable_artifact_contract import ArtifactKind

    for name in ("founding-charter.docx", "investor-update.docx"):
        path = workspace.deliverables_dir() / name
        assert path.stat().st_size > 0
        assert probe.probe(path, ArtifactKind.BUSINESS_DOCUMENT) == (True, "")

    # Each filing was authorised by a SUCCESS-audited release bound to its ref.
    outcomes = {e.artifact_ref: e.outcome for e in sink.entries()}
    assert outcomes.get("founding-charter@v1") is AuditOutcome.SUCCESS
    assert outcomes.get("investor-update@v1") is AuditOutcome.SUCCESS

    # The two filing-related feature checks pass.
    by_feature = {c.feature: c for c in (*built.checks, *operate_checks)}
    assert by_feature[FeatureName.DOCUMENTS_FILED].status is FeatureStatus.PASSED
    assert by_feature[FeatureName.ARTIFACT_GENERATED].status is FeatureStatus.PASSED


def test_ungated_filing_is_impossible(corpus_dir: Path) -> None:
    # Re-filing a catalogued record WITHOUT a release is refused outright — the
    # librarian seam is load-bearing, so no path can file un-gated.
    gates, _ = _inspectable_gates()
    scenario = _SCENARIOS[0]
    built, _checks, _workspace = _run(scenario, corpus_dir, gates)
    record = built.librarian.find(company=scenario.slug, logical_id="founding-charter")[0].record
    with pytest.raises(OutputReviewError):
        built.librarian.file(record, release_decision=None)
    # The release ref convention is unchanged by the gating wiring.
    assert release_artifact_ref_for(record) == "founding-charter@v1"


def test_gated_delivery_is_deterministic_across_runs(corpus_dir: Path) -> None:
    # Two independent runs over the same scenario produce identical audit trails
    # (refs + outcomes + timestamps) under the frozen founding clock.
    scenario = _SCENARIOS[0]

    def audit_fingerprint(tag: str) -> tuple[tuple[str, AuditOutcome, object], ...]:
        gates, sink = _inspectable_gates()
        _run(scenario, corpus_dir / tag, gates)
        return tuple((e.artifact_ref, e.outcome, e.decided_at) for e in sink.entries())

    assert audit_fingerprint("run-a") == audit_fingerprint("run-b")
