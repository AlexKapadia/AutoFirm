"""Synthetic, fully-controlled read model + view builders for driving the cockpit TUI in tests.

These satisfy the structural ``CockpitReadModel`` shape with hand-built, deterministic snapshots
so a Pilot test can feed known rows (populated), empty snapshots (empty state), or make any
accessor raise (error state) — and mutate the data between refreshes to prove ``r`` re-pulls.
No network, no real composition, no real tokens.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from autofirm.cockpit.core.budget_threshold_state import BudgetBand
from autofirm.cockpit.readmodels.front_door_activity_view import (
    FrontDoorActivityEntryView,
    FrontDoorActivityView,
)
from autofirm.cockpit.readmodels.org_snapshot_view import OrgRoleNodeView, OrgSnapshotView
from autofirm.cockpit.readmodels.spend_snapshot_view import SpendSnapshotView
from autofirm.foundation.money.money_amount import Money

_WHEN = datetime(2026, 6, 19, 12, 30, 0, tzinfo=UTC)


@dataclass
class FakeEpoch:
    """A stand-in kill-switch epoch (satisfies ``EpochLike``)."""

    version: int
    tripped: bool


@dataclass
class FakeEvent:
    """A stand-in recorded event (satisfies ``EventLike``)."""

    seq: int
    kind: str
    source: str
    recorded_at: datetime


class SyntheticReadModel:
    """A controllable read model: known snapshots, mutable between refreshes, optionally raising."""

    def __init__(
        self,
        *,
        org: OrgSnapshotView,
        spend: SpendSnapshotView,
        front_door: FrontDoorActivityView,
        epoch: FakeEpoch,
        events: tuple[FakeEvent, ...],
    ) -> None:
        """Seed the model with the snapshots each accessor will return."""
        self.org = org
        self.spend = spend
        self.front_door = front_door
        self.epoch = epoch
        self.events = events
        self.failing: set[str] = set()

    def _maybe_fail(self, name: str) -> None:
        if name in self.failing:
            raise RuntimeError(f"{name} source unavailable")

    def org_snapshot(self) -> OrgSnapshotView:
        self._maybe_fail("org")
        return self.org

    def spend_snapshot(self) -> SpendSnapshotView:
        self._maybe_fail("spend")
        return self.spend

    def front_door_activity(self) -> FrontDoorActivityView:
        self._maybe_fail("front_door")
        return self.front_door

    def kill_switch_epoch(self) -> FakeEpoch:
        self._maybe_fail("kill_switch")
        return self.epoch

    def recorded_events(self) -> tuple[FakeEvent, ...]:
        self._maybe_fail("events")
        return self.events


def populated_org() -> OrgSnapshotView:
    """A two-role org: a founder with one direct report."""
    return OrgSnapshotView(
        root_role_id="founder",
        root_title="Founder",
        roles=(
            OrgRoleNodeView(
                role_id="founder",
                title="Founder",
                manager_id=None,
                direct_report_ids=("coo",),
            ),
            OrgRoleNodeView(
                role_id="coo",
                title="Chief Operating Officer",
                manager_id="founder",
                direct_report_ids=(),
            ),
        ),
        total_role_count=2,
    )


def empty_org() -> OrgSnapshotView:
    """An org with no roles (empty state)."""
    return OrgSnapshotView(root_role_id="", root_title="", roles=(), total_role_count=0)


def populated_spend() -> SpendSnapshotView:
    """Spend with a budget so a WARN_50 band shows, plus a per-model rollup."""
    return SpendSnapshotView(
        grand_total=Money(Decimal("60.00"), "USD"),
        per_role={"coo": Money(Decimal("60.00"), "USD")},
        per_use_case={"research": Money(Decimal("60.00"), "USD")},
        per_model={"openai/gpt-4": Money(Decimal("60.00"), "USD")},
        budget=Money(Decimal("100.00"), "USD"),
        band=BudgetBand.WARN_50,
        ledger_verified=True,
    )


def empty_spend() -> SpendSnapshotView:
    """Zero spend, no budget configured (empty state, but a zero total in the subtitle)."""
    return SpendSnapshotView(
        grand_total=Money(Decimal("0.00"), "USD"),
        per_role={},
        per_use_case={},
        per_model={},
        budget=None,
        band=None,
        ledger_verified=True,
    )


def populated_front_door() -> FrontDoorActivityView:
    """One recorded front-door request."""
    return FrontDoorActivityView(
        entries=(
            FrontDoorActivityEntryView(
                correlation_id="req-001",
                requester_display="Jane Owner",
                routing_outcome="routed_to_capable_role",
                handler_role="Chief Operating Officer",
                delivery_status="delivered",
                timestamp=_WHEN,
            ),
        )
    )


def empty_front_door() -> FrontDoorActivityView:
    """No front-door activity (empty state)."""
    return FrontDoorActivityView(entries=())


def populated_events() -> tuple[FakeEvent, ...]:
    """Two recorded cockpit events."""
    return (
        FakeEvent(seq=0, kind="org_changed", source="lifecycle", recorded_at=_WHEN),
        FakeEvent(seq=1, kind="spend_recorded", source="ledger", recorded_at=_WHEN),
    )


def synthetic_model(*, tripped: bool = False, populated: bool = True) -> SyntheticReadModel:
    """Build a synthetic read model, populated or empty, untripped or tripped."""
    if populated:
        return SyntheticReadModel(
            org=populated_org(),
            spend=populated_spend(),
            front_door=populated_front_door(),
            epoch=FakeEpoch(version=3, tripped=tripped),
            events=populated_events(),
        )
    return SyntheticReadModel(
        org=empty_org(),
        spend=empty_spend(),
        front_door=empty_front_door(),
        epoch=FakeEpoch(version=0, tripped=tripped),
        events=(),
    )
