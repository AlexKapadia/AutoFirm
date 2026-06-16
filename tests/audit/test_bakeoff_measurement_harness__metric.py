"""Tests for the E5 winner-evidence harness -- the metric is measured honestly.

Proves teeth (CLAUDE.md §3.6): the harness reports the REAL behaviour of Candidate
B's verifier (not a guess), so these tests assert the winning metric outcomes: B
detects EVERY attack class incl. truncation, proves append-only consistency, has an
O(log n) inclusion proof and O(log n) verification cost, and crypto-shredding does
not break consistency with a prior STH. (Candidate A's losing numbers are preserved
in the results doc; its implementation was deleted -- no graveyard.)
"""

import math

import pytest

from autofirm.audit.bakeoff_measurement_harness import build_record, run_winner_evidence
from autofirm.audit.candidate_b_consistency_proof import verify_consistency
from autofirm.audit.candidate_b_merkle_audit_log import MerkleAuditLog
from autofirm.audit.tamper_attack_classes import TamperAttackClass

SIZES = [4, 8, 16, 64, 256]


@pytest.fixture(scope="module")
def report():
    return run_winner_evidence(SIZES)


# ----------------------- tamper-detection completeness --------------------- #


def test_winner_detects_every_attack_class_at_every_size(report) -> None:
    for m in report.ordered():
        assert m.all_attacks_detected, (m.tree_size, m.attacks_detected)


def test_winner_detects_all_six_named_classes(report) -> None:
    expected = {c.value for c in TamperAttackClass}
    for m in report.ordered():
        assert set(m.attacks_detected) == expected


def test_winner_is_truncation_resistant(report) -> None:
    for m in report.ordered():
        assert m.truncation_detected is True
        assert m.attacks_detected[TamperAttackClass.TRUNCATE] is True


# --------------------------- consistency proof ----------------------------- #


def test_winner_consistency_proof_correct_at_every_size(report) -> None:
    for m in report.ordered():
        assert m.consistency_proof_correct is True


# ----------------------- proof size / verification cost -------------------- #


def test_winner_inclusion_proof_is_logarithmic(report) -> None:
    for m in report.ordered():
        ceil_log2 = max(1, math.ceil(math.log2(m.tree_size)))
        assert m.inclusion_proof_nodes <= ceil_log2


def test_winner_verify_cost_is_logarithmic(report) -> None:
    for m in report.ordered():
        assert m.verify_hash_ops <= math.ceil(math.log2(m.tree_size)) + 1


def test_winner_append_latency_is_recorded(report) -> None:
    # Append time is measured and non-negative at every size (sanity on the timer).
    for m in report.ordered():
        assert m.append_seconds_total >= 0.0


def test_winner_small_trees_are_trivially_truncation_consistent() -> None:
    # Below the minimum truncation size the truncation check is trivially True
    # (there is no meaningful suffix to drop). Attack completeness is only
    # well-defined for trees large enough to reorder/insert/delete, so it is
    # asserted on the SIZES fixture (>=4), not here.
    small = run_winner_evidence([1, 2, 3])
    for m in small.ordered():
        assert m.truncation_detected is True
        assert m.attacks_detected[TamperAttackClass.TRUNCATE] is True


# --------------------------- crypto-shred (T1) ----------------------------- #


def test_winner_tombstone_does_not_change_prior_sth() -> None:
    log = MerkleAuditLog()
    for i in range(8):
        log.append(build_record(i))
    sth = log.seal(build_record(0).timestamp)
    log.tombstone(2, build_record(8, tombstoned=True))
    # The new tree is append-only consistent with the pre-tombstone STH: the
    # erasure added a leaf, it did NOT rewrite the committed prefix.
    proof, ok = log.prove_consistency(sth)
    assert ok is True
    assert verify_consistency(
        sth.tree_size, len(log), bytes.fromhex(sth.root_hash), log.root(), proof
    )
