"""High-level agent/org memory & learning API (A4 composition root).

What this does
--------------
:class:`AgentMemoryLayer` is the single facade agents and the org use to
remember, recall, evolve, roll back, and forget memory. It composes the injected
seams (clock, id-generator, embedding backend) with the
:class:`VersionedMemoryStore` and the explainable retrieval score into four
operations:

* :meth:`remember` -- validate + write a new memory (WA enforced by the store).
* :meth:`recall` -- principal-scoped (PS) retrieval ranked by the explainable
  recency/relevance/importance score (Gen-Agents 04), top items only (so context
  stays short -- Lost-in-the-Middle 08 / RULER 17).
* :meth:`evolve` -- supersede an existing memory with a new version, preserving
  the prior one in history (learning without losing provenance; A-Mem 03).
* :meth:`forget` -- exact deletion with lineage purge (VF; SISA 15 / GDPR 17).

Per-agent / per-role memory is persisted under the writer's own owner scope; the
shared org scope is a reserved owner any principal may contribute to and everyone
can read.

Why it exists / where it sits
-----------------------------
Per ``docs/research/A4-memory-and-learning-infra/SYNTHESIS.md`` this is the
"External memory + Advanced/Modular RAG retrieval, NOT context-stuffing" surface.
It is the only module callers touch; the store, scorer, and embedder are
implementation details behind it.

Security / compliance invariants upheld
---------------------------------------
* **Fail closed (§5.6):** writes/reads/forgets refuse out-of-scope or malformed
  operations via the store's typed errors; ``recall`` never returns another
  owner's PRIVATE memory.
* **Determinism (§3.11):** ids, timestamps, and embeddings are all injected /
  deterministic, so a sequence of operations yields identical results and an
  identical, explainable ranking every run.
* **Generality (§3.9):** retrieval weights/decay are injected tunables, never
  magic constants fitted to one dataset.
"""

from __future__ import annotations

from dataclasses import dataclass

from autofirm.memory.memory_identifiers import MemoryClock, MemoryIdGenerator
from autofirm.memory.memory_record_contract import (
    MaturityTier,
    MemoryKind,
    MemoryRecord,
    Provenance,
    ProvenanceSource,
    Visibility,
)
from autofirm.memory.retrieval_ranking_score import (
    RetrievalScore,
    RetrievalWeights,
    score_record,
)
from autofirm.memory.semantic_embedding_backend import EmbeddingBackend
from autofirm.memory.versioned_memory_store import VersionedMemoryStore

__all__ = ["AgentMemoryLayer", "RecallResult"]


@dataclass(frozen=True)
class RecallResult:
    """One ranked recall hit: the record plus its explainable score breakdown.

    Pairing the record with its :class:`RetrievalScore` keeps recall explainable
    (CLAUDE §3.11) -- the caller can justify exactly why each hit ranked where it
    did (which of recency / relevance / importance drove it).
    """

    record: MemoryRecord
    score: RetrievalScore


