"""The org-snapshot read-model: a presentation-ready projection of the live org tree.

What this does
--------------
Defines :class:`OrgRoleNodeView` (one immutable node of the org tree — its id, title, the
manager it reports to, and its direct reports) and :class:`OrgSnapshotView` (the whole tree:
the root id/title, every node, and the exact role count). These are the cockpit-facing
projection of the on-main :class:`~autofirm.org.org_hierarchy_state.OrgHierarchy`, built by
:mod:`~autofirm.cockpit.adapters.org_snapshot_adapter` and flattened to plain strings so the
fleet-tree panel binds a stable shape with no on-main import.

Why it exists / where it sits
-----------------------------
The operator's "who reports to whom" tree renders this view. Every node carries both its
``manager_id`` (the up-edge) and its ``direct_report_ids`` (the down-edges), so the UI can
draw the tree without re-querying the hierarchy. Sits in the read-model layer; stdlib only.

Security / compliance invariants upheld
---------------------------------------
* **Read-only projection (CLAUDE.md §3.2):** a node view is an immutable copy; it holds no
  handle back into the live :class:`OrgHierarchy`.
* **Hashable-friendly immutability:** every field is a frozen scalar or a tuple, so a node
  and the whole snapshot are hashable and safe to cache/diff between heartbeats.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["OrgRoleNodeView", "OrgSnapshotView"]


@dataclass(frozen=True, slots=True)
class OrgRoleNodeView:
    """One immutable node of the projected org tree (id, title, up-edge, down-edges).

    Attributes:
        role_id: This role's stable id (string-flattened from the on-main ``RoleId``).
        title: The role's human-readable title.
        manager_id: The id of the role this one reports to, or ``None`` for the root.
        direct_report_ids: The ids of this role's direct reports, in stable sorted order.
    """

    role_id: str
    title: str
    manager_id: str | None
    direct_report_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class OrgSnapshotView:
    """An immutable snapshot of the whole org tree (root + every node + exact count).

    Attributes:
        root_role_id: The single apex role's id.
        root_title: The apex role's human-readable title.
        roles: Every role node, in stable sorted-by-``role_id`` order.
        total_role_count: The exact number of roles in the snapshot (``== len(roles)``).
    """

    root_role_id: str
    root_title: str
    roles: tuple[OrgRoleNodeView, ...]
    total_role_count: int
