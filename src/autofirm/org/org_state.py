"""The immutable whole-org snapshot: hierarchy + ownership ledger + audit trail.

What this does
--------------
Defines :class:`OrgState`, the single immutable value that captures the entire
state of a dynamic org at one point in time: its :class:`OrgHierarchy` (the
acyclic role tree), its :class:`ArtifactOwnershipLedger` (single-writer ownership),
and its :class:`OrgAuditTrail` (the append-only history of how it got here). Every
lifecycle transition consumes one ``OrgState`` and produces the next one.

Why it exists / where it sits
-----------------------------
Extracted into its own module so both the lifecycle engine and its pure internal
helpers can depend on the state type without importing each other (avoids an
import cycle) and so each module stays a single responsibility (CLAUDE.md §5.7).

Security / compliance invariants upheld
---------------------------------------
* **Immutable (append-only state, §3.8):** frozen; a transition never mutates a
  prior state in place, so any operation sequence is a pure, replayable fold.
"""

from __future__ import annotations

from dataclasses import dataclass

from autofirm.org.artifact_ownership_ledger import ArtifactOwnershipLedger
from autofirm.org.org_hierarchy_state import OrgHierarchy
from autofirm.org.org_lifecycle_events import OrgAuditTrail

__all__ = ["OrgState"]


@dataclass(frozen=True, slots=True)
class OrgState:
    """An immutable snapshot of the whole org: hierarchy + ownership + audit trail."""

    hierarchy: OrgHierarchy
    ownership: ArtifactOwnershipLedger
    trail: OrgAuditTrail
