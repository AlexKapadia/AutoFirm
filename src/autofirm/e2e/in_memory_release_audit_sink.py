"""An append-only, in-memory ReleaseAuditSink for the e2e delivery gate.

What this does
--------------
Implements :class:`InMemoryReleaseAuditSink`, a concrete
:class:`~autofirm.output_review.release_decision_gate.ReleaseAuditSink` the e2e
delivery gate writes every release decision through. Each :meth:`record` call
appends one immutable :class:`ReleaseAuditEntry` (artifact ref, outcome, reason,
decided-at) to an append-only list; :meth:`entries` returns a read-only snapshot
so the validation can prove an authorised release AND a denial were both audited.

Why it exists / where it sits
-----------------------------
The release gate fails closed if its audit write raises, so a real (non-raising)
sink is what lets an authorised release actually escape. The e2e validation has no
persistent log to attach to, so it uses this in-memory append-only sink: it is the
minimum honest sink — it really stores every decision and exposes no update/delete,
so the audit trail is tamper-evident by construction (CLAUDE.md §5.6).

Security / compliance invariants upheld (CLAUDE.md §5.6, §3.11)
--------------------------------------------------------------
* **Append-only:** ``record`` only ever appends; the class exposes no way to mutate
  or remove a stored entry, so the trail cannot be silently rewritten.
* **Both outcomes logged:** a SUCCESS (authorised) and a DENY (blocked) are stored
  identically — a denial is recorded, never dropped.
* **Snapshot isolation:** :meth:`entries` returns a fresh tuple, so a caller cannot
  reach into and mutate the internal append-only list.
* **No PII:** stores the opaque artifact ref and a human reason only, never content.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from autofirm.audit.audit_record_contract import AuditOutcome

__all__ = ["InMemoryReleaseAuditSink", "ReleaseAuditEntry"]


@dataclass(frozen=True, slots=True)
class ReleaseAuditEntry:
    """One immutable record of a release decision the sink audited.

    Frozen so a stored entry is a permanent fact about the trail (it cannot be
    edited after the fact), preserving the append-only guarantee.

    Args:
        artifact_ref: The opaque identity of the artifact the decision was over.
        outcome: ``SUCCESS`` for an authorised release, ``DENY`` for a blocked one.
        reason: The human-readable justification the decision carried.
        decided_at: The injected timestamp the decision was stamped with.
    """

    artifact_ref: str
    outcome: AuditOutcome
    reason: str
    decided_at: datetime


class InMemoryReleaseAuditSink:
    """Append-only in-memory sink satisfying the ``ReleaseAuditSink`` Protocol."""

    def __init__(self) -> None:
        """Start with an empty append-only entry list."""
        # Append-only: only ``record`` ever appends; nothing mutates or removes.
        self._entries: list[ReleaseAuditEntry] = []

    def record(
        self,
        *,
        artifact_ref: str,
        outcome: AuditOutcome,
        reason: str,
        decided_at: datetime,
    ) -> None:
        """Append one release-decision audit entry (append-only; never updates).

        Args:
            artifact_ref: The artifact the decision was over.
            outcome: ``SUCCESS`` (authorised) or ``DENY`` (blocked).
            reason: The decision's human-readable justification.
            decided_at: The injected timestamp on the decision.
        """
        self._entries.append(
            ReleaseAuditEntry(
                artifact_ref=artifact_ref,
                outcome=outcome,
                reason=reason,
                decided_at=decided_at,
            )
        )

    def entries(self) -> tuple[ReleaseAuditEntry, ...]:
        """Return every audited entry in decision order (a read-only snapshot)."""
        # Tuple copy so a caller can never mutate the append-only backing list.
        return tuple(self._entries)
