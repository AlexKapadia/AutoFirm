"""Adversarial unit tests for the bus's collaborator components (A2).

Proves teeth (CLAUDE.md §3.6) on each small component in isolation: the dynamic
registry's runtime add/remove + total deregistration, the dedup store's
commit-after-success + FIFO bound, the ordering tracker's strict monotonicity, the
dead-letter queue's drain/peek, and the manual/system clocks. Boundary-exact +
property-based so a mutant on any guard is killed.
"""

from __future__ import annotations

from datetime import datetime

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from autofirm.comms.conversation_ordering_tracker import ConversationOrderingTracker
from autofirm.comms.dead_letter_queue import DeadLetterQueue
from autofirm.comms.delivery_outcome_types import DeadLetterReason
from autofirm.comms.dynamic_agent_registry import DynamicAgentRegistry
from autofirm.comms.idempotent_dedup_store import IdempotentDedupStore
from autofirm.comms.injectable_delivery_clock import ManualClock, SystemClock
from tests.comms.synthetic_comms_fixtures import RecordingHandler, make_envelope

# ----------------------------- Dynamic registry ---------------------------- #


def test_registry_resolves_registered_agent() -> None:
    reg = DynamicAgentRegistry()
    h = RecordingHandler()
    reg.register_agent("a", h)
    assert reg.resolve_directed("a") is h


def test_registry_unknown_recipient_resolves_to_none_fail_closed() -> None:
    reg = DynamicAgentRegistry()
    assert reg.resolve_directed("nobody") is None  # fail-closed signal


def test_registry_runtime_add_then_remove_changes_topology() -> None:
    reg = DynamicAgentRegistry()
    h = RecordingHandler()
    reg.register_agent("a", h)
    assert reg.resolve_directed("a") is h
    reg.deregister_agent("a")
    assert reg.resolve_directed("a") is None  # removed at runtime


def test_registry_reregister_replaces_handler() -> None:
    reg = DynamicAgentRegistry()
    old, new = RecordingHandler(), RecordingHandler()
    reg.register_agent("a", old)
    reg.register_agent("a", new)  # redeploy
    assert reg.resolve_directed("a") is new


def test_deregister_unsubscribes_from_every_topic_no_dangling() -> None:
    reg = DynamicAgentRegistry()
    h = RecordingHandler()
    reg.subscribe("t1", "a", h)
    reg.subscribe("t2", "a", h)
    reg.deregister_agent("a")
    # Total removal: gone from both topics, no dangling subscription leak.
    assert reg.resolve_topic("t1") == ()
    assert reg.resolve_topic("t2") == ()


def test_topic_fan_out_returns_all_current_subscribers() -> None:
    reg = DynamicAgentRegistry()
    a, b = RecordingHandler(), RecordingHandler()
    reg.subscribe("t", "a", a)
    reg.subscribe("t", "b", b)
    handlers = reg.resolve_topic("t")
    # Identity membership (handlers are mutable/unhashable dataclasses).
    assert len(handlers) == 2 and any(h is a for h in handlers) and any(h is b for h in handlers)


def test_unsubscribe_removes_one_subscriber_only() -> None:
    reg = DynamicAgentRegistry()
    a, b = RecordingHandler(), RecordingHandler()
    reg.subscribe("t", "a", a)
    reg.subscribe("t", "b", b)
    reg.unsubscribe("t", "a")
    assert reg.resolve_topic("t") == (b,)


def test_unsubscribe_unknown_topic_is_noop() -> None:
    reg = DynamicAgentRegistry()
    reg.unsubscribe("ghost-topic", "a")  # must not raise


def test_empty_topic_resolves_to_empty_tuple() -> None:
    reg = DynamicAgentRegistry()
    assert reg.resolve_topic("never-used") == ()


def test_register_empty_agent_id_is_refused() -> None:
    reg = DynamicAgentRegistry()
    with pytest.raises(ValueError, match="agent_id must be non-empty"):
        reg.register_agent("", RecordingHandler())


def test_subscribe_empty_topic_or_agent_is_refused() -> None:
    reg = DynamicAgentRegistry()
    with pytest.raises(ValueError, match="must be non-empty"):
        reg.subscribe("", "a", RecordingHandler())
    with pytest.raises(ValueError, match="must be non-empty"):
        reg.subscribe("t", "", RecordingHandler())


def test_deregister_unknown_agent_is_noop_idempotent() -> None:
    reg = DynamicAgentRegistry()
    reg.deregister_agent("never-existed")  # must not raise


# ------------------------------ Dedup store -------------------------------- #


def test_dedup_uncommitted_key_is_not_delivered() -> None:
    store = IdempotentDedupStore()
    assert store.already_delivered("k") is False


def test_dedup_committed_key_is_delivered() -> None:
    store = IdempotentDedupStore()
    store.commit("k")
    assert store.already_delivered("k") is True


def test_dedup_double_commit_is_idempotent() -> None:
    store = IdempotentDedupStore()
    store.commit("k")
    store.commit("k")  # no-op, no corruption
    assert len(store) == 1


def test_dedup_capacity_must_be_positive() -> None:
    with pytest.raises(ValueError, match="positive integer or None"):
        IdempotentDedupStore(capacity=0)
    with pytest.raises(ValueError, match="positive integer or None"):
        IdempotentDedupStore(capacity=-5)


