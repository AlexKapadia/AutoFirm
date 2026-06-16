"""Per-conversation FIFO ordering tracker (causal-seq monotonicity).

What this does
--------------
Enforces per-conversation ordering: within a single ``conversation_id`` the bus
delivers messages in non-decreasing ``causal_seq`` order. The tracker remembers
the highest sequence already *accepted* per conversation and rejects an envelope
whose sequence is strictly lower (a stale / out-of-order message), which the bus
then dead-letters with an ``ORDERING_VIOLATION`` reason.

Why it exists / where it sits
-----------------------------
The A2 guarantee includes "per-conversation ordering". We scope ordering to a
conversation (not a global total order) because a global order would serialise
all org traffic and is not what the synthesis requires -- conversations are the
unit of causal exchange. A duplicate sequence (==) is allowed through to the
dedup store, which suppresses it by key; only a STRICTLY-lower sequence is an
ordering violation.

Security / compliance invariants upheld
---------------------------------------
* **Fail-closed on out-of-order (§5.6):** a strictly-decreasing causal_seq is
  REFUSED (dead-lettered), never silently delivered out of order, so a replayed
  or reordered stale message cannot corrupt a conversation's causal history.
* **Determinism (§3.11):** acceptance depends only on the recorded high-water
  mark and the envelope's sequence -- no clock, no nondeterminism.
"""

from __future__ import annotations

__all__ = ["ConversationOrderingTracker"]


class ConversationOrderingTracker:
    """Tracks the highest accepted causal_seq per conversation (single-writer)."""

    def __init__(self) -> None:
        """Create a tracker with no conversations seen yet."""
        # conversation_id -> highest causal_seq accepted so far for it.
        self._high_water: dict[str, int] = {}

    def accept(self, conversation_id: str, causal_seq: int) -> bool:
        """Return True and advance the high-water mark if in order, else False.

        A sequence >= the recorded high-water mark is in order: we accept it and
        bump the mark (a duplicate == sequence keeps the mark, leaving the dedup
        store to suppress it). A sequence strictly BELOW the mark is out of order
        and rejected (fail-closed) -- the caller dead-letters it.
        """
        current = self._high_water.get(conversation_id)
        if current is not None and causal_seq < current:
            # fail-closed: strictly-decreasing sequence is a stale/reordered
            # message; refuse it rather than deliver out of causal order.
            return False
        # In order (first message, equal, or greater): the guard above already
        # rejected anything strictly below the mark, so here causal_seq >= current
        # always holds and the new high-water is exactly causal_seq.
        self._high_water[conversation_id] = causal_seq
        return True

    def high_water(self, conversation_id: str) -> int | None:
        """Return the highest accepted sequence for a conversation, or None."""
        return self._high_water.get(conversation_id)
