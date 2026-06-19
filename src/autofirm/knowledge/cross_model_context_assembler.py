"""Pure cross-model context assembler -- minimal ranked block carrying taint (W2/B2/B6).

What this does
--------------
Assembles the MINIMAL, ranked, model-agnostic shared-context block a heterogeneous
consumer (a model on a DIFFERENT provider than the writer) needs to act on a
subject at a point in time. It is a PURE function of (backend snapshot, query,
as_of, weights) -- no I/O, no clock, no network -- so the same inputs always
produce a byte-identical block (§3.11). Two guarantees are load-bearing and
MUTATION-CRITICAL:

1. **Carry taint/provenance with EVERY value, write-time -> every hop (B6 CaMeL).**
   Each assembled item keeps its source entry's :class:`TaintOrigin` and
   :class:`KnowledgeProvenance` verbatim. The taint is never dropped, never
   defaulted, never re-derived -- it travels WITH the value into the consuming
   model, so a poisoned (untrusted) entry stays marked across the relay.
2. **NEVER elevate UNTRUSTED to TRUSTED.** The trusted PLAN is built ONLY from
   TRUSTED-origin values (CaMeL P-LLM sees trusted data only); untrusted values are
   returned tagged as untrusted "reference data" and a consequential path is GATED
   -- one poisoned entry cannot steer the fleet (fail-closed).

It also enforces MINIMALITY (Lost-in-the-Middle / RULER, folder 05): it ranks by
relevance and emits only the top-``limit`` items with the most load-bearing facts
at the head, NEVER a raw dump of the whole store.

Why it exists / where it sits
------------------------------
Per ``docs/research/B2-shared-knowledge-graph/README.md`` design implication 1 the
assembler emits a minimal block from the bi-temporal store (the source of truth);
the block is the read-only in-context projection. It integrates with the A4 memory
layer's injected embedder (``autofirm.memory.semantic_embedding_backend``) for the
relevance signal, reusing the same deterministic ranking primitive.

Security / compliance invariants upheld
---------------------------------------
* **Taint propagation (§5.6, B6 CaMeL):** taint/provenance are copied, never
  invented; an item is TRUSTED in the plan iff its source entry was TRUSTED.
* **No elevation, fail closed:** :meth:`assemble` separates trusted plan-context
  from untrusted reference-context; ``consequential_action_allowed`` is True ONLY
  when no untrusted value is in the gated path -- ambiguity refuses (False).
* **Minimality / determinism (§3.11):** top-``limit`` only, ranked deterministically
  with a stable id tiebreak; identical inputs -> identical block.
"""

from __future__ import annotations

from dataclasses import dataclass

from autofirm.knowledge.knowledge_graph_backend_protocol import KnowledgeGraphBackend
from autofirm.knowledge.shared_knowledge_contract import (
    KnowledgeProvenance,
    SharedKnowledgeEntry,
    TaintOrigin,
)
from autofirm.memory.semantic_embedding_backend import EmbeddingBackend, cosine_similarity

__all__ = [
    "AssembledContext",
    "ContextItem",
    "CrossModelContextAssembler",
]


@dataclass(frozen=True)
class ContextItem:
    """One ranked shared-context item with its taint/provenance carried verbatim.

    ``origin`` and ``provenance`` are copied straight from the source entry (never
    re-derived), so the consuming model receives the value AND its capability
    metadata together -- the unit of taint propagation across the provider hop.
    """

    label: str
    value: str
    origin: TaintOrigin  # carried verbatim from the source entry's write-time taint
    provenance: KnowledgeProvenance  # carried verbatim (who wrote it, from where)
    relevance: float  # cosine similarity to the query (the ranking signal, [-1, 1])


@dataclass(frozen=True)
class AssembledContext:
    """The minimal assembled block: trusted plan-context, untrusted reference, gate.

    ``trusted_context`` holds ONLY TRUSTED-origin items -- the material a privileged
    planner may treat as a plan. ``untrusted_context`` holds UNTRUSTED items, tagged
    so the consumer treats them as data to parse, never as instructions.
    ``consequential_action_allowed`` is the fail-closed gate: True iff the gated path
    contains no untrusted value (one poisoned entry => the fleet is held back).
    """

    trusted_context: tuple[ContextItem, ...]
    untrusted_context: tuple[ContextItem, ...]
    consequential_action_allowed: bool

    def all_items(self) -> tuple[ContextItem, ...]:
        """Return trusted then untrusted items (the full minimal block, ordered)."""
        return (*self.trusted_context, *self.untrusted_context)


