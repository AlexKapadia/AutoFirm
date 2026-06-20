"""OrgSnapshotView/OrgRoleNodeView: immutability, hashability, exact fields."""

from __future__ import annotations

import pytest

from autofirm.cockpit.readmodels.org_snapshot_view import OrgRoleNodeView, OrgSnapshotView


def _node(role_id: str = "r-1", manager_id: str | None = "r-0") -> OrgRoleNodeView:
    return OrgRoleNodeView(
        role_id=role_id,
        title="Engineer",
        manager_id=manager_id,
        direct_report_ids=("r-2", "r-3"),
    )


def test_role_node_carries_every_field_exactly() -> None:
    node = _node()
    assert node.role_id == "r-1"
    assert node.title == "Engineer"
    assert node.manager_id == "r-0"
    assert node.direct_report_ids == ("r-2", "r-3")


def test_root_node_has_none_manager() -> None:
    assert _node(role_id="r-0", manager_id=None).manager_id is None


def test_role_node_is_frozen() -> None:
    node = _node()
    with pytest.raises(AttributeError):
        node.title = "mutated"  # type: ignore[misc]


def test_role_node_is_hashable() -> None:
    # tuple-only fields keep the node hashable (cacheable/diffable between heartbeats).
    assert {_node(), _node()} == {_node()}


def test_snapshot_view_is_hashable_and_carries_count() -> None:
    nodes = (_node("r-0", None), _node("r-1", "r-0"))
    snap = OrgSnapshotView(
        root_role_id="r-0", root_title="Founder", roles=nodes, total_role_count=2
    )
    assert snap.root_role_id == "r-0"
    assert snap.total_role_count == 2
    assert hash(snap) == hash(
        OrgSnapshotView(root_role_id="r-0", root_title="Founder", roles=nodes, total_role_count=2)
    )


def test_snapshot_view_is_frozen() -> None:
    snap = OrgSnapshotView(root_role_id="r-0", root_title="F", roles=(), total_role_count=0)
    with pytest.raises(AttributeError):
        snap.total_role_count = 99  # type: ignore[misc]
