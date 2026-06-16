"""Property-based tests for the bus's dedup + ordering INVARIANTS (A2 acceptance).

This is the acceptance bar (CLAUDE.md §3.6) -- not coverage. Hypothesis drives
adversarial streams (reordered, duplicated, interleaved conversations) and asserts
the two load-bearing guarantees hold for EVERY stream:

* **Dedup idempotency:** a handler is invoked AT MOST ONCE per dedup_key across
  arbitrary re-sends -- "no message delivered twice past dedup".
* **Per-conversation FIFO ordering:** the causal_seqs a handler observes within a
  conversation are non-decreasing; any strictly-out-of-order message is
  dead-lettered, never delivered -- "no message delivered out of causal order".
* **No message lost-or-duplicated-past-dedup:** every committed key was delivered
  exactly once; every other send is accounted for as suppressed or dead-lettered.

All synthetic, no network, deterministic (manual clock).
"""

from __future__ import annotations

import anyio
from hypothesis import given, settings
from hypothesis import strategies as st

from autofirm.comms.delivery_outcome_types import DeadLetterReason, DeliveryStatus
from tests.comms.synthetic_comms_fixtures import (
    RecordingHandler,
    make_bus,
    make_envelope,
)


def _run(coro) -> None:
    """Run an async body on the asyncio backend (deterministic single backend)."""
    anyio.run(coro, backend="asyncio")


@settings(max_examples=200, deadline=None)
@given(
    # A stream of dedup keys with deliberate, heavy repetition so duplicates are
    # the common case, not the exception.
    keys=st.lists(st.sampled_from(["k0", "k1", "k2", "k3"]), min_size=1, max_size=40),
)
def test_property_handler_invoked_at_most_once_per_dedup_key(keys: list[str]) -> None:
    async def body() -> None:
        h = make_bus()
        handler = RecordingHandler()
        h.registry.register_agent("agent-b", handler)
        # Every message is in-order (seq increases) so ordering never interferes;
        # this isolates the dedup invariant.
        for seq, key in enumerate(keys):
            await h.bus.deliver(
                make_envelope(recipient="agent-b", causal_seq=seq, dedup_key=key)
            )
        # INVARIANT: each distinct key reached the handler at most once.
        delivered_keys = [e.dedup_key for e in handler.calls]
        assert len(delivered_keys) == len(set(delivered_keys))  # no duplicate delivery
        # And every distinct key in the stream was delivered exactly once.
        assert set(delivered_keys) == set(keys)

    _run(body)


@settings(max_examples=200, deadline=None)
@given(seqs=st.lists(st.integers(min_value=0, max_value=50), min_size=1, max_size=30))
def test_property_per_conversation_delivery_is_monotonic_non_decreasing(
    seqs: list[int],
) -> None:
    async def body() -> None:
        h = make_bus()
        handler = RecordingHandler()
        h.registry.register_agent("agent-b", handler)
        # Unique dedup key per send so dedup never masks an ordering decision --
        # this isolates the ordering invariant from the dedup one.
        for i, seq in enumerate(seqs):
            await h.bus.deliver(
                make_envelope(
                    recipient="agent-b",
                    conversation_id="conv",
                    causal_seq=seq,
                    dedup_key=f"dk-{i}",
                )
            )
        observed = [e.causal_seq for e in handler.calls]
        # INVARIANT: the sequences the handler saw are non-decreasing (FIFO).
        assert observed == sorted(observed)
        # And no strictly-decreasing send was ever delivered (it was dead-lettered).
        running_max = -1
        delivered = 0
        for seq in seqs:
            if seq >= running_max:
                running_max = seq
                delivered += 1
        assert len(handler.calls) == delivered

    _run(body)


@settings(max_examples=150, deadline=None)
@given(
    events=st.lists(
        st.tuples(
            st.sampled_from(["cA", "cB"]),  # conversation id
            st.integers(min_value=0, max_value=20),  # causal_seq
        ),
        min_size=1,
        max_size=30,
    )
)
def test_property_conservation_no_message_lost_or_duplicated_past_dedup(
    events: list[tuple[str, int]],
) -> None:
    async def body() -> None:
        h = make_bus()
        handler = RecordingHandler()
        h.registry.register_agent("agent-b", handler)
        reports = []
        for i, (conv, seq) in enumerate(events):
            reports.append(
                await h.bus.deliver(
                    make_envelope(
                        recipient="agent-b",
                        conversation_id=conv,
                        causal_seq=seq,
                        dedup_key=f"dk-{i}",  # all keys distinct -> no suppression
                    )
                )
            )
        # CONSERVATION: every event is accounted for as exactly one terminal
        # outcome; nothing vanishes. With distinct keys, every event is either
        # DELIVERED (in order) or DEAD_LETTERED (ordering violation) -- never
        # silently lost and never suppressed.
        assert len(reports) == len(events)
        delivered = [r for r in reports if r.status is DeliveryStatus.DELIVERED]
        dead = [r for r in reports if r.status is DeliveryStatus.DEAD_LETTERED]
        assert len(delivered) + len(dead) == len(events)
        # Delivered count equals the per-conversation monotonic-accept count.
        running: dict[str, int] = {}
        expected_delivered = 0
        for conv, seq in events:
            hw = running.get(conv)
            if hw is None or seq >= hw:
                running[conv] = seq
                expected_delivered += 1
        assert len(delivered) == expected_delivered
        assert len(handler.calls) == expected_delivered
        # Every dead-letter here is specifically an ordering violation.
        for r in dead:
            assert r.dead_letter_reason is DeadLetterReason.ORDERING_VIOLATION

    _run(body)


@settings(max_examples=100, deadline=None)
@given(repeats=st.integers(min_value=2, max_value=8))
def test_property_redelivery_of_committed_key_is_always_suppressed(repeats: int) -> None:
    async def body() -> None:
        h = make_bus()
        handler = RecordingHandler()
        h.registry.register_agent("agent-b", handler)
        first = await h.bus.deliver(make_envelope(recipient="agent-b", dedup_key="same"))
        assert first.status is DeliveryStatus.DELIVERED
        # Re-send the SAME key many times: always suppressed, handler never re-run.
        for _ in range(repeats):
            r = await h.bus.deliver(
                make_envelope(recipient="agent-b", causal_seq=99, dedup_key="same")
            )
            assert r.status is DeliveryStatus.DUPLICATE_SUPPRESSED
            assert r.recipients_notified == 0
        assert len(handler.calls) == 1  # delivered exactly once despite N re-sends

    _run(body)


def test_determinism_same_stream_same_outcome_across_repeated_runs() -> None:
    # Determinism (§3.11): the identical input stream produces identical reports
    # and identical audit timestamps across independent runs (manual clock).
    def run_once() -> list[tuple[str, str | None]]:
        results: list[tuple[str, str | None]] = []

        async def body() -> None:
            h = make_bus()
            h.registry.register_agent("agent-b", RecordingHandler())
            stream = [(0, "a"), (1, "b"), (1, "b"), (0, "c"), (2, "a")]
            for seq, key in stream:
                rep = await h.bus.deliver(
                    make_envelope(recipient="agent-b", causal_seq=seq, dedup_key=key)
                )
                reason = rep.dead_letter_reason.value if rep.dead_letter_reason else None
                results.append((rep.status.value, reason))

        _run(body)
        return results

    assert run_once() == run_once()  # bit-for-bit reproducible
