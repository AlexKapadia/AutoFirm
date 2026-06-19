"""Facade re-exporting the eight capability factories the composition root assembles.

What this does
--------------
Collects the per-layer capability factories (egress/security in
:mod:`autofirm.runtime.egress_capability_factories`; knowledge/comms/org in
:mod:`autofirm.runtime.knowledge_capability_factories`) behind one import surface so the
composition root imports a single module. No logic lives here — it is a curated re-export
that keeps the root's import block small and the per-factory files under the 300-line bar
(§5.7).

Why it exists / where it sits
-----------------------------
The composition root (:mod:`autofirm.runtime.platform_composition_root`) builds exactly
eight wired capabilities; this facade is the named seam it imports them from.
"""

from __future__ import annotations

from autofirm.runtime.egress_capability_factories import (
    build_audit_capability,
    build_cost_ledger_capability,
    build_gateway_capability,
    build_kill_switch_capability,
)
from autofirm.runtime.knowledge_capability_factories import (
    build_capability_registry_capability,
    build_comms_capability,
    build_memory_capability,
    build_org_frontdoor_capability,
)

__all__ = [
    "build_audit_capability",
    "build_capability_registry_capability",
    "build_comms_capability",
    "build_cost_ledger_capability",
    "build_gateway_capability",
    "build_kill_switch_capability",
    "build_memory_capability",
    "build_org_frontdoor_capability",
]
