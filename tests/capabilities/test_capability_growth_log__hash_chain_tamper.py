"""Adversarial RFC-6962 hash-chain tamper tests for the capability growth log.

These are the security teeth (CLAUDE.md §3.6 / §5.6): every classic tamper on an
append-only log — REORDER, INSERT, DELETE, MODIFY — must be DETECTED and refused,
fail-closed. The tests forge each attack against a valid chain and assert it is
rejected at the event contract, the append guard, or the full-chain ``verify``.
None is tautological: each constructs a genuinely-tampered structure and asserts
the specific defence fires.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from autofirm.audit.rfc6962_hashing import HASH_BYTES
from autofirm.capabilities.capability_growth_log import CapabilityGrowthLog, GrowthLogError
from autofirm.capabilities.capability_registry_event import (
    GENESIS_PREV_HASH,
    CapabilityRegistryEvent,
)
from tests.capabilities.synthetic_capability_factory import (
    sealed_event,
    valid_descriptor,
)


def _three_event_log() -> CapabilityGrowthLog:
    """A valid, fully-chained 3-event log to mount tamper attacks against."""
    log = CapabilityGrowthLog()
    for i in range(3):
        event = sealed_event(
            log,
            descriptor=valid_descriptor(f"role-{i}", keywords=frozenset({f"kw{i}"})),
            org_event_ref=i,
        )
        log = log.append(event)
    return log


@pytest.mark.security
def test_genesis_event_chains_over_the_all_zero_anchor() -> None:
    event = sealed_event(CapabilityGrowthLog())
    assert event.seq == 0
    assert event.prev_hash == GENESIS_PREV_HASH  # first event anchors at genesis


@pytest.mark.security
def test_modifying_a_field_is_refused_at_the_deserialisation_boundary() -> None:
    # The real ingress for a forged event is deserialisation (model_validate over a
    # dict from disk/wire). A record whose content no longer matches its committed
    # record_hash is refused there — a tampered event cannot enter the system. (Note:
    # model_copy(update=...) bypasses validators by Pydantic design, so it is NOT a
    # trust boundary; the boundaries that matter — model_validate and log verify —
    # both reject it, asserted here and below.)
    good = sealed_event(CapabilityGrowthLog())
    forged = good.model_dump()
    forged["rationale"] = "a different reason"  # content edited, record_hash stale
    with pytest.raises(ValidationError, match="tamper-evident"):
        CapabilityRegistryEvent.model_validate(forged)


@pytest.mark.security
def test_modifying_or_reordering_a_committed_event_fails_verification() -> None:
    log = _three_event_log()
    events = list(log.events())
    # Editing a field in place (via model_copy, which skips validators) yields an
    # event whose stored record_hash no longer matches its content; a log built from
    # the edited chain fails full-chain verification at construction (fail-closed).
    edited = events[1].model_copy(update={"rationale": "tampered reason"})
    with pytest.raises(GrowthLogError, match="verification"):
        CapabilityGrowthLog((events[0], edited, events[2]))
    # Reordering two valid events also fails verification (seq != position / chain).
    with pytest.raises(GrowthLogError, match="verification"):
        CapabilityGrowthLog((events[0], events[2], events[1]))


@pytest.mark.security
def test_deleting_an_event_breaks_the_chain() -> None:
    log = _three_event_log()
    events = list(log.events())
    # Drop the middle event: event[2].prev_hash no longer matches event[0]'s tip,
    # and its seq (2) no longer equals its new position (1) -> verify refuses.
    with pytest.raises(GrowthLogError, match="verification"):
        CapabilityGrowthLog((events[0], events[2]))


@pytest.mark.security
def test_inserting_a_foreign_event_is_refused_on_append() -> None:
    log = _three_event_log()
    # An event sealed against a DIFFERENT (empty) log has prev_hash == genesis and
    # seq 0; appending it onto a 3-event log violates BOTH the seq and chain guards.
    foreign = sealed_event(CapabilityGrowthLog(), org_event_ref=99)
    with pytest.raises(GrowthLogError, match="non-consecutive seq"):
        log.append(foreign)


@pytest.mark.security
def test_append_with_correct_seq_but_wrong_prev_hash_is_refused() -> None:
    log = _three_event_log()
    # Build a DECOY 3-event log with different descriptors, so its tip hash differs
    # from `log`'s tip. An event sealed against the decoy has the RIGHT next seq (3)
    # but a prev_hash that does not match `log`'s tip -> isolates the chain guard.
    decoy = CapabilityGrowthLog()
    for i in range(3):
        decoy = decoy.append(
            sealed_event(
                decoy,
                descriptor=valid_descriptor(f"d{i}", keywords=frozenset({f"d{i}"})),
                org_event_ref=i,
            )
        )
    mismatched = sealed_event(
        decoy,
        descriptor=valid_descriptor("role-3", keywords=frozenset({"kw3"})),
        org_event_ref=3,
    )
    assert mismatched.seq == log.next_seq  # right seq...
    assert mismatched.prev_hash != log.tip_hash  # ...wrong chain link
    with pytest.raises(GrowthLogError, match="broken chain"):
        log.append(mismatched)


@pytest.mark.unit
def test_wrong_width_hash_is_refused_at_the_deserialisation_boundary() -> None:
    good = sealed_event(CapabilityGrowthLog())
    forged = good.model_dump()
    forged["prev_hash"] = b"\x00" * (HASH_BYTES - 1)  # truncated chain link
    with pytest.raises(ValidationError, match=f"{HASH_BYTES} bytes"):
        CapabilityRegistryEvent.model_validate(forged)


@pytest.mark.unit
def test_empty_log_verifies_and_tip_is_genesis() -> None:
    empty = CapabilityGrowthLog()
    assert empty.verify() is True
    assert empty.tip_hash == GENESIS_PREV_HASH
    assert empty.next_seq == 0
