"""Property + combinatorial tests: the current set IS a pure replay of the log.

The load-bearing invariant of the whole registry (data-contracts.md §9): for ANY
sequence of hire / auto_create / rescope / fire, the CURRENT capability set equals
a pure replay of the growth log — never drifting from the recorded history, never
duplicating a capability_id, always gapless. These Hypothesis machines drive
arbitrary org evolutions and re-assert the invariant after every step, plus a
combinatorial scale test (thousands of hires) proving no ceiling and ~O(n) replay.
"""

from __future__ import annotations

import pytest
from hypothesis import HealthCheck, settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, precondition, rule

from autofirm.capabilities.capability_growth_log import CapabilityGrowthLog
from autofirm.capabilities.capability_recording_org import CapabilityRecordingOrg
from autofirm.capabilities.live_capability_registry import LiveCapabilityRegistry
from autofirm.org.org_identifiers import RoleId
from autofirm.org.org_lifecycle_engine import RoleLifecycleError
from tests.capabilities.synthetic_capability_factory import (
    CEO,
    founded_recording_org,
    report_charter,
)

# A pool of distinct, routable responsibility phrases so every hired role advertises
# at least one keyword (an un-keyworded role would not be advertised — by design).
_VOCAB = ("alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta")


def _replay(rec: CapabilityRecordingOrg) -> dict[str, str]:
    """The current set as {capability_id: maturity} via a fresh pure replay."""
    registry = LiveCapabilityRegistry.from_growth_log(rec.growth_log)
    return {str(d.capability_id): d.maturity for d in registry.descriptors()}


@settings(
    max_examples=150,
    stateful_step_count=40,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
)
class CapabilityEvolutionMachine(RuleBasedStateMachine):
    """Drives arbitrary org evolutions, re-asserting the replay invariant each step."""

    def __init__(self) -> None:
        """Found a fresh recording org and seed the independent mirror model."""
        super().__init__()
        self.rec = founded_recording_org(CEO)
        self.counter = 0
        # Mirror model: capability_id -> True(live) / False(deprecated), maintained
        # INDEPENDENTLY of the registry so the invariant compares two derivations.
        self.expected_live: set[str] = {CEO}

    def _live_reports(self) -> list[str]:
        return sorted(r for r in self.expected_live if r != CEO)

    @rule(idx=st.integers(min_value=0, max_value=7))
    def hire(self, idx: int) -> None:
        self.counter += 1
        rid = f"role-{self.counter}"
        kw = _VOCAB[idx]
        try:
            self.rec = self.rec.hire(report_charter(rid, (f"own {kw} work",)))
        except RoleLifecycleError:
            return  # refused mutation grows nothing — invariant still holds
        self.expected_live.add(rid)

    @precondition(lambda self: len(self._live_reports()) > 0)
    @rule(idx=st.integers(min_value=0, max_value=7), data=st.data())
    def rescope(self, idx: int, data: st.DataObject) -> None:
        rid = data.draw(st.sampled_from(self._live_reports()))
        kw = _VOCAB[idx]
        try:
            self.rec = self.rec.rescope(report_charter(rid, (f"own {kw} and ops",)))
        except RoleLifecycleError:
            return

    @precondition(lambda self: len(self._live_reports()) > 0)
    @rule(data=st.data())
    def fire(self, data: st.DataObject) -> None:
        rid = data.draw(st.sampled_from(self._live_reports()))
        try:
            self.rec = self.rec.fire(RoleId(rid))
        except RoleLifecycleError:
            return
        self.expected_live.discard(rid)

    @invariant()
    def current_set_equals_pure_replay(self) -> None:
        replayed = _replay(self.rec)
        # The live (non-deprecated) capability ids equal the independently-tracked
        # expected set — the registry never drifts from the recorded evolution.
        assert set(replayed) == self.expected_live
        # Every live descriptor is 'active' (deprecated ones are dropped from the set).
        assert all(maturity == "active" for maturity in replayed.values())

    @invariant()
    def log_is_gapless_and_chain_verifies(self) -> None:
        events = self.rec.growth_log.events()
        assert [e.seq for e in events] == list(range(len(events)))  # gapless
        assert self.rec.growth_log.verify() is True  # tamper-evident chain intact

    @invariant()
    def no_duplicate_live_capability_id(self) -> None:
        ids = [str(d.capability_id) for d in self.rec.live_registry().descriptors()]
        assert len(ids) == len(set(ids))  # a capability_id appears at most once


TestCapabilityEvolution = CapabilityEvolutionMachine.TestCase


@pytest.mark.property
def test_replay_is_deterministic_across_repeats() -> None:
    # Determinism (§3.11): replaying the SAME log many times yields the identical set.
    rec = founded_recording_org(CEO)
    for i in range(20):
        rec = rec.hire(report_charter(f"r-{i}", (f"own {_VOCAB[i % len(_VOCAB)]} work",)))
    def _replay_ids() -> tuple[str, ...]:
        registry = LiveCapabilityRegistry.from_growth_log(rec.growth_log)
        return tuple(str(d.capability_id) for d in registry.descriptors())

    runs = {_replay_ids() for _ in range(8)}
    assert len(runs) == 1  # every replay identical


@pytest.mark.property
def test_thousands_of_hires_no_ceiling_no_dupes_gapless() -> None:
    # Combinatorial/scale: 2000 distinct hires must produce 2000 (+root) live caps,
    # no duplicate id, and a gapless 2001-event verified chain — no ceiling.
    n = 2000
    rec = founded_recording_org(CEO)
    for i in range(n):
        kw = _VOCAB[i % len(_VOCAB)]
        rec = rec.hire(report_charter(f"role-{i:05d}", (f"own {kw} domain {i}",)))
    descriptors = rec.live_registry().descriptors()
    ids = [str(d.capability_id) for d in descriptors]
    assert len(ids) == n + 1  # all hires + the root
    assert len(set(ids)) == len(ids)  # no duplicate capability_id
    events = rec.growth_log.events()
    assert [e.seq for e in events] == list(range(n + 1))  # gapless to n+1
    assert rec.growth_log.verify() is True  # the 2001-link chain still verifies


@pytest.mark.property
def test_replay_does_exactly_one_fold_step_per_event_linear_in_n() -> None:
    # STRUCTURAL O(n) proof (deterministic, not wall-clock): replay applies the fold
    # step exactly ONCE per event, so its work is exactly linear in the event count.
    # A quadratic replay (re-scanning history per event) would call _apply O(n^2)
    # times; counting the calls proves linearity without a flaky timing budget.
    rec = founded_recording_org(CEO)
    for i in range(400):
        rec = rec.hire(report_charter(f"r-{i:05d}", (f"own {_VOCAB[i % len(_VOCAB)]} domain {i}",)))
    events = rec.growth_log.events()

    def _fold_calls(prefix_len: int) -> int:
        prefix = CapabilityGrowthLog(events[:prefix_len])
        calls = 0
        original = LiveCapabilityRegistry._apply

        def _counting(current, event):  # type: ignore[no-untyped-def]
            nonlocal calls
            calls += 1
            return original(current, event)

        LiveCapabilityRegistry._apply = staticmethod(_counting)  # type: ignore[method-assign]
        try:
            LiveCapabilityRegistry.from_growth_log(prefix)
        finally:
            LiveCapabilityRegistry._apply = original  # type: ignore[method-assign]
        return calls

    # Exactly one fold step per event at both sizes -> work is linear in n. Doubling
    # the events exactly doubles the steps (the signature of O(n), never O(n^2)).
    assert _fold_calls(200) == 200
    assert _fold_calls(400) == 400
