"""Build-the-company flow: stand a company up with the real platform modules.

Drives the platform exactly as a human founder would to bring a company online,
then ASSERTS it actually came up:

1. **Found the org** (org engine) — a CEO root with the founding charter.
2. **Detect a capability gap and auto-create + hire** the missing role
   (org engine ``auto_create_on_gap``), proving the platform's automatic
   role-creation-on-gap.
3. **Wire comms** — register the founded roles on the inter-agent message bus and
   deliver a kickoff message, proving the comms plane is live for this company.
4. **File initial documents** — catalogue a founding charter deliverable in the
   company's isolated document store (document store over the injected boundary).

Every step returns a :class:`FeatureCheck` carrying the real-shaped evidence the
assertion verified; a failure is reported as a FAILED check, never swallowed.
Everything is deterministic (injected clock + id-generator) so two runs over the
same scenario produce identical audit trails (CLAUDE.md §3.11).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime

from autofirm.comms.append_only_audit_sink import InMemoryMessageAuditSink
from autofirm.comms.dynamic_agent_registry import DynamicAgentRegistry, MessageHandler
from autofirm.comms.injectable_delivery_clock import ManualClock
from autofirm.comms.inter_agent_message_bus import InterAgentMessageBus
from autofirm.comms.message_envelope_contract import MessageEnvelope, Performative
from autofirm.document_store.filed_document_record import (
    DeliverableKind,
    FiledDocumentRecord,
)
from autofirm.document_store.librarian_filing_service import LibrarianFilingService
from autofirm.e2e.isolated_company_workspace import IsolatedCompanyWorkspace
from autofirm.e2e.public_company_scenarios import PublicCompanyScenario
from autofirm.e2e.scenario_result_contract import (
    FeatureCheck,
    FeatureName,
    FeatureStatus,
)
from autofirm.org.gap_detection_contract import GapKind, OrgGap
from autofirm.org.org_identifiers import (
    ArtifactId,
    FrozenClock,
    RoleId,
    SequentialIdGenerator,
)
from autofirm.org.org_lifecycle_engine import DynamicOrg
from autofirm.org.org_lifecycle_events import OrgEventKind
from autofirm.org.role_charter_contract import ROOT_AUTHOR, RoleCharter

# A fixed founding epoch so the build's audit trail is deterministic + assertable.
FOUNDING_EPOCH = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)
CEO_ROLE = "ceo"


@dataclass(frozen=True, slots=True)
class BuiltCompany:
    """The live, stood-up company plus the checks proving it came up.

    Args:
        org: The founded org with the auto-created role hired in (the live state
            the operate flow routes its front-door questions over).
        librarian: The document store the company files deliverables into.
        checks: The build-phase :class:`FeatureCheck` verdicts (org/gap/comms/docs).
    """

    org: DynamicOrg
    librarian: LibrarianFilingService
    checks: tuple[FeatureCheck, ...]


def build_company(
    scenario: PublicCompanyScenario, workspace: IsolatedCompanyWorkspace
) -> BuiltCompany:
    """Stand ``scenario`` up in its isolated ``workspace`` and prove it came up."""
    org, founded_check = _found_org(scenario)
    org, gap_check = _auto_create_and_hire(org, scenario)
    comms_check = _wire_comms_and_deliver_kickoff(org, scenario)
    librarian, docs_check = _file_founding_documents(scenario, workspace)
    return BuiltCompany(
        org=org,
        librarian=librarian,
        checks=(founded_check, gap_check, comms_check, docs_check),
    )


def _found_org(scenario: PublicCompanyScenario) -> tuple[DynamicOrg, FeatureCheck]:
    """Found the org with a CEO root; assert the apex and its founding audit event."""
    root = RoleCharter(
        role_id=RoleId(CEO_ROLE),
        title=f"CEO, {scenario.name}",
        responsibilities=("run the company and own enterprise value",),
        ownership_scope="company",
        success_signal="enterprise-value",
        owned_artifacts=frozenset({ArtifactId("founding-charter")}),
        manager_id=None,
        authored_by=ROOT_AUTHOR,
    )
    org = DynamicOrg.found(
        root, FrozenClock(FOUNDING_EPOCH, step_seconds=1.0), SequentialIdGenerator()
    )
    came_up = (
        org.state.hierarchy.root_id() == RoleId(CEO_ROLE)
        and org.state.trail.kinds() == (OrgEventKind.ROLE_HIRED,)
    )
    return org, FeatureCheck(
        feature=FeatureName.ORG_FOUNDED,
        phase="build",
        status=FeatureStatus.PASSED if came_up else FeatureStatus.FAILED,
        detail=f"founded org with CEO root for {scenario.name}",
        evidence={
            "root_id": str(org.state.hierarchy.root_id()),
            "events": str(len(org.state.trail.events)),
        },
    )


def _auto_create_and_hire(
    org: DynamicOrg, scenario: PublicCompanyScenario
) -> tuple[DynamicOrg, FeatureCheck]:
    """Detect a capability gap and auto-create + hire the missing role.

    Proves the platform's automatic role-creation-on-gap: the CEO detects the
    scenario's gap, and the engine spawns + reports the new role with the gap's
    rationale carried into the audit detail (explainability — CLAUDE.md §3.11).
    """
    gap = OrgGap(
        kind=GapKind.SKILL_GAP,
        detected_by=RoleId(CEO_ROLE),
        rationale=scenario.gap_rationale,
        severity=5,
    )
    new_role = RoleCharter(
        role_id=RoleId(scenario.gap_role_id),
        title=scenario.gap_role_id.replace("-", " ").title(),
        responsibilities=scenario.gap_role_responsibilities,
        ownership_scope=f"{scenario.gap_role_id}-scope",
        success_signal=f"{scenario.gap_role_id}-kpi",
        owned_artifacts=frozenset(),
        manager_id=RoleId(CEO_ROLE),
        authored_by=RoleId(CEO_ROLE),
    )
    org = org.auto_create_on_gap(gap, new_role)
    last = org.state.trail.events[-1]
    hired = (
        RoleId(scenario.gap_role_id) in org.state.hierarchy
        and last.kind is OrgEventKind.ROLE_AUTO_CREATED
        and scenario.gap_rationale in last.detail  # the 'why' matches the gap
    )
    return org, FeatureCheck(
        feature=FeatureName.GAP_AUTO_CREATE_HIRE,
        phase="build",
        status=FeatureStatus.PASSED if hired else FeatureStatus.FAILED,
        detail=f"gap auto-created + hired '{scenario.gap_role_id}'",
        evidence={"role": scenario.gap_role_id, "audit_kind": last.kind.value},
    )


def _wire_comms_and_deliver_kickoff(
    org: DynamicOrg, scenario: PublicCompanyScenario
) -> FeatureCheck:
    """Register the founded roles on the bus and deliver a CEO->role kickoff.

    Proves the comms plane is live for this company: the message reaches the
    auto-created role's handler and is recorded in the append-only audit sink.
    """
    received: list[MessageEnvelope] = []

    async def role_handler(envelope: MessageEnvelope) -> None:
        received.append(envelope)

    registry = DynamicAgentRegistry()
    for role_id in org.state.hierarchy.role_ids():
        is_target = str(role_id) == scenario.gap_role_id
        handler: MessageHandler = role_handler if is_target else _noop_handler
        registry.register_agent(str(role_id), handler)
    audit = InMemoryMessageAuditSink()
    bus = InterAgentMessageBus(registry=registry, audit_sink=audit, clock=ManualClock())

    envelope = MessageEnvelope(
        performative=Performative.REQUEST,
        sender=CEO_ROLE,
        recipient=scenario.gap_role_id,
        conversation_id=f"kickoff-{scenario.slug}",
        causal_seq=0,
        dedup_key=f"kickoff-{scenario.slug}-0",
        payload={"action": "stand up your function"},
        timestamp=FOUNDING_EPOCH,
    )
    report = asyncio.run(bus.deliver(envelope))
    delivered = (
        len(received) == 1
        and received[0].recipient == scenario.gap_role_id
        and len(audit.entries()) == 1
    )
    return FeatureCheck(
        feature=FeatureName.COMMS_WIRED,
        phase="build",
        status=FeatureStatus.PASSED if delivered else FeatureStatus.FAILED,
        detail=f"kickoff delivered CEO->{scenario.gap_role_id} over the bus",
        evidence={"delivery_status": report.status.value, "audited": str(len(audit.entries()))},
    )


def _file_founding_documents(
    scenario: PublicCompanyScenario, workspace: IsolatedCompanyWorkspace
) -> tuple[LibrarianFilingService, FeatureCheck]:
    """File a founding-charter deliverable into the company's isolated store.

    Proves the document store catalogues a deliverable under the injected
    ``.autofirm/`` boundary for this company, fail-closed, and can retrieve it.
    """
    librarian = LibrarianFilingService(workspace.boundary)
    record = FiledDocumentRecord(
        logical_id="founding-charter",
        company=scenario.slug,
        kind=DeliverableKind.REPORT,
        canonical_name=f"{scenario.name} Founding Charter",
        extension="md",
        version=1,
        provenance="e2e.company_build_flow:found",
        created_at=FOUNDING_EPOCH,
    )
    entry = librarian.file(record)
    filed = (
        len(librarian.find(company=scenario.slug)) == 1
        and entry.record.logical_id == "founding-charter"
    )
    return librarian, FeatureCheck(
        feature=FeatureName.DOCUMENTS_FILED,
        phase="build",
        status=FeatureStatus.PASSED if filed else FeatureStatus.FAILED,
        detail=f"filed founding charter for {scenario.slug}",
        evidence={"relative_path": entry.relative_path},
    )


async def _noop_handler(envelope: MessageEnvelope) -> None:
    """A live but silent handler for roles other than the kickoff target."""
    return None
