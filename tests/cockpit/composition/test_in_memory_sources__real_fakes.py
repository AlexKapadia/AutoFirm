"""in_memory_sources: builds real on-main fakes; default + injected kill-switch epoch."""

from __future__ import annotations

from datetime import UTC, datetime

from autofirm.cockpit.composition.in_memory_sources import (
    CockpitSources,
    default_in_memory_sources,
)
from autofirm.modelgateway.kill_switch_epoch import KillSwitchEpoch
from autofirm.org.org_identifiers import FrozenClock

_CLOCK = FrozenClock(datetime(2026, 6, 19, 0, 0, tzinfo=UTC), step_seconds=1)


def test_default_sources_are_a_bundle() -> None:
    sources = default_in_memory_sources(_CLOCK)
    assert isinstance(sources, CockpitSources)


def test_default_trail_is_empty() -> None:
    assert default_in_memory_sources(_CLOCK).front_door_trail.entries() == ()


def test_default_ledger_is_empty_and_verified() -> None:
    ledger = default_in_memory_sources(_CLOCK).cost_ledger
    assert ledger.records() == ()
    assert ledger.verify() is True


def test_default_org_is_single_root() -> None:
    state = default_in_memory_sources(_CLOCK).org_state
    assert state.hierarchy.root_id() == "cockpit-root"
    assert state.hierarchy.charter(state.hierarchy.root_id()).title == "Founder"
    assert len(tuple(state.hierarchy.role_ids())) == 1


def test_default_kill_switch_is_untripped_version_zero() -> None:
    epoch = default_in_memory_sources(_CLOCK).kill_switch.current()
    assert epoch.version == 0
    assert epoch.tripped is False


def test_injected_kill_switch_epoch_is_reported() -> None:
    seed = KillSwitchEpoch(version=7, tripped=True)
    epoch = default_in_memory_sources(_CLOCK, kill_switch_epoch=seed).kill_switch.current()
    assert epoch is seed
    assert epoch.version == 7
    assert epoch.tripped is True
