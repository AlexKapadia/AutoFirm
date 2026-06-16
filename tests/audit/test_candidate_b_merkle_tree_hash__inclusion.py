"""Adversarial + property + known-answer tests for Candidate B Merkle tree hash.

Proves teeth (CLAUDE.md §3.6) for the RFC 6962 section 2.1 / 2.1.1 implementation:

* Known-answer tests pinning the empty-tree, single-leaf, and small-tree roots to
  DIRECT ``hashlib`` computations of the RFC recurrence (an independent oracle, so
  a transcription bug in the implementation is caught).
* The largest-power-of-two split is verified against an independent reference and
  on exact boundaries (n, n+1 around powers of two).
* Inclusion proofs verify for EVERY leaf of trees across many sizes (property),
  proof size is O(log n) (property), and verification is fail-closed against
  tampered leaves, forged paths, wrong indices, and wrong roots.
"""

import hashlib

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from autofirm.audit.candidate_b_merkle_tree_hash import (
    largest_power_of_two_below,
    merkle_audit_path,
    merkle_tree_hash,
    verify_inclusion,
)
from autofirm.audit.rfc6962_hashing import leaf_hash, node_hash


def L(i: int) -> bytes:
    """Synthetic leaf input #i (raw bytes, not pre-hashed)."""
    return f"leaf-{i}".encode()


# ----------------------- largest power of two (split k) -------------------- #


@pytest.mark.parametrize(
    ("n", "expected_k"),
    [(2, 1), (3, 2), (4, 2), (5, 4), (7, 4), (8, 4), (9, 8), (16, 8), (17, 16), (1000, 512)],
)
def test_largest_power_of_two_below_known_values(n: int, expected_k: int) -> None:
    assert largest_power_of_two_below(n) == expected_k


def test_largest_power_of_two_below_refuses_small_n() -> None:
    # Exact-message asserts kill error-text mutants on this fail-closed guard.
    with pytest.raises(ValueError) as e1:
        largest_power_of_two_below(1)
    assert str(e1.value) == "largest_power_of_two_below requires n >= 2, got 1"
    with pytest.raises(ValueError) as e0:
        largest_power_of_two_below(0)
    assert str(e0.value) == "largest_power_of_two_below requires n >= 2, got 0"


@settings(max_examples=200)
@given(n=st.integers(min_value=2, max_value=100_000))
def test_property_split_is_largest_power_of_two_strictly_below(n: int) -> None:
    k = largest_power_of_two_below(n)
    # k is a power of two, k < n, and 2k >= n (so it's the LARGEST such).
    assert k & (k - 1) == 0
    assert k < n
    assert k * 2 >= n


# ----------------------- MTH known-answer (oracle) ------------------------- #


def test_mth_empty_tree_is_sha256_of_empty_string() -> None:
    # RFC 6962: MTH({}) = SHA-256().
    assert merkle_tree_hash([]) == hashlib.sha256(b"").digest()


def test_mth_single_leaf_is_leaf_hash() -> None:
    # RFC 6962: MTH({d0}) = SHA-256(0x00 || d0).
    assert merkle_tree_hash([L(0)]) == hashlib.sha256(b"\x00" + L(0)).digest()


def test_mth_two_leaves_by_hand() -> None:
    # n=2, k=1: MTH = node(leaf(d0), leaf(d1)).
    expected = node_hash(leaf_hash(L(0)), leaf_hash(L(1)))
    assert merkle_tree_hash([L(0), L(1)]) == expected


def test_mth_three_leaves_uses_left_full_right_partial_split() -> None:
    # n=3, k=2: MTH = node( node(leaf0,leaf1), leaf2 ).  NOT a balanced split.
    left = node_hash(leaf_hash(L(0)), leaf_hash(L(1)))
    right = leaf_hash(L(2))  # single leaf in the right subtree
    assert merkle_tree_hash([L(0), L(1), L(2)]) == node_hash(left, right)


def test_mth_four_leaves_is_balanced() -> None:
    # n=4, k=2: two balanced subtrees.
    left = node_hash(leaf_hash(L(0)), leaf_hash(L(1)))
    right = node_hash(leaf_hash(L(2)), leaf_hash(L(3)))
    assert merkle_tree_hash([L(i) for i in range(4)]) == node_hash(left, right)


def test_mth_five_leaves_split_4_then_1() -> None:
    # n=5, k=4: left is a full 4-leaf tree, right is a single leaf.
    leaves = [L(i) for i in range(5)]
    left = merkle_tree_hash(leaves[:4])
    right = leaf_hash(L(4))
    assert merkle_tree_hash(leaves) == node_hash(left, right)


