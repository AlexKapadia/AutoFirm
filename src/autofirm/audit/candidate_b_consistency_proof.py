"""Candidate B (part 2) -- the RFC 6962 section 2.1.2 consistency proof.

What this does
--------------
Implements, verbatim from **RFC 6962 section 2.1.2**, the Merkle consistency proof
PROOF(m, D[n]) -- the proof that the size-``m`` tree (an older Signed Tree Head) is
a *prefix* of the size-``n`` tree (a newer STH), i.e. the log was only **appended
to**, never rewritten or truncated. This is the property the Candidate-A hash-chain
*cannot* give (truncation is silent there); it is the reason the bake-off exists.

RFC 6962 section 2.1.2, given ``0 < m < n`` (proof that first ``m`` entries are a
prefix of ``D[n]``)::

    PROOF(m, D[n]) = SUBPROOF(m, D[n], true)

    SUBPROOF(m, D[m], true)  = {}                 # the whole subtree IS the old tree
    SUBPROOF(m, D[m], false) = { MTH(D[m]) }       # commit the old subtree root
    For m < n, k = largest power of two < n:
        if m <= k:
            SUBPROOF(m, D[n], b) = SUBPROOF(m, D[0:k], b)        : MTH(D[k:n])
        else:  # m > k
            SUBPROOF(m, D[n], b) = SUBPROOF(m-k, D[k:n], false)  : MTH(D[0:k])

The boolean ``b`` tracks whether the current subtree's old-tree boundary is on a
"complete subtree" edge (``true`` => the old root is implied, omitted) or must be
explicitly supplied (``false``).

Why it exists / where it sits
-----------------------------
This discharges E5 milestone M3 and the **truncation-resistance** requirement
(``experiments.md`` E5 metric: "tamper-detection completeness"; A6.2 src 05 names
truncation + delayed-detection). A verifier holding an old STH ``(m, old_root)``
and a new STH ``(n, new_root)`` accepts only if the consistency proof reconstructs
BOTH roots -- so dropping or rewriting any of the first ``m`` entries is detected.

Citation
--------
RFC 6962, "Certificate Transparency", section 2.1.2 (Merkle Consistency Proofs).
https://www.rfc-editor.org/rfc/rfc6962

Security / compliance invariants upheld
---------------------------------------
* **Fail-closed verification:** :func:`verify_consistency` returns ``False`` on ANY
  inconsistency -- a truncated/rewritten log, a forged proof, or roots that do not
  match. The caller refuses on ``False``.
* **Bounds-checked:** sizes must satisfy ``0 < m < n`` (the only case a proof is
  defined for; equal sizes need no proof, and ``m > n`` is nonsensical).
"""

from __future__ import annotations

from autofirm.audit.candidate_b_merkle_tree_hash import (
    largest_power_of_two_below,
    merkle_tree_hash,
)
from autofirm.audit.rfc6962_hashing import HASH_BYTES, node_hash

__all__ = ["merkle_consistency_proof", "verify_consistency"]


def merkle_consistency_proof(m: int, leaves: list[bytes]) -> list[bytes]:
    """Compute PROOF(m, D[n]) per RFC 6962 section 2.1.2.

    Args:
        m: The size of the older tree (a prefix length); ``0 < m < n``.
        leaves: The full ordered leaf inputs ``D[n]`` of the newer tree.

    Returns:
        The ordered list of node hashes constituting the consistency proof.

    Raises:
        ValueError: If ``m`` and ``len(leaves)`` do not satisfy ``0 < m < n``
            (fail-closed: a proof is only defined for a strict, non-empty prefix).
    """
    n = len(leaves)
    # fail-closed: a consistency proof is defined only for 0 < m < n.
    if not 0 < m < n:
        raise ValueError(f"consistency proof requires 0 < m < n; got m={m}, n={n}")
    # PROOF(m, D[n]) = SUBPROOF(m, D[n], true).
    return _subproof(m, leaves, True)


def _subproof(m: int, leaves: list[bytes], b: bool) -> list[bytes]:
    """RFC 6962 section 2.1.2 SUBPROOF(m, D[n], b)."""
    n = len(leaves)
    if m == n:
        # SUBPROOF(m, D[m], true) = {}; SUBPROOF(m, D[m], false) = {MTH(D[m])}.
        return [] if b else [merkle_tree_hash(leaves)]
    k = largest_power_of_two_below(n)
    if m <= k:
        # Old boundary is within the left subtree; commit the right subtree root.
        return [*_subproof(m, leaves[:k], b), merkle_tree_hash(leaves[k:])]
    # Old boundary is within the right subtree; the left subtree is fully in the
    # old tree, so its root is committed and b becomes false on the recursion.
    return [*_subproof(m - k, leaves[k:], False), merkle_tree_hash(leaves[:k])]


def verify_consistency(
    m: int,
    n: int,
    old_root: bytes,
    new_root: bytes,
    proof: list[bytes],
) -> bool:
    """Verify an RFC 6962 consistency proof, fail-closed.

    Reconstructs both the old (size ``m``) and new (size ``n``) roots from the
    proof following the RFC 6962 verification algorithm, and accepts only if BOTH
    match. A truncation or rewrite of any of the first ``m`` entries makes the
    reconstruction fail.

    Args:
        m: Older tree size.
        n: Newer tree size.
        old_root: The trusted root of the size-``m`` tree (old STH).
        new_root: The trusted root of the size-``n`` tree (new STH).
        proof: The consistency proof from :func:`merkle_consistency_proof`.

    Returns:
        ``True`` iff the proof reconstructs both roots; ``False`` otherwise.
    """
    # fail-closed: only 0 < m < n is provable. (m == n needs no proof; reject so a
    # forged "equal" claim cannot slip an empty proof past the verifier.)
    if not 0 < m < n:
        return False
    if any(len(h) != HASH_BYTES for h in proof):
        return False  # malformed proof node -> refuse

    # RFC 6962 verification (the standard algorithm derived from section 2.1.2).
    # If m is an exact power of two, the old root is a complete subtree and is NOT
    # in the proof, so it is prepended; otherwise the first proof node IS the old
    # subtree seed.
    # m a power of two => old root is a complete subtree, omitted from the proof.
    path = [old_root, *proof] if m & (m - 1) == 0 else list(proof)
    if not path:
        return False

    # `node` (old-side) and `new_node` (new-side) are folded in lockstep up the
    # tree. fn/sn track the running subtree boundaries; the same proof nodes serve
    # both reconstructions, differing only when the old boundary sits inside a
    # subtree (then the old side does not consume a right sibling).
    fn, sn = m - 1, n - 1
    while fn % 2 == 1:  # shift past trailing complete-subtree levels
        fn >>= 1
        sn >>= 1
    node = path[0]
    new_node = path[0]
    for sibling in path[1:]:
        if sn == 0:
            return False  # more proof nodes than the tree height -> forged
        if fn % 2 == 1 or fn == sn:
            # Old node is a right child (or the boundaries coincide): sibling is on
            # the left for BOTH reconstructions.
            node = node_hash(sibling, node)
            new_node = node_hash(sibling, new_node)
            while fn % 2 == 0 and fn != 0:
                fn >>= 1
                sn >>= 1
        else:
            # Old node is a left child: only the NEW reconstruction absorbs the
            # right sibling; the old root has already fully formed.
            new_node = node_hash(new_node, sibling)
        fn >>= 1
        sn >>= 1
    # Both running boundaries must have collapsed and both roots must match.
    return sn == 0 and node == old_root and new_node == new_root
