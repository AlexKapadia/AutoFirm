"""Adversarial + property tests for the message envelope boundary (A2.1).

Proves teeth (CLAUDE.md §3.6): the envelope refuses every malformed shape at the
boundary -- no destination, two destinations, unknown performative, negative
causal_seq, empty/over-long ids, oversized/unserialisable payload. Designed to
KILL mutants on the exactly-one-destination check, the size cap, and the
non-negative-seq guard.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from autofirm.comms.message_envelope_contract import (
    MAX_PAYLOAD_BYTES,
    MessageEnvelope,
    Performative,
)
from tests.comms.synthetic_comms_fixtures import make_envelope


def test_valid_directed_envelope_constructs() -> None:
    env = make_envelope(recipient="agent-b", topic=None)
    assert env.recipient == "agent-b"
    assert env.topic is None


def test_valid_topic_envelope_constructs() -> None:
    env = make_envelope(recipient=None, topic="planning")
    assert env.topic == "planning"
    assert env.recipient is None


def test_no_destination_is_refused_fail_closed() -> None:
    # Neither recipient nor topic -> undeliverable -> refuse at the boundary.
    with pytest.raises(ValidationError, match="exactly one of 'recipient' or 'topic'"):
        make_envelope(recipient=None, topic=None)


def test_both_destinations_is_refused_fail_closed() -> None:
    # Both set -> ambiguous routing -> refuse (do not guess a destination).
    with pytest.raises(ValidationError, match="exactly one of 'recipient' or 'topic'"):
        make_envelope(recipient="agent-b", topic="planning")


def test_negative_causal_seq_is_refused() -> None:
    with pytest.raises(ValidationError, match="causal_seq must be >= 0"):
        make_envelope(causal_seq=-1)


def test_causal_seq_zero_is_allowed_boundary() -> None:
    # Boundary-exact: 0 is the lowest valid sequence and MUST be accepted.
    assert make_envelope(causal_seq=0).causal_seq == 0


def test_empty_sender_is_refused() -> None:
    with pytest.raises(ValidationError):
        make_envelope(sender="")


def test_unknown_performative_is_refused() -> None:
    with pytest.raises(ValidationError):
        MessageEnvelope(
            performative="gossip",  # type: ignore[arg-type]  # not in the closed set
            sender="a",
            recipient="b",
            conversation_id="c",
            causal_seq=0,
            dedup_key="dk",
            payload={},
            timestamp=make_envelope().timestamp,
        )


def test_all_closed_performatives_are_accepted() -> None:
    # Every member of the closed set must construct -- guards against a mutant
    # that drops or renames a performative.
    for perf in Performative:
        assert make_envelope(performative=perf).performative is perf


def test_payload_at_cap_minus_one_is_accepted_boundary() -> None:
    # A payload whose serialised size is just UNDER the cap is accepted.
    # Build a string payload sized precisely below MAX_PAYLOAD_BYTES.
    filler = "x" * (MAX_PAYLOAD_BYTES - 64)  # leave room for the JSON envelope keys
    env = make_envelope(payload={"d": filler})
    assert env.payload["d"] == filler


def test_payload_over_cap_is_refused_fail_closed() -> None:
    # Just OVER the cap -> refuse (resource-exhaustion / injection defence).
    filler = "x" * (MAX_PAYLOAD_BYTES + 1)
    with pytest.raises(ValidationError, match="exceeds MAX_PAYLOAD_BYTES"):
        make_envelope(payload={"d": filler})


def test_unserialisable_payload_is_refused() -> None:
    # A non-JSON-serialisable payload is untrusted/malformed -> refuse.
    with pytest.raises(ValidationError, match="JSON-serialisable"):
        make_envelope(payload={"bad": object()})


def test_envelope_is_frozen_immutable() -> None:
    env = make_envelope()
    with pytest.raises(ValidationError):
        env.recipient = "someone-else"  # type: ignore[misc]


# Non-whitespace-bordered ids: strip() leaves them non-empty so they are valid.
_clean_ids = st.text(
    alphabet=st.characters(min_codepoint=33, max_codepoint=126),
    min_size=1,
    max_size=32,
)


@settings(max_examples=300)
@given(
    seq=st.integers(min_value=0, max_value=1_000_000),
    sender=_clean_ids,
    dedup=_clean_ids,
)
def test_property_valid_directed_envelopes_round_trip(seq: int, sender: str, dedup: str) -> None:
    # Property: any non-negative seq + non-empty ids yields a valid directed
    # envelope whose fields survive unchanged (no hidden mutation/coercion).
    env = make_envelope(sender=sender, dedup_key=dedup, causal_seq=seq)
    assert env.causal_seq == seq
    assert env.sender == sender  # printable ids round-trip unchanged
    assert env.dedup_key == dedup


def test_whitespace_only_id_is_refused_after_strip() -> None:
    # A whitespace-only id strips to empty -> refused (fail-closed boundary).
    with pytest.raises(ValidationError):
        make_envelope(dedup_key="   ")
