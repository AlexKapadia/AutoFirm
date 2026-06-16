"""Dead-letter queue: the fail-closed sink for undeliverable messages.

What this does
--------------
Captures any envelope the bus could not deliver or process, paired with a named
:class:`DeadLetterReason`, in an append-only in-memory queue. A message is NEVER
silently dropped -- if routing fails for any reason it lands here, observable and
re-drainable by an operator.

Why it exists / where it sits
-----------------------------
"Unknown recipient -> fail-closed to dead-letter, never silently dropped" is a
hard A2 requirement. Isolating the dead-letter sink behind one small class keeps
the bus focused and gives operations a single place to inspect / replay failures.

Security / compliance invariants upheld
---------------------------------------
* **No silent drops (§5.6):** every dead-letter carries the original envelope +
  the explicit reason, so the fail-closed path is fully auditable and explainable.
* **Append-only:** entries are only ever appended and drained, never rewritten,
  mirroring the audit-log append-only invariant.
"""

from __future__ import annotations

from dataclasses import dataclass

from autofirm.comms.delivery_outcome_types import DeadLetterReason
from autofirm.comms.message_envelope_contract import MessageEnvelope

__all__ = ["DeadLetter", "DeadLetterQueue"]


@dataclass(frozen=True, slots=True)
class DeadLetter:
    """One undeliverable message + the named reason it failed (immutable)."""

    envelope: MessageEnvelope
    reason: DeadLetterReason


class DeadLetterQueue:
    """Append-only in-memory dead-letter sink (single-writer per bus instance)."""

    def __init__(self) -> None:
        """Create an empty dead-letter queue."""
        self._entries: list[DeadLetter] = []

    def add(self, envelope: MessageEnvelope, reason: DeadLetterReason) -> None:
        """Append an undeliverable ``envelope`` with its ``reason`` (append-only)."""
        self._entries.append(DeadLetter(envelope=envelope, reason=reason))

    def drain(self) -> tuple[DeadLetter, ...]:
        """Return all dead-letters and clear the queue (operator replay path).

        Returns a snapshot tuple BEFORE clearing so a concurrent reader can never
        observe a half-drained queue.
        """
        snapshot = tuple(self._entries)
        self._entries = []
        return snapshot

    def peek(self) -> tuple[DeadLetter, ...]:
        """Return all current dead-letters WITHOUT clearing (read-only inspect)."""
        return tuple(self._entries)

    def __len__(self) -> int:
        """Number of dead-letters currently held."""
        return len(self._entries)
