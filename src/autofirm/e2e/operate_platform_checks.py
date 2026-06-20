"""Operate-phase platform checks: market-intel, front door, artifacts, heartbeat, flow.

Each check drives one platform plane the way an operator would and asserts its
real output is correct:

* market-intel sweep -> a structured insight (nothing silently dropped);
* green-light gate -> a verdict whose rationale matches it exactly;
* front door -> the owner's question routed to a real handler over the live bus;
* artifacts + document store -> a REAL ``.docx`` written under the isolated root
  and filed in the company's store;
* heartbeat -> a registered beat fires exactly once on the injected clock;
* flow -> a work item moves created -> done with a complete, gapless trail.
"""

from __future__ import annotations

from autofirm.artifacts.business_document_builder import build_business_document
from autofirm.artifacts.business_document_spec import DocumentSection, DocumentSpec
from autofirm.document_store.filed_document_record import (
    DeliverableKind,
    FiledDocumentRecord,
)
from autofirm.document_store.librarian_filing_service import (
    LibrarianFilingService,
    release_artifact_ref_for,
)
from autofirm.e2e.company_build_flow import FOUNDING_EPOCH
from autofirm.e2e.deliverable_kind_to_review_artifact_kind import review_artifact_kind_for
from autofirm.e2e.docx_spec_round_trip_extractor import build_document_spec_round_trip
from autofirm.e2e.e2e_delivery_gates import E2eDeliveryGates
from autofirm.e2e.gate_then_file import gate_then_file
from autofirm.e2e.isolated_company_workspace import IsolatedCompanyWorkspace
from autofirm.e2e.operate_front_door_check import check_front_door_routing
from autofirm.e2e.public_company_scenarios import PublicCompanyScenario
from autofirm.e2e.scenario_result_contract import (
    FeatureCheck,
    FeatureName,
    FeatureStatus,
)
from autofirm.flow.flow_state_machine import WorkState, is_terminal
from autofirm.flow.injected_flow_clock import ManualFlowClock
from autofirm.flow.work_item import WorkItem
from autofirm.heartbeat.heartbeat_scheduler import HeartbeatScheduler
from autofirm.heartbeat.injected_heartbeat_clock import ManualHeartbeatClock
from autofirm.heartbeat.recurring_beat_definition import BeatDefinition
from autofirm.market_intel.green_light_decision_contract import (
    GreenLightConfig,
    GreenLightVerdict,
)
from autofirm.market_intel.green_light_decision_gate import decide_green_light
from autofirm.market_intel.market_insight_audit_sink import InMemoryMarketInsightAuditSink
from autofirm.market_intel.market_insight_contract import InsightCategory, MarketInsight
from autofirm.market_intel.market_sensing_sweep import MarketSensingSweep
from autofirm.market_intel.market_signal_source import (
    InMemoryMarketSignalSource,
    RawMarketSignal,
)
from autofirm.org.org_lifecycle_engine import DynamicOrg
from autofirm.output_review.reviewable_artifact_contract import ReviewableArtifact

__all__ = [
    "check_artifact_and_filing",
    "check_flow_handoff",
    "check_front_door_routing",
    "check_green_light_gate",
    "check_heartbeat_tick",
    "check_market_intel_sweep",
]

_OWNING_TEAM = "growth-team"
_KNOWN_ROLES = frozenset({_OWNING_TEAM, "exec"})
# Two corroborating insights are fed to the green-light gate (above the default
# min-supporting-signals), so the GO verdict must list exactly this many.
_EXPECTED_GREEN_LIGHT_CONTRIBUTIONS = 2
# Float tolerance for the score == sum(contributions) tie (weighted_value is a
# float; the gate sums the same floats, so equality holds within rounding noise).
_SCORE_TIE_TOLERANCE = 1e-9


