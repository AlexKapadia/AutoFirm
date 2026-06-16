"""AutoFirm dynamic-org engine: a deterministic, audited, modular agent-org core.

This package is the modular, dynamic agent-organization core that lets AutoFirm
hire / fire / re-scope roles at runtime within a strict, audited hierarchy, and
automatically create new roles on detected gaps. It models the org and its
lifecycle as pure, deterministic data (roles-as-data); it deliberately does NOT
spawn real CLI sessions — that substrate coupling is a separate task.

Layering (low -> high):
* :mod:`autofirm.org.org_identifiers` — typed ids + injectable Clock/IdGenerator.
* :mod:`autofirm.org.role_charter_contract` — the manager-authored AgentSpec.
* :mod:`autofirm.org.org_lifecycle_events` — the append-only audit trail.
* :mod:`autofirm.org.artifact_ownership_ledger` — single-writer ownership.
* :mod:`autofirm.org.org_hierarchy_state` — the single-rooted acyclic tree.
* :mod:`autofirm.org.gap_detection_contract` — the gap signal that triggers
  automatic role-creation.
* :mod:`autofirm.org.org_state` — the immutable whole-org snapshot.
* :mod:`autofirm.org.org_lifecycle_internals` — pure audit/ownership/authorship helpers.
* :mod:`autofirm.org.org_lifecycle_engine` — the fail-closed mutation engine.
"""

from __future__ import annotations

from autofirm.org.org_lifecycle_engine import (
    DynamicOrg,
    OrgState,
    RoleLifecycleError,
)

__all__ = ["DynamicOrg", "OrgState", "RoleLifecycleError"]
