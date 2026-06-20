"""The org-snapshot panel: renders the fleet tree (role, title, manager, direct reports).

What this does
--------------
Defines :class:`OrgSnapshotPanel`, which maps an
:class:`~autofirm.cockpit.readmodels.org_snapshot_view.OrgSnapshotView` into table rows — one
per role node, showing its id, title, the manager it reports to, and how many direct reports it
has. An org with no roles renders the empty-state message via the base panel.

Why it exists / where it sits
-----------------------------
The operator's "who reports to whom" view. Sits in the tui layer; depends only on the base
panel and the org read-model DTO (no on-main import).
"""

from __future__ import annotations

from autofirm.cockpit.readmodels.org_snapshot_view import OrgSnapshotView
from autofirm.cockpit.tui.cockpit_table_panel import CockpitTablePanel

__all__ = ["OrgSnapshotPanel"]

_NO_MANAGER = "—"  # the root role reports to no one


class OrgSnapshotPanel(CockpitTablePanel):
    """A panel that renders the org tree, one row per role node."""

    def __init__(self) -> None:
        """Build the org panel with its columns and empty-state message."""
        super().__init__(
            title="Org — fleet tree",
            columns=("Role", "Title", "Reports to", "Direct reports"),
            empty_message="No roles in the org yet.",
            panel_id="org-snapshot-panel",
        )

    def show(self, view: OrgSnapshotView) -> None:
        """Render every role node in the snapshot (or the empty message when there are none)."""
        rows = tuple(
            (
                node.role_id,
                node.title,
                node.manager_id if node.manager_id is not None else _NO_MANAGER,
                str(len(node.direct_report_ids)),
            )
            for node in view.roles
        )
        self.set_subtitle(f"{view.total_role_count} role(s) · root {view.root_title}")
        self.display_rows(rows)
