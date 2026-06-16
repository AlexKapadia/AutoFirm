"""The front-door provenance trail: append-only record of every human request's journey.

What this does
--------------
Defines :class:`FrontDoorProvenanceEntry` — one immutable row capturing how a single
human request was handled (who asked, the routing outcome, which role handled it, why,
how the internal delivery resolved, and when) — the :class:`FrontDoorProvenanceTrail`
append-only Protocol the dispatcher records into, and :class:`InMemoryFrontDoorProvenanceTrail`,
an in-memory reference implementation. This is the human-facing audit surface, distinct
from (and complementary to) the comms bus's own per-message audit.

Why it exists / where it sits
-----------------------------
The front door must be "auditable end-to-end" — a human (or an auditor) can ask "what
happened to my request?" and get a complete, provenance-bearing answer: which role,
when, why it was routed there, and whether the internal delivery succeeded. The bus
audits the *internal message*; this trail audits the *human interaction* that produced
it, joined by the correlation id. It is deliberately a simple append-only interface now,
the seam that later wires to the RFC 6962 Merkle audit log in ``src/autofirm/audit/``
(the dispatcher depends only on the Protocol, so swapping the in-memory trail for the
tamper-evident Merkle log is a composition-root change, not a dispatcher change).

Security / compliance invariants upheld
---------------------------------------
* **Append-only (CLAUDE.md §5.6):** the Protocol exposes only ``record`` + read; no
  update/delete. The in-memory impl appends to a list it never rewrites — a recorded
  provenance row is immutable.
* **Audit every decision, including fail-closed ones (§3.11):** the dispatcher records
  an entry for EVERY request — routed or triaged, delivered or dead-lettered — so the
  trail proves what the front door did, not only its successes.
* **No PII beyond the requester's own declared identity:** the entry carries the
  requester id/display name the request already declared and the request body the
  human sent; it introduces no new sensitive data.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from autofirm.comms.delivery_outcome_types import DeliveryStatus
from autofirm.frontdoor.routing_decision_contract import RoutingOutcome

__all__ = [
    "FrontDoorProvenanceEntry",
    "FrontDoorProvenanceTrail",
    "InMemoryFrontDoorProvenanceTrail",
]


@dataclass(frozen=True, slots=True)
class FrontDoorProvenanceEntry:
    """One immutable provenance row for a handled human request (append-only).

    Joins the human interaction to the internal delivery by ``correlation_id``.
    ``routing_outcome`` says whether the request reached a capable role or fell back to
    triage (and which cause); ``handler_role_id`` / ``handler_role_title`` name WHO
    handled it; ``routing_reason`` says WHY; ``delivery_status`` records how the internal
    bus delivery resolved (so a request routed correctly but whose handler errored is
    visible as such — never papered over).
    """

    correlation_id: str  # threads back to the originating HumanRequest
    requester_id: str  # WHO asked
    requester_display_name: str  # human-readable requester name
    routing_outcome: RoutingOutcome  # routed-to-capable / triaged-no-capable / triaged-no-permitted
    handler_role_id: str  # WHICH role handled it (capable role OR triage — never empty)
    handler_role_title: str  # the handler's human-readable title
    routing_reason: str  # WHY it was routed there (explain-every-decision)
    delivery_status: DeliveryStatus  # how the internal bus delivery resolved
    recorded_at: datetime  # WHEN (injected clock, never the wall clock)


class FrontDoorProvenanceTrail(Protocol):
    """Append-only interface the dispatcher records every request's provenance into.

    Implementations MUST be append-only (no update/delete). This is the seam to the
    RFC 6962 Merkle audit log; the dispatcher knows only this Protocol.
    """

    def record(self, entry: FrontDoorProvenanceEntry) -> None:
        """Append one provenance entry (must never mutate prior entries)."""
        ...


class InMemoryFrontDoorProvenanceTrail:
    """Reference append-only provenance trail backed by an in-memory list.

    Suitable for tests and a single-process deployment; production wiring replaces it
    with the Merkle-tree-backed sink (A6) behind the same Protocol.
    """

    def __init__(self) -> None:
        """Create an empty append-only provenance trail."""
        self._entries: list[FrontDoorProvenanceEntry] = []

    def record(self, entry: FrontDoorProvenanceEntry) -> None:
        """Append ``entry``; the existing trail is never rewritten (append-only)."""
        self._entries.append(entry)

    def entries(self) -> tuple[FrontDoorProvenanceEntry, ...]:
        """Return the full append-only trail as an immutable snapshot."""
        return tuple(self._entries)

    def __len__(self) -> int:
        """Number of provenance entries recorded so far."""
        return len(self._entries)
