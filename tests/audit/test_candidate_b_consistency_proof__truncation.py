"""Adversarial + property tests for the RFC 6962 section 2.1.2 consistency proof.

Proves teeth (CLAUDE.md §3.6): a consistency proof between any prefix size m and
full size n verifies against the genuine old/new roots (property, over many
sizes), and is fail-closed against truncation, prefix rewrite, forged proof nodes,
swapped roots, and out-of-range sizes. Small hand-checked trees pin the base cases
(no open-ended exploration -- the proof is generated and checked against the MTH
oracle, the RFC's documented test method).
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from autofirm.audit.candidate_b_consistency_proof import (
    merkle_consistency_proof,
    verify_consistency,
)
from autofirm.audit.candidate_b_merkle_tree_hash import merkle_tree_hash
from autofirm.audit.rfc6962_hashing import HASH_BYTES


def L(i: int) -> bytes:
    """Synthetic leaf input #i."""
    return f"leaf-{i}".encode()


def leaves(n: int) -> list[bytes]:
    return [L(i) for i in range(n)]


# ----------------------------- defined domain ------------------------------ #


def test_proof_refuses_non_strict_prefix() -> None:
    with pytest.raises(ValueError):
        merkle_consistency_proof(0, leaves(4))  # m == 0
    with pytest.raises(ValueError):
        merkle_consistency_proof(4, leaves(4))  # m == n
    with pytest.raises(ValueError):
        merkle_consistency_proof(5, leaves(4))  # m > n


def test_verify_refuses_non_strict_prefix() -> None:
    full = leaves(4)
    new_root = merkle_tree_hash(full)
    old_root = merkle_tree_hash(full[:2])
    # m == n and m == 0 must be rejected (no empty-proof bypass).
    assert verify_consistency(4, 4, new_root, new_root, []) is False
    assert verify_consistency(0, 4, old_root, new_root, []) is False


# --------------------- hand-checked small cases ---------------------------- #


def test_consistency_m1_n2_verifies() -> None:
    full = leaves(2)
    proof = merkle_consistency_proof(1, full)
    assert verify_consistency(
        1, 2, merkle_tree_hash(full[:1]), merkle_tree_hash(full), proof
    )


def test_consistency_m2_n3_verifies() -> None:
    full = leaves(3)
    proof = merkle_consistency_proof(2, full)
    assert verify_consistency(
        2, 3, merkle_tree_hash(full[:2]), merkle_tree_hash(full), proof
    )


def test_consistency_m3_n7_verifies() -> None:
    full = leaves(7)
    proof = merkle_consistency_proof(3, full)
    assert verify_consistency(
        3, 7, merkle_tree_hash(full[:3]), merkle_tree_hash(full), proof
    )


# ------------------------------- properties -------------------------------- #


@settings(max_examples=300)
@given(data=st.data())
def test_property_consistency_holds_for_every_prefix(data: st.DataObject) -> None:
    # For ANY 0 < m < n (n up to 256), the proof verifies against the true roots.
    n = data.draw(st.integers(min_value=2, max_value=256))
    m = data.draw(st.integers(min_value=1, max_value=n - 1))
    full = leaves(n)
    proof = merkle_consistency_proof(m, full)
    old_root = merkle_tree_hash(full[:m])
    new_root = merkle_tree_hash(full)
    assert verify_consistency(m, n, old_root, new_root, proof) is True


@settings(max_examples=200)
@given(data=st.data())
def test_property_proof_size_is_logarithmic(data: st.DataObject) -> None:
    n = data.draw(st.integers(min_value=2, max_value=4096))
    m = data.draw(st.integers(min_value=1, max_value=n - 1))
    proof = merkle_consistency_proof(m, leaves(n))
    # O(log n): never more than ceil(log2(n)) + 1 nodes.
    assert len(proof) <= n.bit_length() + 1


# --------------------------- fail-closed attacks --------------------------- #


@settings(max_examples=150)
@given(data=st.data())
def test_property_prefix_rewrite_is_detected(data: st.DataObject) -> None:
    # Rewrite an entry inside the first m leaves -> old_root no longer matches the
    # prefix the proof commits to -> rejected. (delayed-detection defence.)
    n = data.draw(st.integers(min_value=3, max_value=128))
    m = data.draw(st.integers(min_value=2, max_value=n - 1))
    full = leaves(n)
    proof = merkle_consistency_proof(m, full)
    new_root = merkle_tree_hash(full)
    # Forge the old tree: flip one of its first m entries.
    forged_prefix = list(full[:m])
    forged_prefix[m // 2] = b"rewritten"
    forged_old_root = merkle_tree_hash(forged_prefix)
    assert verify_consistency(m, n, forged_old_root, new_root, proof) is False


@settings(max_examples=150)
@given(data=st.data())
def test_property_truncation_is_detected(data: st.DataObject) -> None:
    # An attacker presents a SHORTER new tree (truncated suffix) but the real old
    # STH. The consistency proof to the genuine new root cannot validate against a
    # truncated new root -> rejected. This is the gap Candidate A could not close.
    n = data.draw(st.integers(min_value=4, max_value=128))
    m = data.draw(st.integers(min_value=1, max_value=n - 2))
    full = leaves(n)
    proof = merkle_consistency_proof(m, full)
    old_root = merkle_tree_hash(full[:m])
    truncated_root = merkle_tree_hash(full[: n - 1])  # dropped the last entry
    assert verify_consistency(m, n, old_root, truncated_root, proof) is False


def test_forged_proof_node_rejected() -> None:
    full = leaves(7)
    proof = merkle_consistency_proof(3, full)
    forged = [b"\xff" * HASH_BYTES, *proof[1:]] if proof else [b"\xff" * HASH_BYTES]
    assert verify_consistency(
        3, 7, merkle_tree_hash(full[:3]), merkle_tree_hash(full), forged
    ) is False


def test_malformed_proof_node_width_rejected() -> None:
    full = leaves(5)
    proof = merkle_consistency_proof(2, full)
    bad = [*proof, b"short"]
    assert verify_consistency(
        2, 5, merkle_tree_hash(full[:2]), merkle_tree_hash(full), bad
    ) is False


def test_swapped_roots_rejected() -> None:
    full = leaves(6)
    proof = merkle_consistency_proof(2, full)
    old_root = merkle_tree_hash(full[:2])
    new_root = merkle_tree_hash(full)
    # Pass new_root where old_root is expected and vice-versa.
    assert verify_consistency(2, 6, new_root, old_root, proof) is False
