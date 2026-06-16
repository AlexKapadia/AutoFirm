"""Synthetic audit-record factory for the E5 tests (no real PII -- CLAUDE.md §3.12).

Builds deterministic, valid :class:`AuditRecord` instances from a seq index so the
candidate-A/B tests share one fixture generator. Content hashes are synthetic
SHA-256 digests derived from the seq -- never real data.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from autofirm.audit.audit_record_contract import AuditOutcome, AuditRecord, EntityRef


def synthetic_digest(salt: str) -> str:
    """A synthetic 64-hex SHA-256 digest from a salt string (never real content)."""
    return hashlib.sha256(salt.encode("utf-8")).hexdigest()


def make_record(  # noqa: PLR0913  -- a keyword-only test factory; arity is intentional
    seq: int,
    *,
    activity: str = "delegate.task",
    outcome: AuditOutcome = AuditOutcome.SUCCESS,
    tenant_id: str = "tenant-A",
    tombstoned: bool = False,
    content_salt: str | None = None,
) -> AuditRecord:
    """Construct a valid synthetic audit record for a given seq."""
    salt = content_salt if content_salt is not None else f"content-{seq}"
    return AuditRecord(
        seq=seq,
        entity=EntityRef(
            entity_id=f"entity-{seq}",
            content_hash=synthetic_digest(salt),
            tombstoned=tombstoned,
        ),
        activity=activity,
        agent=f"spiffe://autofirm/agent/worker/session/{seq}",
        outcome=outcome,
        timestamp=datetime(2026, 1, 1, 0, 0, seq % 60, tzinfo=UTC),
        tenant_id=tenant_id,
    )
