"""RFC 6962 domain-separated SHA-256 hashing primitives (the shared crypto core).

What this does
--------------
Implements the two hashing rules that *both* tamper-evidence candidates in the E5
bake-off share, exactly as specified by **RFC 6962 (Certificate Transparency),
section 2.1**:

* **Leaf hash** ``MTH({d}) = SHA-256(0x00 || d)`` -- a single leaf is hashed with
  the ``0x00`` domain-separation prefix.
* **Interior node hash** ``MTH(D) = SHA-256(0x01 || left || right)`` -- two child
  hashes are combined with the ``0x01`` domain-separation prefix.

Why it exists / where it sits
-----------------------------
The ``0x00`` / ``0x01`` prefixes are *the* defence against second-preimage and
leaf/node confusion attacks: without them an attacker could present an interior
node's two-child preimage as if it were a leaf (or vice-versa) and forge a tree
that hashes to the same root. This is the "zero-error, mutation-tested detail"
called out in ``docs/research/A6-governance-and-auditability/SYNTHESIS.md``
(L1.A6.2) and ``data-contracts.md`` §3 (``prev_hash`` is an "RFC-6962 leaf,
0x00 domain-sep"). Candidate A (hash-chain) reuses :func:`leaf_hash` for its leaf
commitments; Candidate B (Merkle tree) uses both functions.

Citation
--------
RFC 6962, "Certificate Transparency", B. Laurie, A. Langley, E. Kasper, IETF,
June 2013, section 2.1 (Merkle Hash Trees). https://www.rfc-editor.org/rfc/rfc6962

Security / compliance invariants upheld
---------------------------------------
Domain separation is mandatory and non-negotiable (fail-closed: the prefixes are
hard-coded, never parameterised, so no caller can disable them). All hashes are
32-byte SHA-256 digests. Inputs are raw ``bytes``; callers are responsible for
canonical serialisation upstream (see :mod:`audit_record_contract`).
"""

from __future__ import annotations

import hashlib

__all__ = ["HASH_BYTES", "LEAF_PREFIX", "NODE_PREFIX", "leaf_hash", "node_hash"]

# RFC 6962 §2.1 domain-separation prefixes. These are part of the security
# contract -- changing either value silently breaks tamper-evidence, so they are
# module constants, never function arguments (fail-closed by construction).
LEAF_PREFIX = b"\x00"  # MTH({d}) = SHA-256(0x00 || d)   -- leaf domain separation
NODE_PREFIX = b"\x01"  # MTH(D)   = SHA-256(0x01 || l||r) -- interior-node sep
HASH_BYTES = 32  # SHA-256 output width, in bytes.


def leaf_hash(data: bytes) -> bytes:
    """Compute the RFC 6962 leaf hash ``SHA-256(0x00 || data)``.

    Args:
        data: The canonical byte serialisation of one log entry.

    Returns:
        The 32-byte leaf digest.
    """
    return hashlib.sha256(LEAF_PREFIX + data).digest()


def node_hash(left: bytes, right: bytes) -> bytes:
    """Compute the RFC 6962 interior-node hash ``SHA-256(0x01 || left || right)``.

    Args:
        left: The left child's 32-byte hash.
        right: The right child's 32-byte hash.

    Returns:
        The 32-byte interior-node digest.

    Raises:
        ValueError: If either child is not exactly :data:`HASH_BYTES` long
            (fail-closed: a wrong-width child means a programming error or a
            forged proof step, so we refuse rather than hash garbage).
    """
    # fail-closed: only well-formed 32-byte children may be combined.
    if len(left) != HASH_BYTES or len(right) != HASH_BYTES:
        raise ValueError(
            f"node_hash requires two {HASH_BYTES}-byte child hashes; "
            f"got {len(left)} and {len(right)}"
        )
    return hashlib.sha256(NODE_PREFIX + left + right).digest()
