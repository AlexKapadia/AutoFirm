"""Teeth-tests for the append-only in-memory ReleaseAuditSink.

Proves the sink records BOTH a SUCCESS (authorised) and a DENY (blocked) release,
preserves them in order, exposes no mutation path (append-only), and structurally
satisfies the ``ReleaseAuditSink`` seam the release gate writes through.
"""

from __future__ import annotations

from datetime import UTC, datetime

from autofirm.audit.audit_record_contract import AuditOutcome
from autofirm.e2e.in_memory_release_audit_sink import (
    InMemoryReleaseAuditSink,
    ReleaseAuditEntry,
)
from autofirm.output_review.release_decision_gate import ReleaseAuditSink

_AT = datetime(2026, 1, 1, tzinfo=UTC)
_OTHER = datetime(2027, 2, 2, tzinfo=UTC)


def test_records_a_success_entry_exactly() -> None:
    sink = InMemoryReleaseAuditSink()
    sink.record(artifact_ref="a@v1", outcome=AuditOutcome.SUCCESS, reason="green", decided_at=_AT)
    assert sink.entries() == (
        ReleaseAuditEntry(
            artifact_ref="a@v1", outcome=AuditOutcome.SUCCESS, reason="green", decided_at=_AT
        ),
    )


def test_records_success_and_deny_in_order() -> None:
    sink = InMemoryReleaseAuditSink()
    sink.record(artifact_ref="a@v1", outcome=AuditOutcome.SUCCESS, reason="ok", decided_at=_AT)
    sink.record(artifact_ref="b@v1", outcome=AuditOutcome.DENY, reason="blocked", decided_at=_OTHER)
    entries = sink.entries()
    assert len(entries) == 2
    assert [e.outcome for e in entries] == [AuditOutcome.SUCCESS, AuditOutcome.DENY]
    assert entries[1].artifact_ref == "b@v1"
    assert entries[1].decided_at == _OTHER


def test_entries_snapshot_cannot_mutate_backing_log() -> None:
    sink = InMemoryReleaseAuditSink()
    sink.record(artifact_ref="a@v1", outcome=AuditOutcome.SUCCESS, reason="ok", decided_at=_AT)
    snapshot = sink.entries()
    assert isinstance(snapshot, tuple)  # immutable copy, not the internal list
    # Appending more does not retroactively change the earlier snapshot.
    sink.record(artifact_ref="c@v1", outcome=AuditOutcome.DENY, reason="x", decided_at=_AT)
    assert len(snapshot) == 1
    assert len(sink.entries()) == 2


def test_entry_is_frozen() -> None:
    entry = ReleaseAuditEntry(
        artifact_ref="a@v1", outcome=AuditOutcome.SUCCESS, reason="ok", decided_at=_AT
    )
    try:
        entry.outcome = AuditOutcome.DENY  # type: ignore[misc]
    except (AttributeError, TypeError):
        return
    raise AssertionError("ReleaseAuditEntry must be frozen (append-only fact)")


def test_empty_sink_has_no_entries() -> None:
    assert InMemoryReleaseAuditSink().entries() == ()


def test_sink_satisfies_release_audit_sink_protocol() -> None:
    assert isinstance(InMemoryReleaseAuditSink(), ReleaseAuditSink)
