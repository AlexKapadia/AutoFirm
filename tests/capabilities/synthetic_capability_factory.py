"""Synthetic, deterministic builders for the capability-registry test suite.

What this provides
------------------
Side-effect-free factories for valid :class:`RoleCharter` instances, a freshly
founded :class:`CapabilityRecordingOrg`, pinned determinism seams, and a directly
sealed :class:`CapabilityRegistryEvent` so tamper tests can mint a valid event and
then corrupt it. No network, no real I/O, no real PII — synthetic only
(CLAUDE.md §5.5 / §3.12).

These builders deliberately produce *valid* artifacts by default; tests construct
the invalid / adversarial variants inline so the failure each test targets is
explicit and local.
"""

from __future__ import annotations

from datetime import UTC, datetime

from autofirm.capabilities.capability_descriptor import (
    UNSET_CLEARANCE,
    CapabilityDescriptor,
    CapabilityId,
    CapabilityProvenance,
)
from autofirm.capabilities.capability_growth_log import CapabilityGrowthLog
from autofirm.capabilities.capability_recording_org import CapabilityRecordingOrg
from autofirm.capabilities.capability_registry_event import (
    CapabilityRegistryEvent,
    RegistryEventKind,
)
from autofirm.org.org_identifiers import (
    ArtifactId,
    FrozenClock,
    RoleId,
    SequentialIdGenerator,
)
from autofirm.org.role_charter_contract import ROOT_AUTHOR, RoleCharter

# A fixed epoch so growth-event timestamps are deterministic and assertable.
EPOCH = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)
CEO = "ceo"


def fresh_clock(step_seconds: float = 1.0) -> FrozenClock:
    """A deterministic clock starting at EPOCH, advancing ``step_seconds`` per call."""
    return FrozenClock(EPOCH, step_seconds=step_seconds)


def root_charter(role_id: str = CEO) -> RoleCharter:
    """A valid root charter authored by the founder sentinel."""
    return RoleCharter(
        role_id=RoleId(role_id),
        title=role_id.replace("-", " ").title(),
        responsibilities=("run the company and own enterprise value",),
        ownership_scope="company",
        success_signal="enterprise-value",
        owned_artifacts=frozenset({ArtifactId(f"{role_id}-charter")}),
        manager_id=None,
        authored_by=ROOT_AUTHOR,
    )


def report_charter(
    role_id: str,
    responsibilities: tuple[str, ...],
    *,
    manager_id: str = CEO,
) -> RoleCharter:
    """A valid non-root charter managed + authored by ``manager_id``."""
    return RoleCharter(
        role_id=RoleId(role_id),
        title=role_id.replace("-", " ").title(),
        responsibilities=responsibilities,
        ownership_scope=f"{role_id}-scope",
        success_signal=f"{role_id}-kpi",
        owned_artifacts=frozenset(),
        manager_id=RoleId(manager_id),
        authored_by=RoleId(manager_id),
    )


def founded_recording_org(root_id: str = CEO) -> CapabilityRecordingOrg:
    """A freshly founded recording org with pinned determinism seams."""
    return CapabilityRecordingOrg.found(
        root_charter(root_id),
        fresh_clock(),
        SequentialIdGenerator(),
        fresh_clock(),
    )


def valid_descriptor(
    capability_id: str = "role-x",
    *,
    keywords: frozenset[str] = frozenset({"alpha", "beta"}),
    owning_role_id: str | None = None,
    clearance: str = UNSET_CLEARANCE,
    maturity: str = "active",
) -> CapabilityDescriptor:
    """A valid descriptor for direct event/tamper tests (defaults are routable)."""
    return CapabilityDescriptor(
        capability_id=CapabilityId(capability_id),
        name=f"{capability_id} capability",
        keywords=keywords,
        owning_role_id=RoleId(owning_role_id or capability_id),
        required_clearance=clearance,
        provenance=CapabilityProvenance(
            kind="hire", org_event_seq=0, rationale="synthetic test capability"
        ),
        maturity=maturity,  # type: ignore[arg-type]
    )


def sealed_event(  # noqa: PLR0913 -- mirrors the wide, keyword-only seal() surface
    log: CapabilityGrowthLog,
    *,
    kind: RegistryEventKind = "CAPABILITY_ADDED",
    descriptor: CapabilityDescriptor | None = None,
    triggered_by: str = CEO,
    org_event_ref: int = 0,
    rationale: str = "synthetic growth",
) -> CapabilityRegistryEvent:
    """Seal one valid, correctly-chained event against ``log`` (for append/tamper tests)."""
    return log.seal(
        kind=kind,
        descriptor=descriptor if descriptor is not None else valid_descriptor(),
        triggered_by=RoleId(triggered_by),
        org_event_ref=org_event_ref,
        rationale=rationale,
        occurred_at=EPOCH,
    )
