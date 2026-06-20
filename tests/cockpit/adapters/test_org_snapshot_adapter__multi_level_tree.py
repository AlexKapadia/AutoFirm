"""org_snapshot_adapter: exact projection of single-root, flat, and multi-level org trees."""

from __future__ import annotations

from datetime import UTC, datetime

from autofirm.cockpit.adapters.org_snapshot_adapter import build_org_snapshot_view
from autofirm.cockpit.readmodels.org_snapshot_view import OrgRoleNodeView, OrgSnapshotView
from autofirm.org.org_identifiers import FrozenClock, RoleId, SequentialIdGenerator
from autofirm.org.org_lifecycle_engine import DynamicOrg
from autofirm.org.role_charter_contract import ROOT_AUTHOR, RoleCharter

_CLOCK = FrozenClock(datetime(2026, 6, 19, 0, 0, tzinfo=UTC), step_seconds=1)


def _charter(role_id: str, title: str, manager_id: str | None) -> RoleCharter:
    return RoleCharter(
        role_id=RoleId(role_id),
        title=title,
        responsibilities=("do work",),
        ownership_scope="its scope",
        success_signal="it is judged",
        owned_artifacts=frozenset(),
        manager_id=None if manager_id is None else RoleId(manager_id),
        authored_by=ROOT_AUTHOR if manager_id is None else RoleId(manager_id),
    )


def _node(snap: OrgSnapshotView, role_id: str) -> OrgRoleNodeView:
    return next(n for n in snap.roles if n.role_id == role_id)


def test_single_root_only_org() -> None:
    org = DynamicOrg.found(_charter("r-root", "Founder", None), _CLOCK, SequentialIdGenerator())
    snap = build_org_snapshot_view(org.state)
    assert snap.root_role_id == "r-root"
    assert snap.root_title == "Founder"
    assert snap.total_role_count == 1
    root = _node(snap, "r-root")
    assert root.manager_id is None
    assert root.direct_report_ids == ()


def test_wide_flat_org_reports_all_under_root() -> None:
    org = DynamicOrg.found(_charter("r-root", "Founder", None), _CLOCK, SequentialIdGenerator())
    for i in range(4):
        org = org.hire(_charter(f"r-{i}", f"Lead {i}", "r-root"))
    snap = build_org_snapshot_view(org.state)
    assert snap.total_role_count == 5
    root = _node(snap, "r-root")
    assert root.direct_report_ids == ("r-0", "r-1", "r-2", "r-3")  # sorted, all four
    for i in range(4):
        leaf = _node(snap, f"r-{i}")
        assert leaf.manager_id == "r-root"
        assert leaf.direct_report_ids == ()


def test_multi_level_org_every_edge_is_exact() -> None:
    org = DynamicOrg.found(_charter("root", "CEO", None), _CLOCK, SequentialIdGenerator())
    org = org.hire(_charter("m1", "VP Eng", "root"))
    org = org.hire(_charter("m2", "VP Fin", "root"))
    org = org.hire(_charter("l1", "Eng A", "m1"))
    org = org.hire(_charter("l2", "Eng B", "m1"))
    org = org.hire(_charter("l3", "Analyst", "m2"))
    snap = build_org_snapshot_view(org.state)

    assert snap.root_role_id == "root"
    assert snap.root_title == "CEO"
    assert snap.total_role_count == 6
    assert _node(snap, "root").manager_id is None
    assert _node(snap, "root").direct_report_ids == ("m1", "m2")
    assert _node(snap, "m1").manager_id == "root"
    assert _node(snap, "m1").direct_report_ids == ("l1", "l2")
    assert _node(snap, "m2").manager_id == "root"
    assert _node(snap, "m2").direct_report_ids == ("l3",)
    assert _node(snap, "l1").manager_id == "m1"
    assert _node(snap, "l1").direct_report_ids == ()
    assert _node(snap, "l3").manager_id == "m2"


def test_nodes_emitted_in_sorted_id_order() -> None:
    org = DynamicOrg.found(_charter("root", "CEO", None), _CLOCK, SequentialIdGenerator())
    org = org.hire(_charter("zeta", "Z", "root"))
    org = org.hire(_charter("alpha", "A", "root"))
    snap = build_org_snapshot_view(org.state)
    assert [n.role_id for n in snap.roles] == ["alpha", "root", "zeta"]


def test_count_always_equals_number_of_nodes() -> None:
    org = DynamicOrg.found(_charter("root", "CEO", None), _CLOCK, SequentialIdGenerator())
    org = org.hire(_charter("a", "A", "root"))
    snap = build_org_snapshot_view(org.state)
    assert snap.total_role_count == len(snap.roles) == 2
