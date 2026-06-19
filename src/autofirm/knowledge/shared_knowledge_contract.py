"""Model-agnostic shared-knowledge entry -- the cross-provider interop primitive (W2/B2).

What this does
--------------
Defines :class:`SharedKnowledgeEntry`, the single typed, frozen, model-agnostic
"shared-context block" that every heterogeneous agent (different providers) reads
and writes, plus the closed :class:`TaintOrigin` (trusted vs untrusted) and
:class:`KnowledgeProvenance` lineage. The block follows the Letta MemGPT shape
(``label``, ``description``, ``value``, ``limit`` -- folder 04 of B2) so it is
neutral to any one model's prompt format, and it adds the two things B2/B6 require:

* **PROVENANCE + TAINT attached AT WRITE-TIME** (B6 / CaMeL folder): every entry
  records whether its ``value`` originated from a TRUSTED principal (a plan from
  the privileged planner) or UNTRUSTED data (a parsed document, a web page, a peer
  relay). The taint is part of the immutable record, so it travels WITH the value
  across every hop -- a poisoned entry cannot launder its origin.
* **BI-TEMPORAL validity** (Zep/Graphiti -- folder 01): event-time
  ``valid_at``/``invalid_at`` (when the fact is true in the world) AND
  transaction-time ``recorded_at``/``superseded_at`` (when the store learned it),
  giving native "what did the org know at time T" with append-only invalidation.

Why it exists / where it sits
------------------------------
Per ``docs/research/B2-shared-knowledge-graph/README.md`` the shared-context block
is the model-agnostic interop primitive and the bi-temporal store is the source of
truth (CQRS). This module is the *boundary* of the shared-knowledge plane: all
entry content is treated as UNTRUSTED (poisoning defence -- B6, CLAUDE.md §5.6), so
field shapes, the value byte cap, and the temporal ordering are validated here and
nowhere downstream has to re-check.

Security / compliance invariants upheld
---------------------------------------
* **Taint at write-time, deny by default (§5.6, B6 CaMeL):** ``origin`` is REQUIRED
  and immutable; there is no path that mutates an entry to TRUSTED after the fact.
  An untrusted-origin value can never be silently relabelled.
* **Validate input at the boundary (§5.6):** empty/over-cap value, blank label,
  too many tags, or an out-of-order temporal pair are REFUSED at construction
  (fail-closed) rather than stored.
* **Determinism (§3.11):** every timestamp is INJECTED by the caller (from the
  store's clock), never read from the wall clock here, so entries are reproducible.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator, model_validator

__all__ = [
    "MAX_TAGS",
    "MAX_VALUE_BYTES",
    "KnowledgeProvenance",
    "SharedKnowledgeEntry",
    "TaintOrigin",
]

# Hard value byte cap (injection / resource-exhaustion defence -- §5.6). A single
# shared entry whose value exceeds this is refused at the boundary, never stored,
# so one oversized poisoned entry cannot exhaust memory or wedge the assembler.
# Generous for a distilled coordination fact; never a constant tuned to a fixture.
MAX_VALUE_BYTES = 32 * 1024  # 32 KiB

# Hard cap on tags per entry (index-blowup / resource defence).
MAX_TAGS = 64

# A non-empty, length-bounded token (entry id, label, principal, tag). Bounding
# length is part of the injection defence: an unbounded string is a
# resource-exhaustion and log-poisoning vector.
_Token = Annotated[str, StringConstraints(min_length=1, max_length=512, strip_whitespace=True)]


class TaintOrigin(StrEnum):
    """Closed taint label: where a shared value came from (B6 CaMeL capability).

    This is the heart of the shared-knowledge poisoning defence. The label is set
    AT WRITE-TIME and is immutable, so it travels WITH the value across every agent
    hop and into the assembler. The deterministic core NEVER elevates UNTRUSTED to
    TRUSTED -- a privileged plan can only be built from TRUSTED values (fail-closed).
    """

    TRUSTED = "trusted"  # from a trusted principal / the privileged planner (P-LLM)
    UNTRUSTED = "untrusted"  # parsed from a document/web/peer relay (Q-LLM territory)


class KnowledgeProvenance(BaseModel):
    """Queryable write-time provenance for one shared entry (B6 CaMeL capability).

    Records WHO wrote the value (the authenticated principal) and WHICH upstream
    entry ids it was derived from. Together with :class:`TaintOrigin` on the entry
    this is the capability metadata CaMeL attaches to every value -- it lets the
    assembler gate consequential use and lets an auditor trace a poisoned value back
    to its origin and every hop it travelled.
    """

    model_config = ConfigDict(frozen=True)

    written_by: _Token  # the authenticated principal that authored the write (WA)
    source_provider: _Token  # the model/provider family that produced the value (interop audit)
    derived_from: tuple[_Token, ...] = ()  # upstream entry ids this value came from

    @field_validator("derived_from")
    @classmethod
    def _bounded_lineage(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        # fail-closed: an unbounded lineage is a resource-exhaustion vector and a
        # sign of a malformed derivation; cap it at the tag bound.
        if len(value) > MAX_TAGS:
            raise ValueError(f"derived_from exceeds MAX_TAGS {MAX_TAGS}")
        return value


class SharedKnowledgeEntry(BaseModel):
    """One model-agnostic shared-context block (frozen; append-only / bi-temporal).

    The Letta shape (``label``/``description``/``value``/``limit``) makes the entry
    neutral across providers; ``origin`` + ``provenance`` carry the write-time taint
    capability; the bi-temporal pair gives as-of-time correctness. An entry is
    immutable: "updating" writes a NEW entry that supersedes the old one (the store
    sets ``superseded_at`` on the prior transaction-time record), it never mutates.
    """

    model_config = ConfigDict(frozen=True)

    entry_id: _Token
    subject: _Token  # the entity/anchor this fact is about (LOCAL/entity-anchored retrieval)
    label: _Token  # short Letta-style label, e.g. "pricing_model"
    description: str  # what this block is for (may be empty; not the load-bearing value)
    value: str  # the actual shared content (UNTRUSTED unless origin is TRUSTED)
    limit: int  # advisory max characters a consumer should budget for this block
    origin: TaintOrigin  # write-time taint -- immutable, travels with the value
    provenance: KnowledgeProvenance
    tags: tuple[_Token, ...] = ()
    # Event-time validity (world time): when the fact became / stopped being true.
    valid_at: datetime
    invalid_at: datetime | None = None  # None => still valid in event time
    # Transaction-time (store time): when the store learned / forgot the fact.
    recorded_at: datetime  # injected by the store clock, never the wall clock
    superseded_at: datetime | None = None  # None => still the live transaction record

    @field_validator("value")
    @classmethod
    def _value_within_cap(cls, value: str) -> str:
        """Fail-closed: refuse empty or over-cap value at the boundary (§5.6).

        The value is UNTRUSTED content. Empty is a malformed entry (nothing to
        share); over-cap is a resource-exhaustion / poisoning vector. Both are
        refused here so no downstream stage has to re-check.
        """
        if not value:
            raise ValueError("value must be non-empty")  # fail-closed: no empty entries
        size = len(value.encode("utf-8"))
        if size > MAX_VALUE_BYTES:
            raise ValueError(f"value size {size} exceeds MAX_VALUE_BYTES {MAX_VALUE_BYTES}")
        return value

    @field_validator("tags")
    @classmethod
    def _tags_within_cap(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        # fail-closed: cap tag count (index-blowup / resource defence, §5.6).
        if len(value) > MAX_TAGS:
            raise ValueError(f"tag count {len(value)} exceeds MAX_TAGS {MAX_TAGS}")
        return value

    @field_validator("limit")
    @classmethod
    def _limit_positive(cls, value: int) -> int:
        # fail-closed: a non-positive budget is malformed -- a consumer cannot
        # allocate zero/negative space for a block that must carry a value.
        if value <= 0:
            raise ValueError("limit must be a positive character budget")
        return value

    @model_validator(mode="after")
    def _event_time_ordered(self) -> SharedKnowledgeEntry:
        """Fail-closed: event-time validity must be ordered (valid_at < invalid_at).

        A fact cannot stop being true at or before it started being true; an
        inverted/zero-width interval is malformed and would corrupt as-of-time
        reconstruction, so we refuse it at the boundary (§5.6) rather than store it.
        """
        if self.invalid_at is not None and self.invalid_at <= self.valid_at:
            raise ValueError("invalid_at must be strictly after valid_at (event-time order)")
        return self

    @model_validator(mode="after")
    def _transaction_time_ordered(self) -> SharedKnowledgeEntry:
        """Fail-closed: transaction-time must be ordered (recorded_at < superseded_at).

        The store cannot forget a fact at or before it recorded it; an inverted
        transaction interval is malformed and would corrupt "what did we know at T",
        so we refuse it at the boundary (§5.6).
        """
        if self.superseded_at is not None and self.superseded_at <= self.recorded_at:
            raise ValueError("superseded_at must be strictly after recorded_at (txn-time order)")
        return self
