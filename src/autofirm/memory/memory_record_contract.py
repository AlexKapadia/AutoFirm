"""Typed, validated memory record -- the untrusted-content boundary (A4).

What this does
--------------
Defines :class:`MemoryRecord`, the single typed contract every stored memory must
satisfy, plus the closed :class:`MemoryKind` taxonomy (CoALA stores) and
:class:`MaturityTier` (Storage -> Reflection -> Experience). The record carries
its content, the owning agent/role (the access key), its kind + free-form tags,
its provenance lineage, its version, the visibility scope, and an injected
timestamp. Validation happens at construction (the boundary), so malformed or
oversized content can never enter the store.

Why it exists / where it sits
-----------------------------
Per ``docs/research/A4-memory-and-learning-infra/SYNTHESIS.md`` L1.A4.1 the memory
taxonomy is a two-axis model: CoALA four stores (working/episodic/semantic/
procedural) x maturity tier (Storage/Reflection/Experience). This module is the
*boundary* of the memory plane: all stored content is treated as UNTRUSTED
(injection / poisoning defence -- AgentPoison 13, CLAUDE §5.6), so content size
and field shapes are bounded here and nowhere downstream has to re-validate.

Security / compliance invariants upheld
---------------------------------------
* **Validate input at the boundary, deny by default (§5.6):** every field is
  pydantic-validated; an empty owner, an out-of-set kind/tier, an over-cap
  content blob, a blank tag, or a negative version are all REFUSED at
  construction (fail-closed) rather than stored.
* **PV (provenance, A4.4):** every record carries a queryable provenance lineage
  -- its source kind and the ids it was derived from -- so a reflection/insight
  can always be traced back to (and purged with) the source it came from.
* **WA marker (A4.4):** the record names its ``written_by`` principal; the store
  refuses a write whose authoriser does not own the target scope (enforced in the
  store, recorded here).
* **Determinism (§3.11):** ``injected_at`` is supplied by the caller (from the
  layer's injected clock), never read from the wall clock here, so records are
  reproducible in tests and replay.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

__all__ = [
    "MAX_CONTENT_BYTES",
    "MAX_TAGS",
    "MaturityTier",
    "MemoryKind",
    "MemoryRecord",
    "Provenance",
    "ProvenanceSource",
    "Visibility",
]

# Hard content byte cap (injection / resource-exhaustion defence -- §5.6). A
# record whose content exceeds this is refused at the boundary, never stored, so a
# single oversized memory can neither exhaust memory nor wedge the retriever.
# Generous for distilled notes/insights; tune per deployment (never a magic
# constant tuned to a fixture).
MAX_CONTENT_BYTES = 64 * 1024  # 64 KiB

# Hard cap on the number of tags per record (resource / index-blowup defence).
MAX_TAGS = 64

# A non-empty, length-bounded token (owner id, tag, derived-from id). Bounding
# length is part of the injection defence: an unbounded string is a
# resource-exhaustion and log-poisoning vector.
_Token = Annotated[str, StringConstraints(min_length=1, max_length=512, strip_whitespace=True)]


class MemoryKind(StrEnum):
    """Closed CoALA-derived memory taxonomy (SYNTHESIS L1.A4.1, axis 1).

    A closed set (not free text) is what lets retrieval and governance reason
    about kind deterministically. An out-of-set kind is refused at the boundary
    (fail-closed).
    """

    EPISODIC = "episodic"  # a specific past event/observation a run lived through
    SEMANTIC = "semantic"  # a durable fact / piece of world knowledge
    PROCEDURAL = "procedural"  # a learned skill / how-to (Voyager skill-library)
    REFLECTION = "reflection"  # a synthesised lesson distilled from observations
    INSIGHT = "insight"  # a cross-trajectory experiential insight (ExpeL)


class MaturityTier(StrEnum):
    """Closed maturity tier (SYNTHESIS L1.A4.1, axis 2: Storage->Reflection->Experience).

    Records the *maturity* of a memory: a raw stored observation, a reflection
    synthesised from observations, or a distilled cross-trajectory experience.
    """

    STORAGE = "storage"  # raw, as-written
    REFLECTION = "reflection"  # synthesised from one or more storage records
    EXPERIENCE = "experience"  # distilled across many trajectories (most mature)


class Visibility(StrEnum):
    """Closed visibility scope governing who may retrieve a record (PS -- A4.4).

    PRIVATE records are reachable ONLY by their owner; SHARED records are
    additionally reachable by any reader (the org/shared scope). Scoping is
    enforced in the data layer by the store, not by convention (CLAUDE §5.6).
    """

    PRIVATE = "private"  # owner-only (default; fail-closed -- least privilege)
    SHARED = "shared"  # readable org-wide / by any principal


class ProvenanceSource(StrEnum):
    """Closed set naming how a record came to exist (PV lineage -- A4.4)."""

    DIRECT_WRITE = "direct_write"  # written directly by an agent/role
    REFLECTION_OF = "reflection_of"  # synthesised from other records
    SUPERSEDES = "supersedes"  # a new version replacing a prior record


class Provenance(BaseModel):
    """Queryable provenance lineage for one record (PV primitive -- A4.4).

    ``source`` says how the record was produced; ``derived_from`` lists the
    memory ids it was distilled/superseded from (empty for a direct write). This
    is what lets exact deletion (VF) walk the lineage and purge derived
    reflections/insights, not just the row.
    """

    model_config = ConfigDict(frozen=True)

    source: ProvenanceSource
    derived_from: tuple[_Token, ...] = ()

    @field_validator("derived_from")
    @classmethod
    def _bounded_lineage(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        # fail-closed: an unbounded lineage is a resource-exhaustion vector and a
        # sign of a malformed derivation; cap it at the tag bound.
        if len(value) > MAX_TAGS:
            raise ValueError(f"derived_from exceeds MAX_TAGS {MAX_TAGS}")
        return value


class MemoryRecord(BaseModel):
    """One typed memory (frozen once built -- append-only / versioned semantics).

    A record is immutable: "updating" a memory writes a NEW record that supersedes
    the old one (preserving history), it never mutates an existing record. The
    ``owner`` is the access key; ``visibility`` decides whether non-owners may
    read it; ``version`` is the 1-based position in the supersession chain; and
    ``injected_at`` is the deterministic, injected write time used by the recency
    component of retrieval.
    """

    model_config = ConfigDict(frozen=True)

    memory_id: _Token
    owner: _Token  # the principal that OWNS this memory (agent id / role / scope)
    written_by: _Token  # the authenticated principal that authored the write (WA)
    content: str
    kind: MemoryKind
    tier: MaturityTier
    visibility: Visibility = Visibility.PRIVATE  # least privilege: private default
    tags: tuple[_Token, ...] = ()
    provenance: Provenance
    version: int  # 1-based position in the supersession chain
    injected_at: datetime  # injected by the layer clock, never the wall clock

    @field_validator("content")
    @classmethod
    def _content_within_cap(cls, value: str) -> str:
        """Fail-closed: refuse empty or over-cap content at the boundary (§5.6).

        Content is UNTRUSTED. Empty content is a malformed memory (nothing to
        recall); over-cap content is a resource-exhaustion vector. Both are
        refused here so no downstream stage has to re-check.
        """
        if not value:
            raise ValueError("content must be non-empty")  # fail-closed: no empty memories
        size = len(value.encode("utf-8"))
        if size > MAX_CONTENT_BYTES:
            raise ValueError(f"content size {size} exceeds MAX_CONTENT_BYTES {MAX_CONTENT_BYTES}")
        return value

    @field_validator("tags")
    @classmethod
    def _tags_within_cap(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        # fail-closed: cap tag count (index-blowup / resource defence, §5.6).
        if len(value) > MAX_TAGS:
            raise ValueError(f"tag count {len(value)} exceeds MAX_TAGS {MAX_TAGS}")
        return value

    @field_validator("version")
    @classmethod
    def _version_positive(cls, value: int) -> int:
        # fail-closed: versions are 1-based; a non-positive version is malformed
        # and could corrupt the supersession chain ordering.
        if value < 1:
            raise ValueError("version must be >= 1 (1-based supersession position)")
        return value
