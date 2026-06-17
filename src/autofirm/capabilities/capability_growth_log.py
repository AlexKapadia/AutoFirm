"""The append-only, RFC-6962 hash-chained, gapless capability growth log.

What this does
--------------
Defines :class:`CapabilityGrowthLog` — an immutable, append-only sequence of
:class:`CapabilityRegistryEvent` records that is the SOURCE OF TRUTH for how the
org's capability set evolved. It enforces three invariants on every append
(fail-closed): the new event's ``seq`` is exactly the next position (gapless,
no reorder/insert/delete), its ``prev_hash`` equals the previous event's
``record_hash`` (the chain is unbroken), and the whole chain re-verifies. It also
provides :meth:`seal` — the single place that computes an event's hashes from the
log's current tip — and :meth:`verify`, the fail-closed full-chain check.

Why it exists / where it sits
-----------------------------
Per ``docs/architecture/data-contracts.md`` §9 and the B4 research, the growth log
is what lets the platform *show its evolution* and prove the showcase was not
edited after the fact. It sits above the event contract and below the live
registry: :mod:`live_capability_registry` derives the CURRENT set by a PURE replay
of this log, so the current capabilities can never drift from the recorded history.

Security / compliance invariants upheld
---------------------------------------
* **Append-only (CLAUDE.md §5.6 / §3.8):** :meth:`append` returns a NEW log; there
  is no update or delete path. An out-of-order, duplicate, or gapped ``seq`` is
  refused, so history can never be rewritten.
* **Tamper-evident chain (RFC-6962, fail-closed):** an appended event whose
  ``prev_hash`` does not match the current tip is refused; :meth:`verify` re-walks
  the whole chain and refuses on the first broken link — a reorder/insert/delete/
  edit anywhere is detected.
* **Verification-before-trust (fail-closed):** the live registry MUST call
  :meth:`verify` before replaying; an unverifiable log is refused (never replayed
  optimistically), so a corrupted log fails closed rather than serving stale or
  forged capabilities.
* **Pure replay:** the log is the only input the current set is derived from
  (apart from live org clearances), so the derivation is a deterministic fold.
"""

from __future__ import annotations

from datetime import datetime

from autofirm.capabilities.capability_descriptor import CapabilityDescriptor
from autofirm.capabilities.capability_registry_event import (
    GENESIS_PREV_HASH,
    CapabilityRegistryEvent,
    RegistryEventKind,
    compute_record_hash,
)
from autofirm.org.org_identifiers import RoleId

__all__ = ["CapabilityGrowthLog", "GrowthLogError"]


class GrowthLogError(Exception):
    """Raised when an append or verification would violate a growth-log invariant."""


