"""Bi-temporal knowledge-graph backend Protocol + deterministic in-memory fake (W2/B2).

What this does
--------------
Defines :class:`KnowledgeGraphBackend`, the Protocol seam the shared-knowledge
plane depends on (write / as-of-time query / invalidate), plus
:class:`InMemoryBitemporalKnowledgeGraph`, a fully in-memory, network-free,
deterministic bi-temporal fake that the core runs against with NO external graph
DB. A real graph DB (Neo4j/FalkorDB) is an OPT-IN adapter behind the SAME Protocol
-- the deterministic core never imports a graph service directly.

The fake is **append-only**: an entry is never physically deleted. Invalidation
stamps ``superseded_at`` on the prior transaction record and (optionally) writes a
successor; an as-of-time query reconstructs exactly the set of entries the store
knew AND that were event-valid at the requested instant. This is the Zep/Graphiti
bi-temporal model (folder 01) mapped onto AutoFirm's existing append-only pattern.

Why it exists / where it sits
------------------------------
Per ``docs/research/B2-shared-knowledge-graph/golden-set-and-metric.md`` the
chosen backend is a single bi-temporal graph store with an in-memory fake (the
bake-off favourite, Candidate A) accessed via LOCAL/entity-anchored retrieval. The
Protocol keeps the real DB optional; the in-memory fake keeps unit tests free of
any external service (CLAUDE.md §5.5 "no network in unit tests").

Security / compliance invariants upheld
---------------------------------------
* **As-of-time correctness is exact (§3.11):** a query at instant ``T`` NEVER
  returns a fact recorded after ``T`` nor one whose event-validity excludes ``T``;
  the reconstruction is deterministic and ordered.
* **Append-only, no physical delete (§3.8):** invalidation is logical
  (``superseded_at``), so history/audit always survives -- a stale fact stops being
  live without being erased.
* **Fail closed (§5.6):** writing a duplicate live id, or invalidating an unknown /
  already-superseded id, is REFUSED with a typed error rather than silently no-op'd.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from autofirm.knowledge.shared_knowledge_contract import SharedKnowledgeEntry

__all__ = [
    "InMemoryBitemporalKnowledgeGraph",
    "KnowledgeBackendError",
    "KnowledgeGraphBackend",
]


class KnowledgeBackendError(RuntimeError):
    """Typed fail-closed error for an illegal backend operation (§5.6).

    Raised for a duplicate-live-id write or an invalidate of an unknown/already-
    superseded entry -- a caller bug that must surface loudly, never a silent no-op.
    """


@runtime_checkable
class KnowledgeGraphBackend(Protocol):
    """The bi-temporal store seam: write, as-of-time query, invalidate.

    Implementations MUST be append-only (invalidation is logical) and MUST honour
    bi-temporal as-of semantics. The in-memory fake is the reference; a real graph
    DB is an opt-in adapter behind this same Protocol.
    """

    def write(self, entry: SharedKnowledgeEntry) -> SharedKnowledgeEntry:
        """Append ``entry`` as a new live transaction record; return it."""
        ...

    def invalidate(self, *, entry_id: str, superseded_at: datetime) -> SharedKnowledgeEntry:
        """Logically supersede the live record for ``entry_id``; return the closed one."""
        ...

    def query_as_of(
        self,
        *,
        subject: str,
        as_of: datetime,
    ) -> tuple[SharedKnowledgeEntry, ...]:
        """Return entries about ``subject`` known AND event-valid at instant ``as_of``."""
        ...

    def all_live(self) -> tuple[SharedKnowledgeEntry, ...]:
        """Return every currently-live transaction record (for projections/export)."""
        ...


class InMemoryBitemporalKnowledgeGraph:
    """Deterministic, append-only, in-memory bi-temporal store (the reference fake).

    Holds an append-only log of :class:`SharedKnowledgeEntry`. The "live" record for
    an id is the one with ``superseded_at is None``. Invalidation rewrites that
    single record with a stamped ``superseded_at`` (logical close) -- the value and
    every other field are preserved, so history is never lost.
    """

    def __init__(self) -> None:
        """Create an empty store (no external service, no network)."""
        # Append-only log: index in this list == insertion order, the deterministic
        # tiebreak for any query that must return a stable order.
        self._log: list[SharedKnowledgeEntry] = []

    def write(self, entry: SharedKnowledgeEntry) -> SharedKnowledgeEntry:
        """Append ``entry`` as a new live record (fail-closed on a duplicate live id).

        Two LIVE records for one id would make "the current value" ambiguous, so a
        write whose id already has a live record is REFUSED (§5.6) -- callers must
        invalidate first (or use :meth:`supersede`).
        """
        if self._live_index(entry.entry_id) is not None:
            # fail-closed: a second live record for one id is ambiguous state.
            raise KnowledgeBackendError(f"entry_id {entry.entry_id!r} already has a live record")
        if entry.superseded_at is not None:
            # fail-closed: a write must start LIVE; a pre-closed record is malformed.
            raise KnowledgeBackendError("a written entry must be live (superseded_at is None)")
        self._log.append(entry)
        return entry

    def invalidate(self, *, entry_id: str, superseded_at: datetime) -> SharedKnowledgeEntry:
        """Logically close the live record for ``entry_id`` at ``superseded_at``.

        Append-only: the record is rewritten in place with a stamped
        ``superseded_at`` (the contract validates ``superseded_at > recorded_at``).
        Refuses an unknown / already-superseded id (fail-closed) rather than no-op.
        """
        index = self._live_index(entry_id)
        if index is None:
            # fail-closed: nothing live to invalidate -- a caller bug, not a no-op.
            raise KnowledgeBackendError(f"no live record for entry_id {entry_id!r}")
        live = self._log[index]
        closed = live.model_copy(update={"superseded_at": superseded_at})
        self._log[index] = closed
        return closed

    def supersede(
        self, *, entry_id: str, replacement: SharedKnowledgeEntry, superseded_at: datetime
    ) -> SharedKnowledgeEntry:
        """Close the live ``entry_id`` and append ``replacement`` as the new live record.

        The atomic evolve: the prior record stays in history (closed), the new value
        becomes live. The replacement MUST carry its own (new) id so both survive in
        the log -- reusing the closed id would collide on the next live-id check.
        """
        self.invalidate(entry_id=entry_id, superseded_at=superseded_at)
        return self.write(replacement)

    def query_as_of(
        self,
        *,
        subject: str,
        as_of: datetime,
    ) -> tuple[SharedKnowledgeEntry, ...]:
        """Return entries about ``subject`` the store KNEW and were VALID at ``as_of``.

        Bi-temporal point-in-time reconstruction (Zep, folder 01). A record counts
        iff BOTH hold at instant ``as_of``:

        * transaction-time: ``recorded_at <= as_of`` AND (not yet superseded at
          ``as_of``) -- i.e. the store had learned it and had not yet forgotten it;
        * event-time: ``valid_at <= as_of`` AND (not yet invalid at ``as_of``) --
          i.e. the fact was true in the world then.

        The result is ordered by insertion index, so it is byte-stable across runs
        (§3.11). This NEVER reflects a fact recorded after ``as_of`` (the headline
        as-of-time guarantee).
        """
        hits: list[SharedKnowledgeEntry] = []
        for entry in self._log:
            if entry.subject != subject:
                continue
            # transaction-time window: known by as_of, not yet superseded at as_of.
            known = entry.recorded_at <= as_of
            not_forgotten = entry.superseded_at is None or entry.superseded_at > as_of
            # event-time window: true in the world at as_of.
            began = entry.valid_at <= as_of
            still_true = entry.invalid_at is None or entry.invalid_at > as_of
            if known and not_forgotten and began and still_true:
                hits.append(entry)
        # Insertion order is the deterministic, append-only tiebreak.
        return tuple(hits)

    def all_live(self) -> tuple[SharedKnowledgeEntry, ...]:
        """Return every live record (``superseded_at is None``) in insertion order."""
        return tuple(e for e in self._log if e.superseded_at is None)

    def history(self) -> tuple[SharedKnowledgeEntry, ...]:
        """Return the full append-only log (live + closed) in insertion order (audit)."""
        return tuple(self._log)

    def _live_index(self, entry_id: str) -> int | None:
        """Return the log index of the live record for ``entry_id``, or None.

        There is at most one live record per id (the write check enforces it), so
        the first match in insertion order is THE live record.
        """
        for index, entry in enumerate(self._log):
            if entry.entry_id == entry_id and entry.superseded_at is None:
                return index
        return None