def _reference_mth(leaves: list[bytes]) -> bytes:
    """Independent recursive RFC 6962 MTH oracle (separate code path)."""
    if not leaves:
        return hashlib.sha256(b"").digest()
    if len(leaves) == 1:
        return hashlib.sha256(b"\x00" + leaves[0]).digest()
    k = 1
    while k * 2 < len(leaves):
        k *= 2
    return hashlib.sha256(
        b"\x01" + _reference_mth(leaves[:k]) + _reference_mth(leaves[k:])
    ).digest()


@settings(max_examples=150)
@given(n=st.integers(min_value=0, max_value=130))
def test_property_mth_matches_independent_oracle(n: int) -> None:
    leaves = [L(i) for i in range(n)]
    assert merkle_tree_hash(leaves) == _reference_mth(leaves)


# ------------------------- inclusion proofs -------------------------------- #


def test_audit_path_single_leaf_is_empty() -> None:
    assert merkle_audit_path(0, [L(0)]) == []


def test_audit_path_refuses_out_of_range_index() -> None:
    with pytest.raises(ValueError) as e_over:
        merkle_audit_path(3, [L(0), L(1)])
    assert str(e_over.value) == "leaf index 3 out of range for tree size 2"
    with pytest.raises(ValueError) as e_neg:
        merkle_audit_path(-1, [L(0)])
    assert str(e_neg.value) == "leaf index -1 out of range for tree size 1"


def test_inclusion_verifies_for_known_two_leaf_tree() -> None:
    leaves = [L(0), L(1)]
    root = merkle_tree_hash(leaves)
    for m in range(2):
        path = merkle_audit_path(m, leaves)
        assert verify_inclusion(leaves[m], m, 2, path, root) is True


@settings(max_examples=120)
@given(n=st.integers(min_value=1, max_value=200))
def test_property_every_leaf_has_a_valid_inclusion_proof(n: int) -> None:
    leaves = [L(i) for i in range(n)]
    root = merkle_tree_hash(leaves)
    for m in range(n):
        path = merkle_audit_path(m, leaves)
        assert verify_inclusion(leaves[m], m, n, path, root) is True


@settings(max_examples=120)
@given(n=st.integers(min_value=1, max_value=4096))
def test_property_proof_size_is_logarithmic(n: int) -> None:
    # O(log n): an audit path never exceeds ceil(log2(n)) siblings.
    path = merkle_audit_path(0, [L(i) for i in range(n)])
    assert len(path) <= max(1, (n - 1).bit_length())


# ----------------------- fail-closed verification -------------------------- #


def test_verify_rejects_tampered_leaf() -> None:
    leaves = [L(i) for i in range(8)]
    root = merkle_tree_hash(leaves)
    path = merkle_audit_path(3, leaves)
    # Claim a DIFFERENT leaf input at index 3 -> root cannot be reconstructed.
    assert verify_inclusion(b"forged", 3, 8, path, root) is False


def test_verify_rejects_forged_path_sibling() -> None:
    leaves = [L(i) for i in range(8)]
    root = merkle_tree_hash(leaves)
    path = merkle_audit_path(5, leaves)
    forged = [b"\xff" * 32, *path[1:]]
    assert verify_inclusion(leaves[5], 5, 8, forged, root) is False


def test_verify_rejects_wrong_index() -> None:
    leaves = [L(i) for i in range(8)]
    root = merkle_tree_hash(leaves)
    path = merkle_audit_path(2, leaves)
    # Same leaf+path but claim index 6 -> folds the wrong way -> mismatch.
    assert verify_inclusion(leaves[2], 6, 8, path, root) is False


def test_verify_rejects_wrong_root() -> None:
    leaves = [L(i) for i in range(8)]
    path = merkle_audit_path(2, leaves)
    assert verify_inclusion(leaves[2], 2, 8, path, b"\x00" * 32) is False


def test_verify_rejects_out_of_range_claims() -> None:
    leaves = [L(i) for i in range(4)]
    root = merkle_tree_hash(leaves)
    assert verify_inclusion(leaves[0], 0, 0, [], root) is False  # size 0
    assert verify_inclusion(leaves[0], 5, 4, [], root) is False  # index >= size
    assert verify_inclusion(leaves[0], -1, 4, [], root) is False  # negative index


def test_verify_rejects_overlong_path() -> None:
    # A path with more siblings than the tree height is a forged proof.
    leaves = [L(0), L(1)]
    root = merkle_tree_hash(leaves)
    path = merkle_audit_path(0, leaves)
    assert verify_inclusion(leaves[0], 0, 2, [*path, b"\x00" * 32], root) is False
