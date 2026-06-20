"""kill_switch_source: the in-memory fake returns the held epoch; observe-only seam."""

from __future__ import annotations

from autofirm.cockpit.adapters.kill_switch_source import (
    InMemoryKillSwitchSource,
    KillSwitchSource,
)
from autofirm.modelgateway.kill_switch_epoch import KillSwitchEpoch


def test_current_returns_the_held_untripped_epoch() -> None:
    epoch = KillSwitchEpoch(version=3, tripped=False)
    source = InMemoryKillSwitchSource(epoch)
    assert source.current() is epoch
    assert source.current().version == 3
    assert source.current().tripped is False


def test_current_returns_the_held_tripped_epoch() -> None:
    epoch = KillSwitchEpoch(version=4, tripped=True)
    source = InMemoryKillSwitchSource(epoch)
    assert source.current().tripped is True


def test_current_is_stable_across_calls() -> None:
    epoch = KillSwitchEpoch(version=1)
    source = InMemoryKillSwitchSource(epoch)
    assert source.current() is source.current()  # observe-only: same value, no mutation


def test_in_memory_source_satisfies_the_protocol() -> None:
    source: KillSwitchSource = InMemoryKillSwitchSource(KillSwitchEpoch(version=0))
    assert isinstance(source.current(), KillSwitchEpoch)


def test_source_has_no_trip_or_rearm_write_surface() -> None:
    # observe-only: the cockpit must NOT expose a way to flip the kill-switch from here.
    source = InMemoryKillSwitchSource(KillSwitchEpoch(version=0))
    assert not hasattr(source, "trip")
    assert not hasattr(source, "rearm")
    assert not hasattr(source, "reset")
