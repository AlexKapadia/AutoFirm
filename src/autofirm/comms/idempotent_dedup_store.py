"""Idempotent dedup store: turns at-least-once into effective at-most-once.

What this does
--------------
Tracks which ``dedup_key`` values have already been *committed* (successfully
delivered). The bus consults :meth:`already_delivered` before invoking handlers
and calls :meth:`commit` only AFTER a delivery succeeds, so a re-sent envelope
(at-least-once retry) is suppressed -- the delivery becomes effective
at-most-once per key.

Why it exists / where it sits
-----------------------------
At-least-once transports can re-deliver. Per the A2 reliability requirement we
add idempotent dedup so a handler is not driven twice for the same logical
message. The store is the single source of truth for "have we already committed
this key?" -- mirroring the saga replay log's ``already_applied`` idempotency
defence, but for the comms plane.

Security / compliance invariants upheld
---------------------------------------
* **Commit-after-success ordering (the dedup contract):** the key is recorded
  only after the handler returns without raising. If the handler fails, the key
  is NOT committed, so a retry can legitimately re-attempt delivery -- and that
  retry is what makes the guarantee at-LEAST-once, never silently-dropped.
* **Bounded growth:** an optional capacity cap evicts the oldest keys FIFO so an
  unbounded key stream cannot exhaust memory (resource-exhaustion defence, §5.6).
"""

from __future__ import annotations

from collections import OrderedDict

__all__ = ["IdempotentDedupStore"]


class IdempotentDedupStore:
    """In-memory committed-key set with optional FIFO capacity bound.

    Not thread-safe by itself: the bus serialises access within a single AnyIO
    task scope, so committed-key reads/writes never interleave (the comms core is
    single-writer per bus instance by construction).
    """

    def __init__(self, capacity: int | None = None) -> None:
        """Create the store, optionally bounding it to ``capacity`` keys.

        ``capacity`` must be positive if given; a non-positive cap is a
        configuration error and is refused (fail-closed) rather than silently
        treated as unbounded.
        """
        if capacity is not None and capacity <= 0:
            raise ValueError("capacity must be a positive integer or None")
        self._capacity = capacity
        # OrderedDict gives O(1) membership + O(1) oldest-eviction for the bound.
        self._committed: OrderedDict[str, None] = OrderedDict()

    def already_delivered(self, dedup_key: str) -> bool:
        """Return True if ``dedup_key`` was already committed (=> suppress)."""
        return dedup_key in self._committed

    def commit(self, dedup_key: str) -> None:
        """Record ``dedup_key`` as delivered. Called AFTER a successful handler.

        Re-committing an existing key is a no-op (idempotent), so a double-commit
        cannot corrupt the set. When a capacity bound is set, the oldest key is
        evicted FIFO once the cap is exceeded.
        """
        if dedup_key in self._committed:
            return  # idempotent: already committed, nothing to do
        self._committed[dedup_key] = None
        if self._capacity is not None and len(self._committed) > self._capacity:
            # Evict the oldest committed key (FIFO) to respect the bound. A future
            # re-send of an evicted key would re-deliver -- acceptable under the
            # explicit at-least-once contract, and bounded memory is the priority.
            self._committed.popitem(last=False)

    def __len__(self) -> int:
        """Number of currently-committed keys (for tests / observability)."""
        return len(self._committed)