class CapabilityGrowthLog:
    """An immutable, append-only, hash-chained log of capability-growth events.

    Built empty and grown via :meth:`seal` + :meth:`append`. Every mutator returns
    a NEW log; the underlying tuple is never edited in place, so any sequence of
    appends is a pure, replayable, tamper-evident fold.
    """

    __slots__ = ("_events",)

    def __init__(self, events: tuple[CapabilityRegistryEvent, ...] = ()) -> None:
        """Wrap ``events`` and fully verify the chain (fail-closed at construction).

        A log can only be observed if its chain verifies end to end, so a tampered
        tuple can never be wrapped and trusted.
        """
        self._events = events
        self._verify_or_refuse()  # fail-closed: refuse to hold an unverifiable chain

    @property
    def tip_hash(self) -> bytes:
        """The ``record_hash`` of the last event, or the genesis anchor if empty.

        This is the ``prev_hash`` the next sealed event must chain over, so a caller
        never has to reach into the event list to extend the chain correctly.
        """
        return self._events[-1].record_hash if self._events else GENESIS_PREV_HASH

    @property
    def next_seq(self) -> int:
        """The ``seq`` the next appended event must carry (== current length)."""
        return len(self._events)

    def events(self) -> tuple[CapabilityRegistryEvent, ...]:
        """The ordered tuple of growth events (the full recorded evolution)."""
        return self._events

    def seal(  # noqa: PLR0913 -- a growth event is intrinsically wide; every field
        # is a distinct, required, keyword-only input (no grab-bag dict).
        self,
        *,
        kind: RegistryEventKind,
        descriptor: CapabilityDescriptor,
        triggered_by: RoleId,
        org_event_ref: int,
        rationale: str,
        occurred_at: datetime,
    ) -> CapabilityRegistryEvent:
        """Build the next chained event from this log's tip (the single hash writer).

        Assigns the gapless ``seq`` and chains ``prev_hash`` to :attr:`tip_hash`,
        then computes the ``record_hash`` over the canonical content — so callers
        never compute or pass hashes themselves (one place owns chaining, §5.7).
        """
        seq = self.next_seq
        prev_hash = self.tip_hash
        record_hash = compute_record_hash(
            seq=seq,
            kind=kind,
            descriptor=descriptor,
            triggered_by=triggered_by,
            org_event_ref=org_event_ref,
            rationale=rationale,
            occurred_at=occurred_at,
            prev_hash=prev_hash,
        )
        return CapabilityRegistryEvent(
            seq=seq,
            kind=kind,
            descriptor=descriptor,
            triggered_by=triggered_by,
            org_event_ref=org_event_ref,
            rationale=rationale,
            occurred_at=occurred_at,
            prev_hash=prev_hash,
            record_hash=record_hash,
        )

    def append(self, event: CapabilityRegistryEvent) -> CapabilityGrowthLog:
        """Return a NEW log with ``event`` appended (append-only, fail-closed).

        Refuses (does not append) if the event's ``seq`` is not exactly the next
        position (a gap, duplicate, or reorder) or its ``prev_hash`` does not match
        the current tip (a broken chain link) — so the log can never be rewritten,
        reordered, or have an event spliced in (§5.6).
        """
        if event.seq != self.next_seq:
            # fail-closed: a non-consecutive seq is a gap/duplicate/reorder attempt.
            raise GrowthLogError(
                f"non-consecutive seq: expected {self.next_seq}, got {event.seq}"
            )
        if event.prev_hash != self.tip_hash:
            # fail-closed: a prev_hash that does not match the tip breaks the chain
            # (an insert or a forged predecessor) — refuse rather than chain over it.
            raise GrowthLogError("event prev_hash does not match the log tip (broken chain)")
        return CapabilityGrowthLog((*self._events, event))

    def verify(self) -> bool:
        """Re-walk the whole chain; True iff every link and seq is intact.

        Independent of construction so a caller can re-verify a log it was handed
        (verification-before-trust). Checks each event's ``seq`` is its position,
        its ``prev_hash`` chains the predecessor (genesis for the first), and its
        ``record_hash`` re-derives from its canonical content.
        """
        expected_prev = GENESIS_PREV_HASH
        for position, event in enumerate(self._events):
            if event.seq != position:
                return False  # a gap/reorder: seq must equal position
            if event.prev_hash != expected_prev:
                return False  # a broken/forged chain link
            recomputed = compute_record_hash(
                seq=event.seq,
                kind=event.kind,
                descriptor=event.descriptor,
                triggered_by=event.triggered_by,
                org_event_ref=event.org_event_ref,
                rationale=event.rationale,
                occurred_at=event.occurred_at,
                prev_hash=event.prev_hash,
            )
            if recomputed != event.record_hash:
                return False  # the stored hash does not match the content (edited)
            expected_prev = event.record_hash
        return True

    def _verify_or_refuse(self) -> None:
        """Raise if the chain does not verify (fail-closed construction guard)."""
        if not self.verify():
            # fail-closed: a log whose chain is broken must never be observed or
            # replayed — refuse to construct it rather than serve forged history.
            raise GrowthLogError("growth log chain failed verification (tamper detected)")
