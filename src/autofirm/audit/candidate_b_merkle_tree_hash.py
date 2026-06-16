"""Candidate B (part 1) -- the RFC 6962 Merkle Tree Hash and inclusion proofs.

What this does
--------------
Implements, verbatim from **RFC 6962 section 2.1**, the Merkle Tree Hash (MTH)
recurrence over an ordered list of leaf inputs, and the **audit path / inclusion
proof** (RFC 6962 section 2.1.1) plus its verifier.

RFC 6962 section 2.1 MTH recurrence (D[n] = {d(0),...,d(n-1)}):

    MTH({})  = SHA-256()                                   # empty tree
    MTH({d0}) = SHA-256(0x00 || d0)                         # single leaf
    For n > 1, let k be the largest power of two < n:
        MTH(D[n]) = SHA-256(0x01 || MTH(D[0:k]) || MTH(D[k:n]))

The split point ``k`` is the LARGEST power of two STRICTLY LESS THAN ``n`` -- this
gives RFC 6962's characteristic left-full, right-partial tree (NOT a balanced
floor(n/2) split), which is what makes inclusion AND consistency proofs O(log n).

RFC 6962 section 2.1.1 audit path PATH(m, D[n]):

    PATH(0, {d0}) = {}
    For n > 1, k = largest power of two < n:
        if m < k: PATH(m, D[n]) = PATH(m, D[0:k]) : MTH(D[k:n])
        else:     PATH(m, D[n]) = PATH(m-k, D[k:n]) : MTH(D[0:k])

Why it exists / where it sits
-----------------------------
This is the **reference-design** competitor in the E5 bake-off (``experiments.md``
E5: "(c) RFC-6962 Merkle / STH"). It gives O(log n) inclusion proofs and (with the
consistency proof in :mod:`candidate_b_consistency_proof`) detects truncation that
the Candidate-A chain cannot. The empty-tree / single-leaf base cases and the
largest-power-of-two split are the exact details a known-answer test must pin.

Citation
--------
RFC 6962, "Certificate Transparency", section 2.1 (Merkle Hash Trees) and section
2.1.1 (Merkle Audit Paths). https://www.rfc-editor.org/rfc/rfc6962

Security / compliance invariants upheld
---------------------------------------
* **Domain separation:** leaves via ``leaf_hash`` (0x00), interiors via
  ``node_hash`` (0x01) -- reuses the shared, fail-closed RFC 6962 primitives.
* **Fail-closed proof verification:** :func:`verify_inclusion` recomputes the root
  from the proof and compares; ANY mismatch (tampered leaf, forged path, wrong
  index/size) returns ``False`` -- the caller refuses on ``False``.
* **Bounds-checked indices:** out-of-range leaf indices / sizes are refused.
"""

from __future__ import annotations

import hashlib

from autofirm.audit.rfc6962_hashing import leaf_hash, node_hash

__all__ = [
    "largest_power_of_two_below",
    "merkle_audit_path",
    "merkle_tree_hash",
    "verify_inclusion",
]

# RFC 6962 only splits (sub)trees with more than one leaf; below this the
# recurrence uses its base cases instead.
_MIN_SPLITTABLE_TREE = 2


def largest_power_of_two_below(n: int) -> int:
    """Return the largest power of two STRICTLY less than ``n`` (RFC 6962 split k).

    For ``n >= 2`` this is ``2**floor(log2(n-1))``. Defined only for ``n >= 2``
    (the recurrence only splits trees with more than one leaf).

    Args:
        n: The (sub)tree leaf count; must be ``>= 2``.

    Returns:
        ``k`` = largest power of two with ``k < n``.

    Raises:
        ValueError: If ``n < 2`` (fail-closed: the split is undefined there).
    """
    if n < _MIN_SPLITTABLE_TREE:
        # fail-closed: callers must only split trees of size >= 2.
        raise ValueError(f"largest_power_of_two_below requires n >= 2, got {n}")
    k = 1
    # Double k while the NEXT double would still stay strictly below n.
    while k * 2 < n:
        k *= 2
    return k


def merkle_tree_hash(leaves: list[bytes]) -> bytes:
    """Compute MTH over ``leaves`` (each leaf is the raw entry input ``d(i)``).

    Implements the RFC 6962 section 2.1 recurrence exactly, including the empty
    tree (SHA-256 of the empty string) and single-leaf (``0x00`` prefixed) base
    cases.

    Args:
        leaves: Ordered list of leaf INPUTS ``d(0)..d(n-1)`` (raw bytes, not
            pre-hashed); MTH applies the ``0x00`` leaf prefix internally.

    Returns:
        The 32-byte Merkle Tree Hash root.
    """
    n = len(leaves)
    if n == 0:
        # RFC 6962: MTH({}) = SHA-256() -- the hash of the empty string.
        return hashlib.sha256(b"").digest()
    if n == 1:
        # RFC 6962: MTH({d0}) = SHA-256(0x00 || d0).
        return leaf_hash(leaves[0])
    k = largest_power_of_two_below(n)
    # RFC 6962: MTH(D[n]) = SHA-256(0x01 || MTH(D[0:k]) || MTH(D[k:n])).
    return node_hash(merkle_tree_hash(leaves[:k]), merkle_tree_hash(leaves[k:]))


