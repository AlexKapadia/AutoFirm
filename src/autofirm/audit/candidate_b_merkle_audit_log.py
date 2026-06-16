"""Candidate B (part 3) -- the append-driven Merkle audit log with STH commitments.

What this does
--------------
Wraps the RFC 6962 MTH + inclusion + consistency primitives into the same
append-only log *interface* Candidate A exposes, so the E5 bake-off measures both
under identical conditions (``experiments.md`` E5). It maintains the ordered leaf
inputs, can :meth:`seal` a Signed-Tree-Head commitment at any gate, produces
inclusion proofs (O(log n)) and consistency proofs between two seals, and detects
truncation BEFORE a seal (the property the Candidate-A chain lacks).

Why it exists / where it sits
-----------------------------
A6.2 recommends "audit log = append-only events sealed in a history-tree / CT-style
Merkle log, publishing a Signed Tree Head at every gate". This is that log. The
verification cost asymmetry vs Candidate A (O(log n) proof vs O(n) full walk) is
what the bake-off measures.

Security / compliance invariants upheld
---------------------------------------
* **Append-only:** only :meth:`append`; gapless monotonic ``seq`` enforced
  fail-closed at the boundary.
* **Truncation-resistant:** :meth:`prove_consistency` against a prior STH refuses
  (returns ``False`` via the verifier) if entries committed before that STH were
  dropped or rewritten.
* **Crypto-shred (T1):** :meth:`tombstone` appends a new tombstone leaf; existing
  leaves and all prior STH roots are never rewritten.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from autofirm.audit.audit_record_contract import (
    AuditRecord,
    SignedTreeHead,
    canonical_bytes,
)
from autofirm.audit.candidate_b_consistency_proof import (
    merkle_consistency_proof,
    verify_consistency,
)
from autofirm.audit.candidate_b_merkle_tree_hash import (
    merkle_audit_path,
    merkle_tree_hash,
    verify_inclusion,
)

__all__ = ["MerkleAuditLog"]


@dataclass
class MerkleAuditLog:
    """An append-only RFC 6962 Merkle audit log over :class:`AuditRecord` leaves."""

    _records: list[AuditRecord] = field(default_factory=list)
    _leaf_inputs: list[bytes] = field(default_factory=list)

    def __len__(self) -> int:
        """Return the number of leaves currently in the log."""
        return len(self._records)

    def append(self, record: AuditRecord) -> None:
        """Append a record (its canonical bytes become the leaf input).

        Args:
            record: The audit record to append.

        Raises:
            ValueError: If ``record.seq`` is not the next gapless index.
        """
        expected = len(self._records)
        # fail-closed: gapless monotonic seq is a log invariant.
        if record.seq != expected:
            raise ValueError(f"non-gapless seq: expected {expected}, got {record.seq}")
        self._records.append(record)
        self._leaf_inputs.append(canonical_bytes(record))

    def root(self) -> bytes:
        """Return the current Merkle Tree Hash over all leaves."""
        return merkle_tree_hash(self._leaf_inputs)

    def seal(self, sealed_at: datetime) -> SignedTreeHead:
        """Produce a Signed Tree Head committing the current tree size + root."""
        return SignedTreeHead(
            tree_size=len(self._leaf_inputs),
            root_hash=self.root().hex(),
            sealed_at=sealed_at,
        )

    def inclusion_proof(self, m: int) -> list[bytes]:
        """Return the RFC 6962 audit path for leaf ``m`` (O(log n) size)."""
        return merkle_audit_path(m, self._leaf_inputs)

    def verify_inclusion(self, m: int, expected_root: bytes) -> bool:
        """Verify leaf ``m`` is included under ``expected_root`` (fail-closed)."""
        return verify_inclusion(
            self._leaf_inputs[m],
            m,
            len(self._leaf_inputs),
            self.inclusion_proof(m),
            expected_root,
        )

    def verify_inclusion_of_input(
        self, leaf_input: bytes, m: int, expected_root: bytes, audit_path: list[bytes]
    ) -> bool:
        """Verify an arbitrary ``leaf_input`` at index ``m`` against a root + path.

        Used to prove a *forged* leaf cannot be substituted at ``m``: a tampered
        input cannot reconstruct the sealed ``expected_root`` (fail-closed).
        """
        return verify_inclusion(
            leaf_input, m, len(self._leaf_inputs), audit_path, expected_root
        )

    def prove_consistency(self, old: SignedTreeHead) -> tuple[list[bytes], bool]:
        """Prove the current tree is append-only consistent with a prior STH.

        Returns:
            ``(proof, ok)`` where ``ok`` is the fail-closed verification result
            against the old STH's root and the current root. ``ok`` is ``False``
            if any pre-``old`` entry was truncated or rewritten.
        """
        n = len(self._leaf_inputs)
        m = old.tree_size
        # Equal size: nothing appended since the seal -> the old root must still
        # be reproducible from the current leaves (truncation/rewrite check).
        if m == n:
            ok = self.root().hex() == old.root_hash
            return [], ok
        if not 0 < m < n:
            return [], False
        proof = merkle_consistency_proof(m, self._leaf_inputs)
        ok = verify_consistency(m, n, bytes.fromhex(old.root_hash), self.root(), proof)
        return proof, ok

    def tombstone(self, seq_to_erase: int, tombstone_record: AuditRecord) -> None:
        """Crypto-shred content by appending a tombstone (T1/A6.4); no rewrite.

        Raises:
            ValueError: If ``seq_to_erase`` does not exist or the record is not a
                tombstone.
        """
        # fail-closed: erase only existing content, and the marker must be a real
        # tombstone so the erasure is itself auditable.
        if not 0 <= seq_to_erase < len(self._records):
            raise ValueError(f"cannot tombstone non-existent seq {seq_to_erase}")
        if not tombstone_record.entity.tombstoned:
            raise ValueError("tombstone_record.entity.tombstoned must be True")
        self.append(tombstone_record)

    def records(self) -> tuple[AuditRecord, ...]:
        """Return an immutable snapshot of the appended records."""
        return tuple(self._records)

    def leaf_inputs(self) -> list[bytes]:
        """Return a copy of the ordered leaf inputs (read-only access)."""
        return list(self._leaf_inputs)
