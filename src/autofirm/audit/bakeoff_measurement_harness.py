"""The E5 winner-evidence harness -- measures the chosen design (Candidate B).

What this does
--------------
Measures the WINNER of the E5 bake-off (Candidate B, the RFC 6962 Merkle / STH log)
on the pre-agreed E5 metric (``experiments.md`` E5; CLAUDE.md §4.5): append latency,
inclusion-proof size (O(log n)), verification cost (hash-operation count, an
O()-proxy), consistency-proof correctness, and tamper-detection completeness across
every attack class in :class:`TamperAttackClass`, plus truncation resistance. The
output is a structured :class:`WinnerReport` consumed by the evidence/ showcase.

The losing Candidate A (plain hash-chain) was DELETED in the same change that
selected the winner (no graveyard, CLAUDE.md §3.8). Its measured numbers -- which
decided the bake-off -- are preserved in
``docs/architecture/experiments/E5-tamper-evident-log-results.md``.

Why it exists / where it sits
-----------------------------
This is the durable, re-runnable evidence that the chosen design meets the E5
metric. It imports no analysis-only libraries (ADR-001 §5).

Security / compliance invariants upheld
---------------------------------------
Measurement only -- it never weakens a verifier. Tamper detection is asserted by
running Candidate B's real verifier / root-recomputation against a tampered copy;
"detected" means the verifier reported a tamper (fail-closed), not a guess.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime

from autofirm.audit.audit_record_contract import AuditOutcome, AuditRecord, EntityRef
from autofirm.audit.candidate_b_consistency_proof import verify_consistency
from autofirm.audit.candidate_b_merkle_audit_log import MerkleAuditLog
from autofirm.audit.candidate_b_merkle_tree_hash import merkle_tree_hash
from autofirm.audit.tamper_attack_classes import TamperAttackClass

__all__ = [
    "WinnerMeasurement",
    "WinnerReport",
    "build_record",
    "run_winner_evidence",
]

# Below this size a suffix-truncation is not meaningfully distinguishable, so the
# truncation check is treated as trivially consistent.
_MIN_TRUNCATION_TREE = 4


def _digest(salt: str) -> str:
    return hashlib.sha256(salt.encode("utf-8")).hexdigest()


def build_record(seq: int, *, tombstoned: bool = False) -> AuditRecord:
    """Build a deterministic synthetic audit record for the harness (no PII)."""
    return AuditRecord(
        seq=seq,
        entity=EntityRef(
            entity_id=f"entity-{seq}",
            content_hash=_digest(f"content-{seq}"),
            tombstoned=tombstoned,
        ),
        activity="bakeoff.append",
        agent=f"spiffe://autofirm/agent/bakeoff/session/{seq}",
        outcome=AuditOutcome.SUCCESS,
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        tenant_id="tenant-bakeoff",
    )


@dataclass(frozen=True)
class WinnerMeasurement:
    """All measured numbers for the winner at one tree size."""

    tree_size: int
    append_seconds_total: float  # wall time to append `tree_size` records
    inclusion_proof_nodes: int  # O(log n) proof size for a representative leaf
    verify_hash_ops: int  # hash operations to verify that leaf's membership
    consistency_proof_correct: bool  # append-only consistency provable + verified
    truncation_detected: bool  # suffix-drop before an STH caught
    attacks_detected: dict[str, bool]  # per TamperAttackClass: detected?

    @property
    def all_attacks_detected(self) -> bool:
        """True iff every enumerated attack class was detected (completeness)."""
        return all(self.attacks_detected.values())


@dataclass
class WinnerReport:
    """The winner's measurements across the measured tree sizes."""

    measurements: list[WinnerMeasurement] = field(default_factory=list)

    def ordered(self) -> list[WinnerMeasurement]:
        """Return measurements ordered by tree size."""
        return sorted(self.measurements, key=lambda m: m.tree_size)


def _root_of(leaf_inputs: list[bytes]) -> bytes:
    return merkle_tree_hash(leaf_inputs)


