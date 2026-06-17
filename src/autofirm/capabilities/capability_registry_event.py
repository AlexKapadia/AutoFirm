"""The append-only, hash-chained growth event recording one capability change.

What this does
--------------
Defines :class:`CapabilityRegistryEvent` — one immutable record in the capability
growth log — and its **canonical byte serialisation** (the deterministic, injective
encoding fed to :func:`autofirm.audit.rfc6962_hashing.leaf_hash`). Each event
carries a gapless ``seq``, the change ``kind``, the POST-event ``descriptor``, the
managing role that ``triggered`` it, the link back to the org event, a PII-free
``rationale``, an injected ``occurred_at`` instant, and the RFC-6962 chain links
``prev_hash`` / ``record_hash`` that make tampering detectable.

Why it exists / where it sits
-----------------------------
Per ``docs/architecture/data-contracts.md`` §9, the growth log is the source of
truth for *showing the evolution* of the org's capabilities. The org's existing
:class:`~autofirm.org.org_lifecycle_events.OrgAuditTrail` is gapless but NOT
hash-chained; this event adds the RFC-6962 chaining (research finding: B4 +
E5 bake-off, ``docs/research/B4-capability-registries/``) so the growth log is
*tamper-evident*, not merely ordered. It reuses :func:`leaf_hash` from
``autofirm.audit`` — the chaining primitive is written once and shared.

Security / compliance invariants upheld
---------------------------------------
* **Tamper-evidence (RFC-6962, fail-closed):** ``record_hash`` MUST equal the
  canonical leaf hash of this event's content chained over ``prev_hash``; a
  mismatch is refused at construction, so a forged/edited event cannot be built.
* **Single-writer authorship (least-privilege):** ``triggered_by`` is the managing
  role whose lifecycle action caused the growth — never a self-grant; the
  projection enforces this is a managing role, the event records it for audit.
* **PII-free rationale (audited):** an empty rationale is refused; the rationale is
  the deterministic 'why' carried from the causing org event.
* **Gapless seq:** ``seq`` is non-negative; the growth log enforces it is exactly
  the next position (gapless), so a dropped/duplicated event is detectable.
* **Immutable:** frozen once built; the log only ever appends new events.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from autofirm.audit.rfc6962_hashing import HASH_BYTES, leaf_hash
from autofirm.capabilities.capability_descriptor import CapabilityDescriptor
from autofirm.org.org_identifiers import RoleId

__all__ = [
    "GENESIS_PREV_HASH",
    "CapabilityRegistryEvent",
    "RegistryEventKind",
    "canonical_event_bytes",
    "compute_record_hash",
]

# The closed set of growth kinds (data-contracts.md §9). A capability is ADDED on a
# hire/auto-create, PROMOTED on a maturity advance, DEPRECATED on a fire, and
# RESCOPED when its owning role's charter changes its surface.
RegistryEventKind = Literal[
    "CAPABILITY_ADDED",
    "CAPABILITY_PROMOTED",
    "CAPABILITY_DEPRECATED",
    "CAPABILITY_RESCOPED",
]

# The chain anchor for the FIRST event (seq 0): an all-zero 32-byte hash. A genuine
# previous-event hash is never all-zero (it is a SHA-256 digest), so the genesis
# link is unambiguous and cannot be confused with a real predecessor.
GENESIS_PREV_HASH = b"\x00" * HASH_BYTES


def canonical_event_bytes(  # noqa: PLR0913 -- the event preimage is intrinsically
    # wide; every field is a distinct keyword-only commitment input (no dict).
    *,
    seq: int,
    kind: RegistryEventKind,
    descriptor: CapabilityDescriptor,
    triggered_by: RoleId,
    org_event_ref: int,
    rationale: str,
    occurred_at: datetime,
    prev_hash: bytes,
) -> bytes:
    """Serialise an event's *content* to canonical, deterministic, injective bytes.

    Mirrors :func:`autofirm.audit.audit_record_contract.canonical_bytes`: sorted
    keys, tight separators, UTC-normalised timestamp, sorted keyword set, and the
    ``prev_hash`` as hex — so the same logical event always yields identical bytes
    (determinism, §3.11) and two distinct events never collide on the encoding. The
    ``record_hash`` is intentionally NOT part of the preimage (it is the OUTPUT).
    """
    occurred = occurred_at if occurred_at.tzinfo is not None else occurred_at.replace(tzinfo=UTC)
    occurred = occurred.astimezone(UTC)
    payload = {
        "seq": seq,
        "kind": kind,
        "triggered_by": str(triggered_by),
        "org_event_ref": org_event_ref,
        "rationale": rationale,
        "occurred_at": occurred.isoformat(),
        "prev_hash": prev_hash.hex(),
        "descriptor": {
            "capability_id": str(descriptor.capability_id),
            "name": descriptor.name,
            # sorted so set ordering cannot change the encoding (determinism).
            "keywords": sorted(descriptor.keywords),
            "owning_role_id": str(descriptor.owning_role_id),
            "required_clearance": descriptor.required_clearance,
            "maturity": descriptor.maturity,
            "provenance": {
                "kind": descriptor.provenance.kind,
                "org_event_seq": descriptor.provenance.org_event_seq,
                "rationale": descriptor.provenance.rationale,
            },
        },
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def compute_record_hash(  # noqa: PLR0913 -- mirrors canonical_event_bytes's wide,
    # keyword-only commitment surface (one arg per committed field).
    *,
    seq: int,
    kind: RegistryEventKind,
    descriptor: CapabilityDescriptor,
    triggered_by: RoleId,
    org_event_ref: int,
    rationale: str,
    occurred_at: datetime,
    prev_hash: bytes,
) -> bytes:
    """Compute the RFC-6962 leaf hash chaining this event's content over ``prev_hash``.

    ``prev_hash`` is folded into the canonical preimage (above), so the hash
    commits to BOTH this event and its position in the chain — editing any earlier
    event changes every later ``record_hash`` (the tamper-evidence property).
    """
    return leaf_hash(
        canonical_event_bytes(
            seq=seq,
            kind=kind,
            descriptor=descriptor,
            triggered_by=triggered_by,
            org_event_ref=org_event_ref,
            rationale=rationale,
            occurred_at=occurred_at,
            prev_hash=prev_hash,
        )
    )


class CapabilityRegistryEvent(BaseModel):
    """One immutable, hash-chained capability-growth record (data-contracts.md §9).

    Construction is fail-closed: the ``record_hash`` MUST equal the canonical leaf
    hash of this event chained over ``prev_hash``, so a tampered or forged event
    cannot be constructed. Hashes are stored as bytes (32-byte SHA-256 digests).
    """

    model_config = ConfigDict(frozen=True)

    seq: int  # monotonic, GAPLESS (the log enforces it == next position)
    kind: RegistryEventKind  # the growth kind (closed set)
    descriptor: CapabilityDescriptor  # the POST-event state of the capability
    triggered_by: RoleId  # the managing role whose action caused growth (audited)
    org_event_ref: int  # gapless seq of the causing org-lifecycle event (the link)
    rationale: str  # PII-free 'why' (audited); refused if empty
    occurred_at: datetime  # injected clock (deterministic)
    prev_hash: bytes  # RFC-6962 chain link to the previous event (or genesis)
    record_hash: bytes  # H(canonical(this event)) chained over prev_hash

    @field_validator("seq", "org_event_ref")
    @classmethod
    def _non_negative(cls, value: int) -> int:
        # fail-closed: seqs and org-event refs are non-negative gapless counters.
        if value < 0:
            raise ValueError("seq and org_event_ref must be >= 0")
        return value

    @field_validator("rationale")
    @classmethod
    def _rationale_non_empty(cls, value: str) -> str:
        # fail-closed: a growth event with no stated reason is not auditable.
        if not value.strip():
            raise ValueError("event rationale must be non-empty (audited 'why')")
        return value

    @field_validator("prev_hash", "record_hash")
    @classmethod
    def _hash_width(cls, value: bytes) -> bytes:
        # fail-closed: a wrong-width hash is a malformed chain link or forged proof
        # step — refuse rather than chain over garbage (mirrors node_hash's check).
        if len(value) != HASH_BYTES:
            raise ValueError(f"hash must be exactly {HASH_BYTES} bytes, got {len(value)}")
        return value

    @model_validator(mode="after")
    def _record_hash_matches(self) -> CapabilityRegistryEvent:
        # fail-closed tamper-evidence: the stored record_hash MUST equal the
        # recomputed canonical leaf hash chained over prev_hash. Any edit to any
        # field changes the canonical preimage and breaks this equality, so a
        # forged/edited event is refused at construction (§5.6).
        expected = compute_record_hash(
            seq=self.seq,
            kind=self.kind,
            descriptor=self.descriptor,
            triggered_by=self.triggered_by,
            org_event_ref=self.org_event_ref,
            rationale=self.rationale,
            occurred_at=self.occurred_at,
            prev_hash=self.prev_hash,
        )
        if self.record_hash != expected:
            raise ValueError("record_hash does not match canonical content (tamper-evident)")
        return self