class AgentMemoryLayer:
    """Composition root for agent/org memory: remember / recall / evolve / forget."""

    def __init__(
        self,
        *,
        clock: MemoryClock,
        id_generator: MemoryIdGenerator,
        embedder: EmbeddingBackend,
        weights: RetrievalWeights | None = None,
        store: VersionedMemoryStore | None = None,
    ) -> None:
        """Wire the injected seams; default weights/store are created if omitted.

        Everything that could introduce nondeterminism (now, new ids, embeddings)
        is INJECTED, so the layer is a pure function of its inputs and the
        operation sequence (§3.11).
        """
        self._clock = clock
        self._id_generator = id_generator
        self._embedder = embedder
        self._weights = weights if weights is not None else RetrievalWeights()
        self._store = store if store is not None else VersionedMemoryStore()

    @staticmethod
    def shared_scope() -> str:
        """Return the reserved owner id for org-wide / shared memory."""
        return VersionedMemoryStore.reserved_shared_scope()

    # -- write (WA) --------------------------------------------------------

    def remember(  # noqa: PLR0913 -- keyword-only API mirroring the record fields
        self,
        *,
        written_by: str,
        owner: str,
        content: str,
        kind: MemoryKind,
        tier: MaturityTier = MaturityTier.STORAGE,
        visibility: Visibility = Visibility.PRIVATE,
        tags: tuple[str, ...] = (),
        derived_from: tuple[str, ...] = (),
    ) -> MemoryRecord:
        """Validate + persist a new memory, returning the stored record.

        Builds a fresh, boundary-validated :class:`MemoryRecord` (version 1,
        injected id + timestamp) and writes it through the store, which enforces
        the WA check. ``derived_from`` (if given) records a reflection lineage so
        the record can be purged with its source on VF.
        """
        source = (
            ProvenanceSource.REFLECTION_OF if derived_from else ProvenanceSource.DIRECT_WRITE
        )
        record = MemoryRecord(
            memory_id=self._id_generator.next_id("mem"),
            owner=owner,
            written_by=written_by,
            content=content,  # untrusted; re-validated/ capped at the contract boundary
            kind=kind,
            tier=tier,
            visibility=visibility,
            tags=tags,
            provenance=Provenance(source=source, derived_from=derived_from),
            version=1,
            injected_at=self._clock.now(),  # injected, deterministic timestamp
        )
        return self._store.write(record)

    # -- read (PS) ---------------------------------------------------------

    def recall(
        self,
        *,
        reader: str,
        owner: str,
        query: str,
        limit: int,
        importance_of: dict[str, float] | None = None,
    ) -> list[RecallResult]:
        """Return the top-``limit`` readable records for ``owner`` ranked by score.

        PS: only records the ``reader`` is permitted to see are scored (private
        records of another owner are filtered IN THE DATA LAYER, before ranking).
        Each candidate is scored by the explainable recency/relevance/importance
        blend against the embedded query; ties break on memory_id for a
        deterministic order. ``limit`` must be positive (fail-closed) and the
        result is truncated so the assembled context stays short.
        """
        if limit <= 0:
            # fail-closed: a non-positive limit is a caller bug, not "return all".
            raise ValueError("limit must be a positive integer")
        importance_of = importance_of or {}
        query_vector = self._embedder.embed(query)
        reference = self._clock.now()
        candidates = self._store.scan_readable(owner=owner, reader=reader)
        scored: list[RecallResult] = []
        for record in candidates:
            score = score_record(
                record_vector=self._embedder.embed(record.content),
                query_vector=query_vector,
                written_at=record.injected_at,
                # importance defaults to 0.0 when unspecified (no salience claimed).
                importance=importance_of.get(record.memory_id, 0.0),
                reference_time=reference,
                weights=self._weights,
            )
            scored.append(RecallResult(record=record, score=score))
        # Deterministic ranking: highest total first, memory_id as the stable
        # tiebreak so equal-scoring records never reorder between runs (§3.11).
        scored.sort(key=lambda r: (-r.score.total, r.record.memory_id))
        return scored[:limit]

    def get(self, *, reader: str, owner: str, memory_id: str) -> MemoryRecord:
        """Fetch one record by id, PS-checked (fail-closed on cross-owner private)."""
        return self._store.get(owner=owner, memory_id=memory_id, reader=reader)

    # -- evolve (versioning) -----------------------------------------------

    def evolve(  # noqa: PLR0913 -- keyword-only supersession delta surface
        self,
        *,
        written_by: str,
        owner: str,
        memory_id: str,
        content: str,
        tags: tuple[str, ...] | None = None,
        visibility: Visibility | None = None,
    ) -> MemoryRecord:
        """Supersede ``memory_id`` with a new version, preserving the prior in history.

        Learning without losing provenance: a logical memory keeps a STABLE
        ``memory_id`` across its whole supersession chain. The prior version stays
        in the append-only history (rollback / audit), while a new record with the
        SAME id but the next version number and provenance SUPERSEDES becomes the
        live head. Unspecified fields inherit from the current head, so an evolve
        is a minimal, explicit delta.
        """
        head = self._store.get(owner=owner, memory_id=memory_id, reader=written_by)
        new_version = self._store.next_version(
            owner=owner, memory_id=memory_id, written_by=written_by
        )
        evolved = MemoryRecord(
            memory_id=memory_id,  # stable id: the supersession chain shares one id
            owner=owner,
            written_by=written_by,
            content=content,
            kind=head.kind,
            tier=head.tier,
            visibility=visibility if visibility is not None else head.visibility,
            tags=tags if tags is not None else head.tags,
            # SUPERSEDES with no external derived_from: the chain is the id itself.
            provenance=Provenance(source=ProvenanceSource.SUPERSEDES),
            version=new_version,
            injected_at=self._clock.now(),
        )
        return self._store.write(evolved)

    def history(self, *, owner: str, memory_id: str) -> list[MemoryRecord]:
        """Return the full version history of one id (oldest first) for audit/RB."""
        return self._store.versions_of(owner=owner, memory_id=memory_id)

    def rollback(
        self, *, written_by: str, owner: str, memory_id: str, target_version: int
    ) -> MemoryRecord:
        """Roll ``memory_id`` back to ``target_version`` (RB), append-only.

        Writes a new live version copying the historical ``target_version``'s
        content, so the rollback is auditable and reversible -- the bad version
        stays in history, it is simply no longer the head. Refuses an unknown
        target version (fail-closed).
        """
        return self._store.restore_version(
            owner=owner,
            memory_id=memory_id,
            target_version=target_version,
            written_by=written_by,
            injected_at=self._clock.now(),
        )

    # -- forget (VF) -------------------------------------------------------

    def forget(self, *, owner: str, memory_id: str) -> tuple[str, ...]:
        """Exactly delete ``memory_id`` and every record derived from it (VF).

        Returns the sorted tuple of purged ids -- the auditable non-recoverability
        proof. After this, the purged records are no longer live (recall/get
        cannot return them).
        """
        return self._store.delete_with_lineage(owner=owner, memory_id=memory_id)
