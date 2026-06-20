"""``frozen=True`` + ``slots=True`` immutability proofs for every cockpit read-model view.

Why this file exists (CLAUDE.md §3.6)
-------------------------------------
The behavioural read-model suites assert read-only mappings and (sometimes) ``frozen`` via
``pytest.raises(AttributeError)``, but they do not pin BOTH dataclass flags on every view:
mutmut's ``slots=True`` -> ``slots=False`` (grows a ``__dict__`` that silently absorbs forged
attributes) and ``frozen=True`` -> ``frozen=False`` (lets a "frozen" snapshot be mutated after
presentation) mutants survive. Each test below asserts assignment raises
:class:`dataclasses.FrozenInstanceError` (kills ``frozen=False``) AND that the instance has no
``__dict__`` (kills ``slots=False``), for all five view classes.
"""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from autofirm.cockpit.readmodels.front_door_activity_view import (
    FrontDoorActivityEntryView,
    FrontDoorActivityView,
)
from autofirm.cockpit.readmodels.org_snapshot_view import OrgRoleNodeView, OrgSnapshotView
from autofirm.cockpit.readmodels.spend_snapshot_view import SpendSnapshotView
from autofirm.foundation.money.money_amount import Money

_TS = datetime(2026, 6, 19, 12, 0, tzinfo=UTC)


def _money(amount: str) -> Money:
    return Money(Decimal(amount), "USD")


def _entry() -> FrontDoorActivityEntryView:
    return FrontDoorActivityEntryView(
        correlation_id="c-0",
        requester_display="Ada",
        routing_outcome="routed_to_capable_role",
        handler_role="Engineer",
        delivery_status="delivered",
        timestamp=_TS,
    )


def _node() -> OrgRoleNodeView:
    return OrgRoleNodeView(
        role_id="r-0", title="CEO", manager_id=None, direct_report_ids=("r-1",)
    )


def _spend_view() -> SpendSnapshotView:
    return SpendSnapshotView(
        grand_total=_money("10.00"),
        per_role={"r-0": _money("10.00")},
        per_use_case={"uc-0": _money("10.00")},
        per_model={"openai/gpt-x": _money("10.00")},
        budget=None,
        band=None,
        ledger_verified=True,
    )


def test_front_door_entry_view_is_frozen_and_slotted() -> None:
    obj = _entry()
    with pytest.raises(dataclasses.FrozenInstanceError):
        obj.delivery_status = "lost"  # type: ignore[misc]
    assert not hasattr(obj, "__dict__")


def test_front_door_activity_view_is_frozen_and_slotted() -> None:
    obj = FrontDoorActivityView(entries=(_entry(),))
    with pytest.raises(dataclasses.FrozenInstanceError):
        obj.entries = ()  # type: ignore[misc]
    assert not hasattr(obj, "__dict__")


def test_org_role_node_view_is_frozen_and_slotted() -> None:
    obj = _node()
    with pytest.raises(dataclasses.FrozenInstanceError):
        obj.title = "tampered"  # type: ignore[misc]
    assert not hasattr(obj, "__dict__")


def test_org_snapshot_view_is_frozen_and_slotted() -> None:
    obj = OrgSnapshotView(
        root_role_id="r-0", root_title="CEO", roles=(_node(),), total_role_count=1
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        obj.total_role_count = 99  # type: ignore[misc]
    assert not hasattr(obj, "__dict__")


def test_spend_snapshot_view_is_frozen_and_slotted() -> None:
    obj = _spend_view()
    with pytest.raises(dataclasses.FrozenInstanceError):
        obj.ledger_verified = False  # type: ignore[misc]
    assert not hasattr(obj, "__dict__")
