"""The org-snapshot adapter: project the live org hierarchy into a cockpit read-model.

What this does
--------------
Defines :func:`build_org_snapshot_view`, which walks the on-main
:class:`~autofirm.org.org_hierarchy_state.OrgHierarchy` carried by an
:class:`~autofirm.org.org_state.OrgState` and maps every role into a flattened, string-only
:class:`~autofirm.cockpit.readmodels.org_snapshot_view.OrgRoleNodeView`, then assembles the
whole :class:`~autofirm.cockpit.readmodels.org_snapshot_view.OrgSnapshotView` (root id/title,
all nodes in stable sorted order, exact count). Read-only.

Why it exists / where it sits
-----------------------------
This is the seam that turns the live org tree into the cockpit's fleet-tree panel data. It
accepts an :class:`OrgState` (obtained from ``DynamicOrg.state`` — a property, not a call), so
the cockpit never drives a lifecycle transition; it only reads the current snapshot. Sits in
the adapters layer (the only cockpit layer allowed to import on-main domain types).

Security / compliance invariants upheld
---------------------------------------
* **Read-only projection (CLAUDE.md §3.2):** the adapter only queries the hierarchy
  (``root_id`` / ``role_ids`` / ``charter`` / ``direct_reports``) and copies fields into
  immutable views — it never mutates the org.
* **Deterministic ordering (§3.11):** nodes and each node's reports are emitted in sorted id
  order, so the same org always yields a byte-identical snapshot (diffable across heartbeats).
"""

from __future__ import annotations

from autofirm.cockpit.readmodels.org_snapshot_view import OrgRoleNodeView, OrgSnapshotView
from autofirm.org.org_state import OrgState

__all__ = ["build_org_snapshot_view"]


def build_org_snapshot_view(state: OrgState) -> OrgSnapshotView:
    """Project an :class:`OrgState`'s hierarchy into an immutable :class:`OrgSnapshotView`.

    Args:
        state: The org state to snapshot (e.g. ``dynamic_org.state``).

    Returns:
        An :class:`OrgSnapshotView` with every role node (sorted by id), the root identity,
        and the exact role count.
    """
    hierarchy = state.hierarchy
    root_id = hierarchy.root_id()
    nodes = tuple(
        OrgRoleNodeView(
            role_id=str(role_id),
            title=hierarchy.charter(role_id).title,
            manager_id=_manager_id_of(hierarchy.charter(role_id).manager_id),
            direct_report_ids=tuple(
                sorted(str(report) for report in hierarchy.direct_reports(role_id))
            ),
        )
        for role_id in sorted(hierarchy.role_ids())
    )
    return OrgSnapshotView(
        root_role_id=str(root_id),
        root_title=hierarchy.charter(root_id).title,
        roles=nodes,
        total_role_count=len(nodes),
    )


def _manager_id_of(manager_id: str | None) -> str | None:
    """Flatten an optional on-main ``RoleId`` manager reference to ``str | None``.

    The root role's ``manager_id`` is ``None`` (no parent); a non-root role's is stringified.
    """
    return None if manager_id is None else str(manager_id)