def check_market_intel_sweep(scenario: PublicCompanyScenario) -> FeatureCheck:
    """Sense the scenario's public signal into a structured insight, audited.

    The sweep treats the observation as UNTRUSTED, sanitizes it, and structures it
    into exactly one accepted insight; the audit trail length equals the number of
    signals fetched (nothing silently dropped — the core market-intel invariant).
    """
    raw = RawMarketSignal(
        source_name="public-feed",
        observation=scenario.market_observation,
        proposed_category=InsightCategory.MARKET_TREND,
    )
    sink = InMemoryMarketInsightAuditSink()
    sweep = MarketSensingSweep(
        sources=(InMemoryMarketSignalSource("public-feed", (raw,)),),
        audit_sink=sink,
        clock=ManualHeartbeatClock(start=FOUNDING_EPOCH),
        owning_team=_OWNING_TEAM,
        known_roles=_KNOWN_ROLES,
    )
    result = sweep.run()
    accounted = len(result.insights) + len(result.rejections)
    correct = (
        len(result.insights) == 1  # the clean public signal became one insight
        and accounted == 1  # nothing silently dropped (accepted + rejected == fetched)
        and result.team_work_item is not None  # accepted insight flowed to the team
    )
    return FeatureCheck(
        feature=FeatureName.MARKET_INTEL_SWEEP,
        phase="operate",
        status=FeatureStatus.PASSED if correct else FeatureStatus.FAILED,
        detail="public signal sensed into a structured insight; nothing dropped",
        evidence={"insights": str(len(result.insights)), "rejections": str(len(result.rejections))},
    )


def check_green_light_gate(scenario: PublicCompanyScenario) -> FeatureCheck:
    """Decide go / no-go; assert the rationale matches the verdict exactly.

    Two supporting insights above the confidence floor clear the default
    threshold, so the verdict is GO and its ``total_score`` equals the sum of the
    listed contributions — the rationale IS the proof of the verdict (§3.11).
    """
    insights = (
        MarketInsight(
            source_name="public-feed",
            observation=scenario.market_observation,
            category=InsightCategory.MARKET_TREND,
            confidence=0.8,
            sensed_at=FOUNDING_EPOCH,
        ),
        MarketInsight(
            source_name="public-feed",
            observation="second corroborating public market signal",
            category=InsightCategory.CUSTOMER_DEMAND,
            confidence=0.7,
            sensed_at=FOUNDING_EPOCH,
        ),
    )
    decision = decide_green_light(insights, GreenLightConfig())
    contribution_sum = sum(c.weighted_value for c in decision.contributions)
    matches = (
        decision.verdict is GreenLightVerdict.GO
        and len(decision.contributions) == _EXPECTED_GREEN_LIGHT_CONTRIBUTIONS
        and abs(decision.total_score - contribution_sum) < _SCORE_TIE_TOLERANCE
    )
    return FeatureCheck(
        feature=FeatureName.GREEN_LIGHT_GATE,
        phase="operate",
        status=FeatureStatus.PASSED if matches else FeatureStatus.FAILED,
        detail="green-light verdict produced; rationale matches the verdict",
        evidence={"verdict": decision.verdict.value, "score": f"{decision.total_score:.4f}"},
    )


