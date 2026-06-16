"""Candidate A -- the plain forward hash-chain audit log (E5 baseline).

What this does
--------------
Implements the founding tamper-evidence primitive (Schneier-Kelsey /
Haber-Stornetta linking, A6.2 src 03): an append-only log where each entry stores
the hash of the previous entry, so any mid-log edit breaks every subsequent link.

The chain link for entry *i* is::

    link[i] = SHA-256(0x01 || prev_link || leaf_hash(record[i]))

where ``prev_link`` is ``link[i-1]`` (or a fixed 32-byte genesis seed for *i = 0*),
``leaf_hash`` is the RFC 6962 ``SHA-256(0x00 || canonical(record))`` leaf, and the
``0x01`` interior-node prefix domain-separates a *link* from a *leaf* (reusing the
shared RFC 6962 primitives so A and B hash records identically -- a fair bake-off).

Why it exists / where it sits
-----------------------------
This is the **baseline** competitor in the E5 bake-off (``experiments.md`` E5: "(a)
plain hash-chain"). It detects mid-log edits but, per the research (A6.2 src 05),
has **O(n) verification** (you must walk the whole chain) and is **silently
truncatable** (dropping a suffix leaves a still-valid shorter chain) unless an
external commitment (STH) pins the length. The bake-off (M4) measures exactly these
weaknesses against Candidate B.

Security / compliance invariants upheld
---------------------------------------
* **Append-only:** the only mutator is :meth:`append`; there is no update/delete
  (FHIR no-update/no-delete, src 02). ``seq`` is assigned monotonically and
  gaplessly by the log, not the caller.
* **Fail-closed verification:** :meth:`verify` returns the first tamper it finds
  (or ``None`` if intact); a caller treats any non-``None`` result as "refuse".
* **Crypto-shredding (T1/A6.4):** :meth:`tombstone` erases content by appending a
  *new* tombstone record -- it never rewrites an existing link.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from autofirm.audit.audit_record_contract import AuditRecord
from autofirm.audit.rfc6962_hashing import HASH_BYTES, node_hash

__all__ = ["ChainEntry", "HashChainLog", "TamperFinding"]

# Fixed genesis seed for link[-1]; 32 zero bytes. Hard-coded (not caller-supplied)
# so the chain origin is part of the contract and cannot be forged by choosing it.
GENESIS_LINK = b"\x00" * HASH_BYTES


@dataclass(frozen=True)
class TamperFinding:
    """A detected tamper: which entry failed and a human-readable reason.

    Returned by :meth:`HashChainLog.verify`. A non-``None`` finding means the log
    MUST be treated as compromised (fail-closed).
    """

    seq: int
    reason: str


@dataclass(frozen=True)
class ChainEntry:
    """One immutable chain entry: the record plus its computed forward link."""

    record: AuditRecord
    link: bytes  # SHA-256(0x01 || prev_link || leaf_hash(record))


@dataclass
class HashChainLog:
    """An append-only forward hash-chain over :class:`AuditRecord` leaves."""

    _entries: list[ChainEntry] = field(default_factory=list)

    def __len__(self) -> int:
        """Return the number of entries currently in the chain."""
        return len(self._entries)

    @property
    def head_link(self) -> bytes:
        """The most recent chain link (or the genesis seed for an empty log)."""
        return self._entries[-1].link if self._entries else GENESIS_LINK

    def append(self, record: AuditRecord) -> ChainEntry:
        """Append a record, computing and storing its forward link.

        The record's ``seq`` MUST equal the next gapless index, enforcing the
        monotonic-gapless invariant at the log boundary (fail-closed).

        Args:
            record: The audit record to append.

        Returns:
            The created :class:`ChainEntry`.

        Raises:
            ValueError: If ``record.seq`` is not the expected next index.
        """
        expected = len(self._entries)
        # fail-closed: gapless monotonic seq is a log invariant, refuse otherwise.
        if record.seq != expected:
            raise ValueError(f"non-gapless seq: expected {expected}, got {record.seq}")
        link = node_hash(self.head_link, record.leaf())
        entry = ChainEntry(record=record, link=link)
        self._entries.append(entry)
        return entry

    def tombstone(self, seq_to_erase: int, tombstone_record: AuditRecord) -> ChainEntry:
        """Crypto-shred a record's content by appending a tombstone (T1/A6.4).

        This NEVER rewrites the chain: the original entry's link is untouched, the
        plaintext content was never stored (only its digest), and a *new* record
        is appended declaring the erasure. The chain stays verifiable.

        Args:
            seq_to_erase: The seq whose content is being declared erased.
            tombstone_record: The new (tombstoned) record to append.

        Returns:
            The appended tombstone :class:`ChainEntry`.

        Raises:
            ValueError: If ``seq_to_erase`` is not an existing entry, or the
                tombstone record is not marked tombstoned.
        """
        # fail-closed: can only erase content that exists, and the new record must
        # actually be a tombstone (so the erasure is itself auditable).
        if not 0 <= seq_to_erase < len(self._entries):
            raise ValueError(f"cannot tombstone non-existent seq {seq_to_erase}")
        if not tombstone_record.entity.tombstoned:
            raise ValueError("tombstone_record.entity.tombstoned must be True")
        return self.append(tombstone_record)

    def verify(self) -> TamperFinding | None:
        """Recompute every link; return the first tamper or ``None`` if intact.

        This is **O(n)** -- it walks the entire chain (the baseline's measured
        weakness vs Candidate B's O(log n) proofs).

        Returns:
            The first :class:`TamperFinding`, or ``None`` if the chain is intact.
        """
        prev = GENESIS_LINK
        for index, entry in enumerate(self._entries):
            # Detect reordering / insertion / deletion via the gapless seq.
            if entry.record.seq != index:
                return TamperFinding(index, f"seq mismatch: stored {entry.record.seq}")
            expected_link = node_hash(prev, entry.record.leaf())
            # A bit-flip in the record changes its leaf -> link mismatch here.
            if entry.link != expected_link:
                return TamperFinding(index, "link mismatch: record or link altered")
            prev = entry.link
        return None

    def entries(self) -> tuple[ChainEntry, ...]:
        """Return an immutable snapshot of the chain (read-only access)."""
        return tuple(self._entries)
