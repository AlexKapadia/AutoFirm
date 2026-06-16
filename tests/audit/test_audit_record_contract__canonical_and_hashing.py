"""Adversarial + property tests for the audit record contract and RFC 6962 hashing.

Proves teeth (CLAUDE.md §3.6): the canonical encoding is deterministic and
injective, hashes-not-PII is enforced fail-closed, and the RFC 6962 domain-sep
prefixes are exactly 0x00 / 0x01 (a forged-equal-root attack must fail). Designed
to KILL mutants on the prefixes, the length checks, and the canonical field set.
"""

import hashlib
from datetime import timedelta, timezone

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from autofirm.audit.audit_record_contract import (
    AuditOutcome,
    EntityRef,
    SignedTreeHead,
    canonical_bytes,
)
from autofirm.audit.rfc6962_hashing import (
    HASH_BYTES,
    LEAF_PREFIX,
    NODE_PREFIX,
    leaf_hash,
    node_hash,
)
from tests.audit.synthetic_audit_records import make_record, synthetic_digest

# --------------------------- RFC 6962 prefixes ----------------------------- #


def test_leaf_prefix_is_exactly_0x00() -> None:
    assert LEAF_PREFIX == b"\x00"


def test_node_prefix_is_exactly_0x01() -> None:
    assert NODE_PREFIX == b"\x01"


def test_leaf_hash_matches_rfc6962_recurrence_by_hand() -> None:
    # MTH({d}) = SHA-256(0x00 || d). Known-answer against a direct computation.
    data = b"hello-leaf"
    assert leaf_hash(data) == hashlib.sha256(b"\x00" + data).digest()
    assert len(leaf_hash(data)) == HASH_BYTES


def test_node_hash_matches_rfc6962_recurrence_by_hand() -> None:
    left = leaf_hash(b"L")
    right = leaf_hash(b"R")
    assert node_hash(left, right) == hashlib.sha256(b"\x01" + left + right).digest()


def test_leaf_and_node_hash_of_same_bytes_differ_second_preimage_defence() -> None:
    # Domain separation: a 64-byte blob hashed as a leaf must NOT equal the same
    # blob split and hashed as a node -- this is the whole point of 0x00 vs 0x01.
    left = leaf_hash(b"a")
    right = leaf_hash(b"b")
    blob = left + right
    assert leaf_hash(blob) != node_hash(left, right)


def test_node_hash_rejects_wrong_width_children_fail_closed() -> None:
    good = leaf_hash(b"x")
    # The fail-closed error must NAME the control and report the offending widths
    # so an operator can act on it. Assert the EXACT message (start-anchored, full
    # string) so error-text mutants -- which prepend/append "XX" -- are killed.
    with pytest.raises(ValueError) as exc1:
        node_hash(good, b"too-short")  # 9-byte right child
    assert str(exc1.value) == "node_hash requires two 32-byte child hashes; got 32 and 9"
    with pytest.raises(ValueError) as exc2:
        node_hash(b"", good)  # empty left child
    assert str(exc2.value) == "node_hash requires two 32-byte child hashes; got 0 and 32"


# --------------------------- hashes-not-PII (T1) --------------------------- #


def test_entity_ref_refuses_non_hex_content_hash() -> None:
    # fail-closed: a record cannot be built carrying raw (non-digest) content.
    with pytest.raises(ValidationError):
        EntityRef(entity_id="e", content_hash="not-a-hash")


def test_entity_ref_refuses_wrong_length_digest() -> None:
    with pytest.raises(ValidationError):
        EntityRef(entity_id="e", content_hash="abcd")  # too short
    with pytest.raises(ValidationError):
        EntityRef(entity_id="e", content_hash="a" * 65)  # too long


def test_audit_record_refuses_negative_seq_fail_closed() -> None:
    with pytest.raises(ValidationError):
        make_record(-1)


def test_audit_record_is_frozen_append_only() -> None:
    rec = make_record(0)
    with pytest.raises(ValidationError):
        rec.seq = 5  # type: ignore[misc]


def test_signed_tree_head_refuses_negative_size() -> None:
    with pytest.raises(ValidationError):
        SignedTreeHead(
            tree_size=-1, root_hash=synthetic_digest("r"), sealed_at=make_record(0).timestamp
        )


# ----------------------- canonical serialisation --------------------------- #


def test_canonical_bytes_is_deterministic() -> None:
    a = canonical_bytes(make_record(7))
    b = canonical_bytes(make_record(7))
    assert a == b


def test_canonical_bytes_distinguishes_every_field() -> None:
    base = make_record(3)
    # Flipping ANY field must change the canonical encoding (injectivity), or a
    # tamper on that field would be invisible to the leaf hash.
    variants = [
        make_record(4),  # seq
        make_record(3, activity="other.activity"),
        make_record(3, outcome=AuditOutcome.DENY),
        make_record(3, tenant_id="tenant-B"),
        make_record(3, tombstoned=True),
        make_record(3, content_salt="different-content"),
    ]
    base_bytes = canonical_bytes(base)
    for v in variants:
        assert canonical_bytes(v) != base_bytes


def test_canonical_bytes_normalises_timezone() -> None:
    rec = make_record(2)
    # Same instant expressed in +05:00 must canonicalise identically (UTC norm).
    shifted = rec.model_copy(
        update={"timestamp": rec.timestamp.astimezone(timezone(timedelta(hours=5)))}
    )
    assert canonical_bytes(rec) == canonical_bytes(shifted)


@settings(max_examples=200)
@given(seq=st.integers(min_value=0, max_value=10_000), salt=st.text(min_size=0, max_size=40))
def test_property_canonical_injective_on_content(seq: int, salt: str) -> None:
    # Property: distinct content salts (=> distinct digests) yield distinct leaves;
    # identical inputs yield identical leaves. This is the load-bearing invariant
    # every chain/tree commitment relies on.
    r1 = make_record(seq, content_salt=salt)
    r2 = make_record(seq, content_salt=salt)
    assert r1.leaf() == r2.leaf()
    r3 = make_record(seq, content_salt=salt + "x")
    assert r1.leaf() != r3.leaf()
