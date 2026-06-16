"""Append-only audit sink for every routed message (A2 top priority; A6 hook).

What this does
--------------
Defines the :class:`MessageAuditSink` protocol -- the append-only interface the
bus calls to record EVERY message it routes (delivered, suppressed, or
dead-lettered) -- and an in-memory :class:`InMemoryMessageAuditSink` reference
implementation. Each entry captures the dedup key, conversation, sender,
resolved destination, performative, outcome, and the injected timestamp.

Why it exists / where it sits
-----------------------------
"Every message routed is recorded in an append-only audit trail" is the A2 top
priority. This is deliberately a *simple append-only interface now*; it is the
seam that will later wire to the RFC 6962 Merkle audit log in
``src/autofirm/audit/`` (``audit_record_contract.py`` / ``candidate_b_merkle_audit_log``)
-- the bus depends only on the protocol, so swapping the in-memory sink for the
tamper-evident Merkle log is a composition-root change, not a bus change.

Security / compliance invariants upheld
---------------------------------------
* **Append-only (§5.6):** the interface exposes only ``record`` + read; no
  update/delete. The in-memory impl appends to a list it never rewrites.
* **Audit-before-or-with-decision:** the bus records an entry for every routing
  decision, including fail-closed denials (dead-letters) -- the log proves what
  the system did, not just its successes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from autofirm.comms.delivery_outcome_types import DeadLetterReason, DeliveryStatus
from autofirm.comms.message_envelope_contract import Performative

__all__ = [
    "InMemoryMessageAuditSink",
    "MessageAuditEntry",
    "MessageAuditSink",
]


@dataclass(frozen=True, slots=True)
class MessageAuditEntry:
    """One immutable audit row for a routed message (append-only).

    ``destination`` is the resolved directed recipient OR ``topic:<name>`` so the
    trail shows exactly where the message went. ``dead_letter_reason`` is set IFF
    the outcome was a dead-letter -- the explain-every-decision record (§3.11).
    """

    dedup_key: str
    conversation_id: str
    sender: str
    destination: str
    performative: Performative
    status: DeliveryStatus
    recipients_notified: int
    timestamp: datetime
    dead_letter_reason: DeadLetterReason | None = None


class MessageAuditSink(Protocol):
    """Append-only audit interface the bus records every routed message into.

    Implementations MUST be append-only (no update/delete). This is the seam to
    the RFC 6962 Merkle audit log; the bus knows only this protocol.
    """

    def record(self, entry: MessageAuditEntry) -> None:
        """Append one audit entry (must never mutate prior entries)."""
        ...


class InMemoryMessageAuditSink:
    """Reference append-only sink backed by an in-memory list.

    Suitable for tests and a single-process deployment; the production wiring
    replaces it with the Merkle-tree-backed sink (A6) behind the same protocol.
    """

    def __init__(self) -> None:
        """Create an empty append-only audit log."""
        self._entries: list[MessageAuditEntry] = []

    def record(self, entry: MessageAuditEntry) -> None:
        """Append ``entry``; the existing log is never rewritten (append-only)."""
        self._entries.append(entry)

    def entries(self) -> tuple[MessageAuditEntry, ...]:
        """Return the full append-only trail as an immutable snapshot."""
        return tuple(self._entries)

    def __len__(self) -> int:
        """Number of audit entries recorded so far."""
        return len(self._entries)
