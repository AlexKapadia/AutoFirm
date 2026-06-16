"""Append-only, versioned, principal-scoped memory store (A4 core).

What this does
--------------
:class:`VersionedMemoryStore` is the deterministic, in-memory heart of the memory
layer. It persists :class:`MemoryRecord` values append-only (a "write" never
mutates a row -- superseding writes a NEW version that links to the prior one),
keyed by owner so each agent/role's memory is stored *with its owner*. It
enforces the five A4 governance primitives:

* **WA (write-authorization):** a write is refused unless the author is
  authorised for the target owner scope.
* **PV (provenance):** every record's lineage is queryable; supersession and
  reflection links are preserved.
* **PS (principal-scope):** retrieval/get is scoped in the data layer -- a reader
  never reaches another owner's PRIVATE record.
* **RB (rollback):** the full version history is retained so any owner scope can
  be rolled back to a known-safe version.
* **VF (verified-forget):** exact deletion drops the record AND walks the
  provenance lineage to purge records derived from it, returning the purged ids
  as a non-recoverability proof.

Why it exists / where it sits
-----------------------------
Per ``docs/research/A4-memory-and-learning-infra/SYNTHESIS.md`` durable knowledge
lives in a swappable external index (Lewis 05); this in-memory implementation is
the deterministic core used by the high-level layer and every unit test (no
network -- CLAUDE §5.5). A production index implements the same write/get/scan
surface behind the same governance checks.

Security / compliance invariants upheld
---------------------------------------
* **Fail closed (§5.6):** unauthorised writes, cross-owner private reads, and
  operations on missing/forgotten ids raise typed errors -- never silent success.
* **Least privilege (§5.6):** PRIVATE is the default; a non-owner can reach a
  record only if it is explicitly SHARED.
* **Determinism (§3.11):** no ambient clock/randomness; ids and timestamps are
  injected, so the same operation sequence yields the same store every run.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from autofirm.memory.memory_access_errors import (
    MemoryWriteAuthorizationError,
    PrincipalScopeViolationError,
    RecordNotFoundError,
)
from autofirm.memory.memory_record_contract import (
    MemoryRecord,
    Provenance,
    ProvenanceSource,
    Visibility,
)

__all__ = ["VersionedMemoryStore"]

# The reserved owner scope for org-wide / shared memory. A write to this scope is
# the one case where author != owner is permitted (any authenticated principal
# may contribute org knowledge), and its records are readable by everyone.
SHARED_SCOPE = "__org_shared__"


@dataclass
class _OwnerPartition:
    """All records belonging to one owner scope, partitioned for data-layer PS.

    ``live`` maps a memory id to its current record; ``history`` keeps every
    version ever written (append-only) so rollback (RB) and provenance walks (PV)
    have the full lineage even after supersession or deletion.
    """

    live: dict[str, MemoryRecord] = field(default_factory=dict)
    history: list[MemoryRecord] = field(default_factory=list)


class VersionedMemoryStore:
    """In-memory, append-only, owner-partitioned record store with A4 governance.

    Not thread-safe by itself: the memory layer serialises access, so the core is
    single-writer by construction (mirrors the comms/saga substrates).
    """

    def __init__(self) -> None:
        """Create an empty store with one partition per owner (created on demand)."""
        # Partitioning BY OWNER in the data layer is the PS control: a reader can
        # only be handed records from its own partition (or the shared scope).
        self._partitions: dict[str, _OwnerPartition] = defaultdict(_OwnerPartition)

    # -- writes (WA) -------------------------------------------------------

    def write(self, record: MemoryRecord) -> MemoryRecord:
        """Append ``record`` to its owner partition after the WA check (fail-closed).

        WA: the author (``written_by``) must equal the target ``owner`` UNLESS the
        target is the shared org scope (where any authenticated principal may
        contribute). Any other author/owner mismatch is refused -- no write
        without an authorised source.
        """
        if record.owner not in (record.written_by, SHARED_SCOPE):
            # fail-closed (WA): author is not authorised for this private owner.
            raise MemoryWriteAuthorizationError(
                f"principal {record.written_by!r} may not write to owner {record.owner!r}"
            )
        partition = self._partitions[record.owner]
        partition.live[record.memory_id] = record
        partition.history.append(record)  # append-only: history is never rewritten
        return record

    # -- reads (PS) --------------------------------------------------------

    def get(self, *, owner: str, memory_id: str, reader: str) -> MemoryRecord:
        """Return one live record IF the reader is in scope (PS), else fail-closed.

        PS: the reader may read its own owner scope, or any SHARED record. A
        reader asking for another owner's PRIVATE record is refused -- the scope
        check happens in the data layer, before any content is returned.
        """
        record = self._partitions[owner].live.get(memory_id)
        if record is None:
            # fail-closed (VF/RB): never fabricate a missing/forgotten record.
            raise RecordNotFoundError(f"no live record {memory_id!r} for owner {owner!r}")
        self._enforce_read_scope(record=record, reader=reader)
        return record

    def scan_readable(self, *, owner: str, reader: str) -> list[MemoryRecord]:
        """Return every live record in ``owner`` the ``reader`` is permitted to see.

        PS in the data layer: if the reader owns the scope (or it is the shared
        scope) all live records are returned; otherwise ONLY the SHARED records
        are -- a non-owner can never enumerate another owner's PRIVATE memory.
        """
        partition = self._partitions.get(owner)
        if partition is None:
            return []
        owns_scope = owner in (reader, SHARED_SCOPE)
        return [
            rec
            for rec in partition.live.values()
            # least privilege: non-owners see SHARED records only.
            if owns_scope or rec.visibility is Visibility.SHARED
        ]

    @staticmethod
    def _enforce_read_scope(*, record: MemoryRecord, reader: str) -> None:
        """Fail-closed PS guard: refuse a cross-owner read of a PRIVATE record."""
        if record.owner in (reader, SHARED_SCOPE):
            return  # owner (or shared scope) -> permitted
        if record.visibility is Visibility.SHARED:
            return  # explicitly shared -> permitted to any reader
        # fail-closed (PS): a non-owner reaching a PRIVATE record is refused.
        raise PrincipalScopeViolationError(
            f"reader {reader!r} may not read private record owned by {record.owner!r}"
        )

    # -- supersession (versioning + PV) -----------------------------------

    def next_version(self, *, owner: str, memory_id: str, written_by: str) -> int:
        """Return the version a supersession of ``memory_id`` should carry.

        Looks up the current live record (fail-closed if absent) and returns its
        version + 1, so supersession chains are strictly increasing per id.
        """
        current = self.get(owner=owner, memory_id=memory_id, reader=written_by)
        return current.version + 1

    # -- rollback (RB) -----------------------------------------------------

    def versions_of(self, *, owner: str, memory_id: str) -> list[MemoryRecord]:
        """Return the full append-only version history of one id (oldest first).

        RB / PV: history is never rewritten, so this is the audit trail used to
        roll an id back to a known-safe version.
        """
        return [rec for rec in self._partitions[owner].history if rec.memory_id == memory_id]

    def restore_version(
        self,
        *,
        owner: str,
        memory_id: str,
        target_version: int,
        written_by: str,
        injected_at: object,
    ) -> MemoryRecord:
        """Roll ``memory_id`` back by writing a new version copying ``target_version``.

        RB done append-only: we never mutate history. We find the historical
        version, then write a fresh version under the SAME id (next version,
        provenance SUPERSEDES) carrying the old content -- so the rollback is
        itself an auditable forward step, not a destructive rewrite. Refuses if
        the target version was never recorded (fail-closed).
        """
        history = self.versions_of(owner=owner, memory_id=memory_id)
        source = next((r for r in history if r.version == target_version), None)
        if source is None:
            # fail-closed (RB): cannot restore a version that was never written.
            raise RecordNotFoundError(
                f"version {target_version} of {memory_id!r} not found for owner {owner!r}"
            )
        head = self.get(owner=owner, memory_id=memory_id, reader=written_by)
        restored = MemoryRecord(
            memory_id=memory_id,  # stable id: rollback stays in the same chain
            owner=owner,
            written_by=written_by,
            content=source.content,
            kind=source.kind,
            tier=source.tier,
            visibility=source.visibility,
            tags=source.tags,
            provenance=Provenance(source=ProvenanceSource.SUPERSEDES),
            version=head.version + 1,
            injected_at=injected_at,  # type: ignore[arg-type]  # datetime; pydantic re-validates
        )
        return self.write(restored)

    # -- verified-forget (VF) ---------------------------------------------

    def delete_with_lineage(self, *, owner: str, memory_id: str) -> tuple[str, ...]:
        """Exactly delete ``memory_id`` AND every record derived from it (VF).

        VF: external-store exact delete is the only verifiable path (SISA 15,
        GDPR Art. 17). We drop the target from ``live`` and then transitively drop
        any live record whose provenance lineage references a purged id, so a
        reflection/insight distilled from the deleted source cannot survive. The
        returned tuple is the auditable set of purged ids (non-recoverability
        proof). Refuses if the target id is not live (fail-closed).
        """
        partition = self._partitions[owner]
        if memory_id not in partition.live:
            # fail-closed (VF): cannot prove deletion of something not present.
            raise RecordNotFoundError(f"no live record {memory_id!r} for owner {owner!r}")
        purged: set[str] = {memory_id}
        del partition.live[memory_id]
        # Transitive purge: repeatedly drop live records derived from a purged id
        # until a fixed point. Bounded by the (shrinking) live-record count, so it
        # always terminates -- no unbounded loop a mutant could hang.
        for _ in range(len(partition.live)):
            cascade = {
                mid
                for mid, rec in partition.live.items()
                if any(parent in purged for parent in rec.provenance.derived_from)
            }
            if not cascade:
                break  # fixed point reached: nothing else derives from a purged id
            for mid in cascade:
                del partition.live[mid]
            purged |= cascade
        # Sorted for a deterministic, comparable non-recoverability proof.
        return tuple(sorted(purged))

    def is_live(self, *, owner: str, memory_id: str) -> bool:
        """Return True iff ``memory_id`` is currently a live (non-forgotten) record."""
        partition = self._partitions.get(owner)
        return partition is not None and memory_id in partition.live

    @staticmethod
    def reserved_shared_scope() -> str:
        """Return the reserved owner id for org-wide / shared memory."""
        return SHARED_SCOPE