def check_artifact_and_filing(
    scenario: PublicCompanyScenario,
    librarian: LibrarianFilingService,
    workspace: IsolatedCompanyWorkspace,
    gates: E2eDeliveryGates,
) -> FeatureCheck:
    """Generate a REAL investor-ready ``.docx``, REVIEW it, then file it if released.

    The artifact is written under the company's ``.autofirm/`` root (a real file on
    disk in the deletable workspace), then routed through the output-review gate
    (the FILE_OPENS_CLEAN probe reads the bytes; SPEC_ROUND_TRIP re-reads the title)
    and the release authority BEFORE the librarian catalogues it — proving no
    deliverable reaches the store without an authorised, ref-bound release (P4).
    """
    periods = len(scenario.projected_cash_flows)
    spec = DocumentSpec(
        title=f"{scenario.name} Investor Update",
        executive_summary=(
            f"{scenario.name} operating in {scenario.industry}; public-data validation."
        ),
        sections=(
            DocumentSection(
                "Performance",
                (f"Revenue {scenario.revenue}.", f"Opex {scenario.operating_expense}."),
            ),
            DocumentSection("Outlook", (f"Projected cash flows over {periods} periods.",)),
        ),
    )
    destination = workspace.deliverables_dir() / "investor-update.docx"
    written = build_business_document(spec, destination)
    record = FiledDocumentRecord(
        logical_id="investor-update",
        company=scenario.slug,
        kind=DeliverableKind.REPORT,
        canonical_name=f"{scenario.name} Investor Update",
        extension="docx",
        version=1,
        provenance="e2e.operate_platform_checks:artifact",
        created_at=FOUNDING_EPOCH,
    )
    # The reviewable handle binds to THIS record's release ref; FILE_OPENS_CLEAN
    # reads ``written`` and SPEC_ROUND_TRIP gets a GENUINE title re-read from disk.
    artifact = ReviewableArtifact(
        artifact_ref=release_artifact_ref_for(record),
        kind=review_artifact_kind_for(record.kind),
        path=written,
        spec_round_trip=build_document_spec_round_trip(spec.title, written),
    )
    entry = gate_then_file(
        librarian,
        record,
        artifact=artifact,
        gate=gates.review_gate,
        release_gate=gates.release_gate,
        reason="investor update passed the deterministic output-review floor",
    )
    ok = (
        written.exists()
        and written.stat().st_size > 0  # a real, non-empty .docx was produced
        and len(librarian.find(company=scenario.slug, logical_id="investor-update")) == 1
    )
    return FeatureCheck(
        feature=FeatureName.ARTIFACT_GENERATED,
        phase="operate",
        status=FeatureStatus.PASSED if ok else FeatureStatus.FAILED,
        detail="real .docx artifact reviewed, released, and filed under the isolated root",
        evidence={"bytes": str(written.stat().st_size), "filed_path": entry.relative_path},
    )


def check_heartbeat_tick(scenario: PublicCompanyScenario) -> FeatureCheck:
    """Register a beat and tick the injected clock so it fires exactly once."""
    fired_count = {"n": 0}

    def beat_callback() -> None:
        fired_count["n"] += 1

    clock = ManualHeartbeatClock(start=FOUNDING_EPOCH)
    scheduler = HeartbeatScheduler(clock)
    scheduler.register(
        BeatDefinition(name="market-sweep", interval_seconds=60.0, callback=beat_callback)
    )
    clock.advance(60.0)  # exactly one interval -> due once
    result = scheduler.tick()
    correct = result.fired == ("market-sweep",) and fired_count["n"] == 1
    return FeatureCheck(
        feature=FeatureName.HEARTBEAT_TICK,
        phase="operate",
        status=FeatureStatus.PASSED if correct else FeatureStatus.FAILED,
        detail="registered beat fired exactly once on the injected clock",
        evidence={"fired": str(result.fired), "calls": str(fired_count["n"])},
    )


def check_flow_handoff(scenario: PublicCompanyScenario, org: DynamicOrg) -> FeatureCheck:
    """Move a work item through the org (created -> done) with a gapless trail.

    The item is assigned to the company's auto-created role, started, and
    completed; the resulting trail is gapless and reaches a terminal state,
    proving the flow primitive operates over the live org's real roles.
    """
    role = scenario.gap_role_id
    clock = ManualFlowClock()
    item = WorkItem.create(
        work_id=f"WI-{scenario.slug}", clock=clock, known_roles=frozenset({role})
    )
    item = item.assign_to(role, "stand up function")
    clock.tick()
    item = item.start("begin")
    clock.tick()
    item = item.complete("done")
    correct = (
        item.state is WorkState.DONE
        and is_terminal(item.state)
        and item.trail.is_gapless()
        and item.trail.transitions[0].to_role == role
    )
    return FeatureCheck(
        feature=FeatureName.FLOW_HANDOFF,
        phase="operate",
        status=FeatureStatus.PASSED if correct else FeatureStatus.FAILED,
        detail="work item moved created->done with a gapless trail",
        evidence={"final_state": item.state.value, "transitions": str(len(item.trail.transitions))},
    )
