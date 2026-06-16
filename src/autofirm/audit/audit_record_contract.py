"""The append-only audit record: PROV-shaped, FHIR-split, hashes-not-PII.

What this does
--------------
Defines :class:`AuditRecord`, the typed contract every sensitive action emits, and
its **canonical byte serialisation** -- the deterministic, injective encoding that
is fed to :func:`autofirm.audit.rfc6962_hashing.leaf_hash` to produce the leaf
commitment both E5 candidates chain/tree over. The contract mirrors
``data-contracts.md`` §3 (PROV-DM why-record + FHIR AuditEvent security-record),
and the :class:`SignedTreeHead` gate-time commitment.

Why it exists / where it sits
-----------------------------
Per ``docs/research/A6-governance-and-auditability/SYNTHESIS.md`` (L1.A6.1/2) the
record carries the PROV triple (entity/activity/agent) plus the FHIR outcome, and
the log must be append-only and store **hashes/lineage of sensitive data, never
raw PII** (the T1 ruling). Crypto-shredding (A6.4) erases *content* and writes a
tombstone without rewriting the chain -- modelled here by content being a digest
(:class:`EntityRef.content_hash`) that can be tombstoned, so no plaintext PII ever
enters a record in the first place.

Security / compliance invariants upheld
---------------------------------------
* **Hashes-not-PII (T1):** ``EntityRef`` holds a ``content_hash`` digest, never raw
  content. The contract is fail-closed -- a non-hex / wrong-length digest is
  refused at construction (pydantic validation), so a record carrying raw PII
  cannot be built.
* **Canonical serialisation is deterministic and injective:** sorted keys, no
  whitespace, explicit field ordering, length-prefix-free JSON with UTF-8 -- the
  same record always hashes to the same leaf (CLAUDE.md §3.11 determinism), and
  two different records can never collide on the encoding.
* **Append-only:** the model is frozen (immutable) once built; the log structures
  (candidates A/B) never expose UPDATE/DELETE (FHIR no-update/no-delete, src 02).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

from autofirm.audit.rfc6962_hashing import HASH_BYTES, leaf_hash

__all__ = [
    "AuditOutcome",
    "AuditRecord",
    "EntityRef",
    "SignedTreeHead",
    "canonical_bytes",
]

# A hex SHA-256 digest: exactly 64 lowercase hex chars. Used for every place a
# sensitive value would otherwise appear (hashes-not-PII, T1).
HexDigest = Annotated[
    str, StringConstraints(pattern=r"^[0-9a-f]{64}$", min_length=64, max_length=64)
]


class AuditOutcome(StrEnum):
    """FHIR AuditEvent outcome (``data-contracts.md`` §3).

    ``DENY`` records a fail-closed refusal -- denials are audited, not dropped
    (CLAUDE.md §5.6), so the log proves the system refused rather than silently
    proceeded.
    """

    SUCCESS = "SUCCESS"
    DENY = "DENY"  # fail-closed refusal, logged (not an error -- a deliberate refusal)
    ERROR = "ERROR"


class EntityRef(BaseModel):
    """What was acted on -- a *hash/lineage reference*, never raw PII (T1).

    Crypto-shredding (A6.4) tombstones a record by flipping :attr:`tombstoned`
    True; the ``content_hash`` stays (it is already a non-reversible digest), so
    the chain/tree is never rewritten -- only the (already absent) plaintext is
    declared erased.
    """

    model_config = ConfigDict(frozen=True)

    entity_id: str  # opaque identifier (already non-PII -- e.g. a UUID/lineage id)
    content_hash: HexDigest  # H(content); the raw content is NEVER stored (T1)
    tombstoned: bool = False  # crypto-shred marker; chain is NOT rewritten (A6.4/T1)


class AuditRecord(BaseModel):
    """One append-only PROV+FHIR audit event (``data-contracts.md`` §3).

    The record is frozen once constructed (append-only / immutable). Its canonical
    serialisation (:func:`canonical_bytes`) is the preimage of the leaf hash that
    both E5 candidates commit to.
    """

    model_config = ConfigDict(frozen=True)

    seq: int  # monotonic, gapless (enforced by the log structure, not here)
    # PROV-DM why-record (entity is a hash ref, agent/activity are opaque ids).
    entity: EntityRef
    activity: str  # what happened (opaque activity ref)
    agent: str  # who -- attested SPIFFE id (opaque string here)
    # FHIR security-record.
    outcome: AuditOutcome
    timestamp: datetime
    tenant_id: str  # PS tenant scoping (A8.2)

    @field_validator("seq")
    @classmethod
    def _seq_non_negative(cls, value: int) -> int:
        # fail-closed: sequence numbers are non-negative monotonic counters.
        if value < 0:
            raise ValueError("seq must be >= 0 (monotonic gapless counter)")
        return value

    def leaf(self) -> bytes:
        """Return this record's RFC 6962 leaf hash ``SHA-256(0x00 || canonical)``."""
        return leaf_hash(canonical_bytes(self))


def canonical_bytes(record: AuditRecord) -> bytes:
    """Serialise a record to its canonical, deterministic, injective byte form.

    The encoding sorts keys, strips all insignificant whitespace, normalises the
    timestamp to UTC ISO-8601, and is UTF-8 -- so an identical record always
    yields identical bytes (determinism, CLAUDE.md §3.11) and distinct records
    never collide on the encoding.

    Args:
        record: The (frozen) audit record to encode.

    Returns:
        The canonical UTF-8 byte serialisation.
    """
    # Normalise the timestamp to UTC so equal instants in different zones encode
    # identically (determinism). naive datetimes are treated as UTC.
    ts = record.timestamp
    ts = ts.replace(tzinfo=UTC) if ts.tzinfo is None else ts.astimezone(UTC)
    payload = {
        "seq": record.seq,
        "entity": {
            "entity_id": record.entity.entity_id,
            "content_hash": record.entity.content_hash,
            "tombstoned": record.entity.tombstoned,
        },
        "activity": record.activity,
        "agent": record.agent,
        "outcome": record.outcome.value,
        "timestamp": ts.isoformat(),
        "tenant_id": record.tenant_id,
    }
    # sort_keys + tight separators => a single canonical form per logical record.
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


class SignedTreeHead(BaseModel):
    """Gate-time Merkle commitment (``data-contracts.md`` §3; RFC 6962 §3.5 STH).

    Published at every gate (CLAUDE.md §3.13). ``tree_size`` is the number of
    leaves committed; ``root_hash`` is the Merkle Tree Hash over those leaves. A
    truncation that drops leaves committed before an STH is detectable because the
    truncated log cannot reproduce a consistency proof to this STH (the
    truncation-resistance defence, A6.2 src 05).
    """

    model_config = ConfigDict(frozen=True)

    tree_size: int  # number of leaves sealed (>= 0)
    root_hash: HexDigest  # MTH over the first ``tree_size`` leaves
    sealed_at: datetime

    @field_validator("tree_size")
    @classmethod
    def _size_non_negative(cls, value: int) -> int:
        # fail-closed: an STH cannot commit a negative number of leaves.
        if value < 0:
            raise ValueError("tree_size must be >= 0")
        return value


# Defensive constant re-export so downstream length checks cite one source.
_HASH_BYTES = HASH_BYTES