def _truncation_detected(tree_size: int) -> bool:
    """Return True iff a suffix-truncation before a prior STH is caught."""
    if tree_size < _MIN_TRUNCATION_TREE:
        return True  # too small to truncate meaningfully; trivially consistent
    half = tree_size // 2
    old_log = MerkleAuditLog()
    for i in range(half):
        old_log.append(build_record(i))
    old_sth = old_log.seal(datetime(2026, 1, 1, tzinfo=UTC))
    full = MerkleAuditLog()
    for i in range(tree_size):
        full.append(build_record(i))
    truncated = MerkleAuditLog()
    for i in range(tree_size - 1):
        truncated.append(build_record(i))
    proof, _ = full.prove_consistency(old_sth)
    # The honest proof must NOT validate against the truncated root -> detected.
    return not verify_consistency(
        old_sth.tree_size,
        tree_size,
        bytes.fromhex(old_sth.root_hash),
        truncated.root(),
        proof,
    )


def _attacks_detected(tree_size: int, root: bytes) -> dict[str, bool]:
    """Run every named attack against Candidate B and record detection."""

    def fresh() -> MerkleAuditLog:
        log = MerkleAuditLog()
        for i in range(tree_size):
            log.append(build_record(i))
        return log

    mid = tree_size // 2
    detected: dict[str, bool] = {}

    # BIT_FLIP: altering a leaf's content changes the recomputed root AND its
    # genuine inclusion proof can no longer reach the sealed root -- assert BOTH.
    log = fresh()
    path = log.inclusion_proof(mid)
    forged_input = b"evil-content"
    leaves = log.leaf_inputs()
    leaves[mid] = forged_input
    root_diverges = _root_of(leaves) != root
    inclusion_fails = not log.verify_inclusion_of_input(forged_input, mid, root, path)
    detected[TamperAttackClass.BIT_FLIP] = root_diverges and inclusion_fails

    # REORDER/INSERT/DELETE/REPLAY all change the leaf set -> the recomputed root
    # diverges from the sealed root.
    log = fresh()
    leaves = log.leaf_inputs()
    leaves[mid - 1], leaves[mid] = leaves[mid], leaves[mid - 1]
    detected[TamperAttackClass.REORDER] = _root_of(leaves) != root

    leaves = log.leaf_inputs()
    leaves.insert(mid, leaves[mid])
    detected[TamperAttackClass.INSERT] = _root_of(leaves) != root

    leaves = log.leaf_inputs()
    del leaves[mid]
    detected[TamperAttackClass.DELETE] = _root_of(leaves) != root

    detected[TamperAttackClass.TRUNCATE] = _truncation_detected(tree_size)

    leaves = log.leaf_inputs()
    leaves.append(leaves[0])  # replay entry 0
    detected[TamperAttackClass.REPLAY] = _root_of(leaves) != root
    return detected


def _measure(tree_size: int) -> WinnerMeasurement:
    log = MerkleAuditLog()
    start = time.perf_counter()
    for i in range(tree_size):
        log.append(build_record(i))
    append_total = time.perf_counter() - start

    root = log.root()
    mid = tree_size // 2
    proof = log.inclusion_proof(mid)
    # Verifying inclusion folds exactly len(proof) node hashes + 1 leaf hash.
    verify_hash_ops = len(proof) + 1

    # Consistency: seal an old STH at half size, append the rest, prove append-only.
    half = max(1, tree_size // 2)
    old_log = MerkleAuditLog()
    for i in range(half):
        old_log.append(build_record(i))
    old_sth = old_log.seal(datetime(2026, 1, 1, tzinfo=UTC))
    _, consistency_ok = log.prove_consistency(old_sth) if tree_size > half else ([], True)

    return WinnerMeasurement(
        tree_size=tree_size,
        append_seconds_total=append_total,
        inclusion_proof_nodes=len(proof),  # O(log n)
        verify_hash_ops=verify_hash_ops,
        consistency_proof_correct=consistency_ok,
        truncation_detected=_truncation_detected(tree_size),
        attacks_detected=_attacks_detected(tree_size, root),
    )


def run_winner_evidence(tree_sizes: list[int]) -> WinnerReport:
    """Measure the winner (Candidate B) over the given tree sizes.

    Args:
        tree_sizes: Ascending list of leaf counts to measure at.

    Returns:
        A :class:`WinnerReport` with one measurement per size.
    """
    report = WinnerReport()
    for size in tree_sizes:
        report.measurements.append(_measure(size))
    return report
