"""AutoFirm capability registry: the DYNAMIC, EVOLVING, tamper-evident capability set.

This package replaces the locked-in static capability list with a registry that
GROWS automatically as the org evolves. Hiring, auto-creating, re-scoping, or
firing a role projects (purely) onto an append-only, RFC-6962 hash-chained growth
log; the CURRENT routable capability set is derived by a pure replay of that log.
The growth log doubles as the showcase of HOW the org's capabilities evolved.

Layering (low -> high):
* :mod:`~autofirm.capabilities.capability_descriptor` — one advertised capability
  (frozen, deny-by-default clearance, routable-or-refuse keyword surface).
* :mod:`~autofirm.capabilities.capability_registry_event` — one append-only,
  RFC-6962-chained growth event (reuses :mod:`autofirm.audit.rfc6962_hashing`).
* :mod:`~autofirm.capabilities.capability_growth_log` — the append-only, gapless,
  hash-chained log; the source of truth, with fail-closed tamper detection.
* :mod:`~autofirm.capabilities.org_event_to_capability_projection` — the PURE map
  from an org-lifecycle event to the capability-growth it implies (auto-growth).
* :mod:`~autofirm.capabilities.live_capability_registry` — the CURRENT set, derived
  by pure replay (verification-before-load); REPLACES the static enumeration.
* :mod:`~autofirm.capabilities.capability_recording_org` — the DynamicOrg wrapper
  that grows the log automatically on each accepted lifecycle transition.
"""

from __future__ import annotations

from autofirm.capabilities.capability_descriptor import (
    UNSET_CLEARANCE,
    CapabilityDescriptor,
    CapabilityId,
    CapabilityProvenance,
)
from autofirm.capabilities.capability_growth_log import CapabilityGrowthLog, GrowthLogError
from autofirm.capabilities.capability_recording_org import CapabilityRecordingOrg
from autofirm.capabilities.capability_registry_event import (
    CapabilityRegistryEvent,
    RegistryEventKind,
)
from autofirm.capabilities.live_capability_registry import LiveCapabilityRegistry
from autofirm.capabilities.org_event_to_capability_projection import (
    ProjectedGrowth,
    project_org_event,
)

__all__ = [
    "UNSET_CLEARANCE",
    "CapabilityDescriptor",
    "CapabilityGrowthLog",
    "CapabilityId",
    "CapabilityProvenance",
    "CapabilityRecordingOrg",
    "CapabilityRegistryEvent",
    "GrowthLogError",
    "LiveCapabilityRegistry",
    "ProjectedGrowth",
    "RegistryEventKind",
    "project_org_event",
]