class CrossModelContextAssembler:
    """Pure assembler: minimal ranked shared-context with taint carried every hop."""

    def __init__(self, *, embedder: EmbeddingBackend) -> None:
        """Wire the injected (deterministic) embedder used for the relevance signal."""
        # Injected so the relevance ranking is deterministic and network-free,
        # reusing the A4 memory plane's embedding seam (no second embedding stack).
        self._embedder = embedder

    def assemble(
        self,
        *,
        backend: KnowledgeGraphBackend,
        subject: str,
        query: str,
        as_of: object,
        limit: int,
    ) -> AssembledContext:
        """Assemble the minimal ranked block for ``subject`` as known at ``as_of``.

        Pulls only the as-of-valid entries about ``subject`` from the backend (the
        source of truth), ranks them by relevance to ``query``, keeps the top
        ``limit``, and splits them by taint -- carrying each item's origin and
        provenance verbatim. ``limit`` must be positive (fail-closed); a non-positive
        budget is a caller bug, not "return everything" (that would defeat
        minimality and risk dumping a poisoned store).
        """
        if limit <= 0:
            # fail-closed: a non-positive limit is a bug, never "emit the raw dump".
            raise ValueError("limit must be a positive integer")
        # as_of is a datetime at runtime; typed as object here so this module need
        # not import datetime just for the pass-through to the backend Protocol.
        entries = backend.query_as_of(subject=subject, as_of=as_of)  # type: ignore[arg-type]
        ranked = self._rank(entries=entries, query=query)
        top = ranked[:limit]  # MINIMALITY: top-limit only, never the whole store
        trusted: list[ContextItem] = []
        untrusted: list[ContextItem] = []
        for item in top:
            # NO ELEVATION: an item lands in the trusted plan-context iff its SOURCE
            # entry was written TRUSTED. Untrusted values are never relabelled.
            if item.origin is TaintOrigin.TRUSTED:
                trusted.append(item)
            else:
                untrusted.append(item)
        # Fail-closed gate: a consequential action is permitted ONLY when NO
        # untrusted value is present in the assembled (gated) path. A single
        # poisoned/untrusted entry holds the whole fleet back (B6 fan-out defence).
        consequential_allowed = len(untrusted) == 0
        return AssembledContext(
            trusted_context=tuple(trusted),
            untrusted_context=tuple(untrusted),
            consequential_action_allowed=consequential_allowed,
        )

    def _rank(
        self, *, entries: tuple[SharedKnowledgeEntry, ...], query: str
    ) -> list[ContextItem]:
        """Rank entries by relevance to ``query``, carrying taint/provenance verbatim.

        Each entry's value is embedded and scored by cosine similarity to the query
        embedding (reusing the A4 ranking primitive). The :class:`ContextItem` copies
        ``origin`` and ``provenance`` straight from the entry -- the write-time taint
        is NEVER dropped here. Ties break on ``entry_id`` so the order is stable
        across runs (§3.11).
        """
        query_vector = self._embedder.embed(query)
        items: list[tuple[str, ContextItem]] = []
        for entry in entries:
            relevance = cosine_similarity(self._embedder.embed(entry.value), query_vector)
            item = ContextItem(
                label=entry.label,
                value=entry.value,
                origin=entry.origin,  # carried verbatim: write-time taint, no re-derive
                provenance=entry.provenance,  # carried verbatim: who/where/lineage
                relevance=relevance,
            )
            items.append((entry.entry_id, item))
        # Deterministic ranking: highest relevance first; entry_id is the stable
        # tiebreak so equal-scoring items never reorder between runs (§3.11).
        items.sort(key=lambda pair: (-pair[1].relevance, pair[0]))
        return [item for _entry_id, item in items]