def merkle_audit_path(m: int, leaves: list[bytes]) -> list[bytes]:
    """Compute the RFC 6962 section 2.1.1 audit path PATH(m, D[n]) for leaf ``m``.

    Args:
        m: Zero-based index of the leaf to prove (``0 <= m < n``).
        leaves: The ordered leaf inputs ``D[n]``.

    Returns:
        The ordered list of sibling node hashes from the leaf up to the root.

    Raises:
        ValueError: If ``m`` is out of range for ``leaves`` (fail-closed).
    """
    n = len(leaves)
    # fail-closed: cannot prove a leaf that isn't in the tree.
    if not 0 <= m < n:
        raise ValueError(f"leaf index {m} out of range for tree size {n}")
    if n == 1:
        # RFC 6962: PATH(0, {d0}) = {} (a single-leaf tree has an empty path).
        return []
    k = largest_power_of_two_below(n)
    if m < k:
        # Leaf is in the left subtree: path within left, then the right subtree root.
        return [*merkle_audit_path(m, leaves[:k]), merkle_tree_hash(leaves[k:])]
    # Leaf is in the right subtree: path within right, then the left subtree root.
    return [*merkle_audit_path(m - k, leaves[k:]), merkle_tree_hash(leaves[:k])]


def verify_inclusion(
    leaf_input: bytes,
    m: int,
    tree_size: int,
    audit_path: list[bytes],
    expected_root: bytes,
) -> bool:
    """Verify an RFC 6962 inclusion proof, fail-closed.

    Recomputes the root by folding the audit path into the leaf hash following the
    same left/right structure the path was generated with, and compares to
    ``expected_root``. Returns ``False`` on ANY inconsistency.

    Args:
        leaf_input: The raw leaf input ``d(m)`` whose inclusion is claimed.
        m: The claimed zero-based leaf index.
        tree_size: The claimed total number of leaves ``n``.
        audit_path: The sibling hashes from :func:`merkle_audit_path`.
        expected_root: The trusted root (e.g. from a SignedTreeHead) to match.

    Returns:
        ``True`` iff the proof reconstructs ``expected_root``; ``False`` otherwise.
    """
    # fail-closed: reject structurally impossible claims before touching crypto.
    if tree_size <= 0 or not 0 <= m < tree_size:
        return False
    # Derive the same left/right structure the path generator used (RFC 6962
    # section 2.1.1). Each decision is ("L", ...) when the proven node is the LEFT
    # child (sibling on the right) or ("R", ...) otherwise. The decisions are
    # produced top-down here, so we apply them in REVERSE to fold bottom-up --
    # matching merkle_audit_path, whose siblings are ordered leaf-first.
    decisions = _inclusion_fold_structure(m, tree_size)
    # A forged proof of the wrong length cannot match the tree height.
    if len(decisions) != len(audit_path):
        return False
    node = leaf_hash(leaf_input)
    # Both lists are leaf-first: merkle_audit_path appends the leaf-level sibling
    # first (innermost recursion), and _inclusion_fold_structure likewise places
    # the deepest decision first, so they zip directly.
    for sibling, is_left_child in zip(audit_path, decisions, strict=True):
        node = node_hash(node, sibling) if is_left_child else node_hash(sibling, node)
    return node == expected_root


def _inclusion_fold_structure(m: int, n: int) -> list[bool]:
    """Return the top-down left/right child flags for leaf ``m`` in a size-``n`` tree.

    Mirrors :func:`merkle_audit_path`'s recursion exactly so the verifier folds the
    siblings in the matching order. Each element is ``True`` when, at that level,
    the proven node is the LEFT child (its sibling -- a right-subtree root -- was
    appended) and ``False`` when it is the right child.
    """
    if n == 1:
        return []
    k = largest_power_of_two_below(n)
    if m < k:
        # Proven node sits in the left subtree -> it is the LEFT child here.
        return [*_inclusion_fold_structure(m, k), True]
    # Proven node sits in the right subtree -> it is the RIGHT child here.
    return [*_inclusion_fold_structure(m - k, n - k), False]