def test_dedup_capacity_bound_evicts_oldest_fifo() -> None:
    store = IdempotentDedupStore(capacity=2)
    store.commit("k1")
    store.commit("k2")
    store.commit("k3")  # exceeds cap -> evicts k1 (oldest)
    assert len(store) == 2
    assert store.already_delivered("k1") is False  # evicted
    assert store.already_delivered("k2") is True
    assert store.already_delivered("k3") is True


def test_dedup_recommit_existing_key_does_not_evict() -> None:
    # Re-committing an existing key is a no-op and must NOT trigger eviction.
    store = IdempotentDedupStore(capacity=2)
    store.commit("k1")
    store.commit("k2")
    store.commit("k1")  # already present -> no-op
    assert len(store) == 2
    assert store.already_delivered("k1") is True
    assert store.already_delivered("k2") is True


@settings(max_examples=200)
@given(keys=st.lists(st.text(min_size=1, max_size=6), min_size=1, max_size=30))
def test_property_dedup_membership_matches_committed_set(keys: list[str]) -> None:
    store = IdempotentDedupStore()
    for k in keys:
        store.commit(k)
    # Property: a key is "delivered" IFF it was committed; len == distinct count.
    assert len(store) == len(set(keys))
    for k in set(keys):
        assert store.already_delivered(k) is True


# --------------------------- Ordering tracker ------------------------------ #


def test_ordering_first_message_accepted() -> None:
    t = ConversationOrderingTracker()
    assert t.accept("c", 0) is True
    assert t.high_water("c") == 0


def test_ordering_increasing_seq_accepted() -> None:
    t = ConversationOrderingTracker()
    assert t.accept("c", 0) is True
    assert t.accept("c", 5) is True
    assert t.high_water("c") == 5


def test_ordering_equal_seq_accepted_boundary() -> None:
    # Equal seq is in order (dedup, not ordering, suppresses re-sends).
    t = ConversationOrderingTracker()
    t.accept("c", 3)
    assert t.accept("c", 3) is True  # boundary: == high-water is accepted


def test_ordering_strictly_lower_seq_rejected_fail_closed() -> None:
    t = ConversationOrderingTracker()
    t.accept("c", 5)
    assert t.accept("c", 4) is False  # boundary: just-below is rejected
    assert t.high_water("c") == 5  # mark unchanged after a rejection


def test_ordering_is_per_conversation_independent() -> None:
    t = ConversationOrderingTracker()
    t.accept("cA", 10)
    # A low seq in a DIFFERENT conversation is still its first -> accepted.
    assert t.accept("cB", 0) is True


def test_ordering_unknown_conversation_high_water_is_none() -> None:
    t = ConversationOrderingTracker()
    assert t.high_water("never") is None


@settings(max_examples=200)
@given(seqs=st.lists(st.integers(min_value=0, max_value=50), min_size=1, max_size=30))
def test_property_ordering_high_water_is_running_max_of_accepted(seqs: list[int]) -> None:
    t = ConversationOrderingTracker()
    running_max = -1
    for seq in seqs:
        accepted = t.accept("c", seq)
        # Property: accepted IFF seq >= current running max; mark == running max.
        assert accepted == (seq >= running_max)
        if accepted:
            running_max = seq
        assert t.high_water("c") == running_max


# ------------------------------ Dead-letter -------------------------------- #


def test_dead_letter_add_then_peek_preserves_envelope_and_reason() -> None:
    dlq = DeadLetterQueue()
    env = make_envelope()
    dlq.add(env, DeadLetterReason.HANDLER_ERROR)
    entries = dlq.peek()
    assert len(entries) == 1
    assert entries[0].envelope is env
    assert entries[0].reason is DeadLetterReason.HANDLER_ERROR


def test_dead_letter_drain_returns_all_then_clears() -> None:
    dlq = DeadLetterQueue()
    dlq.add(make_envelope(dedup_key="d1"), DeadLetterReason.UNKNOWN_RECIPIENT)
    dlq.add(make_envelope(dedup_key="d2"), DeadLetterReason.ORDERING_VIOLATION)
    drained = dlq.drain()
    assert len(drained) == 2
    assert len(dlq) == 0  # drained -> empty
    assert dlq.peek() == ()


def test_dead_letter_peek_does_not_clear() -> None:
    dlq = DeadLetterQueue()
    dlq.add(make_envelope(), DeadLetterReason.HANDLER_ERROR)
    dlq.peek()
    assert len(dlq) == 1  # peek is read-only


# --------------------------------- Clocks ---------------------------------- #


def test_manual_clock_is_frozen_until_tick() -> None:
    clk = ManualClock()
    t0 = clk.now()
    assert clk.now() == t0  # frozen
    t1 = clk.tick(10.0)
    assert t1 > t0
    assert clk.now() == t1


def test_manual_clock_normalises_naive_start_to_utc() -> None:
    clk = ManualClock(start=datetime(2030, 6, 1))  # naive
    assert clk.now().tzinfo is not None  # normalised to UTC


def test_system_clock_returns_timezone_aware_utc() -> None:
    assert SystemClock().now().tzinfo is not None
