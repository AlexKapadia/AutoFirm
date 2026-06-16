"""Tests for the E5 bake-off harness -- the pre-agreed metric is measured honestly.

Proves teeth (CLAUDE.md §3.6): the harness reports the REAL behaviour of each
candidate's verifier (not a guess), so these tests assert the metric outcomes that
decide the winner: Candidate B detects EVERY attack class incl. truncation and
proves append-only consistency; Candidate A misses truncation and has no
consistency proof; B's inclusion proof is O(log n) while A's is O(n); and both
honour crypto-shredding without rewriting prior commitments.
"""

import math

import pytest

from autofirm.audit.bakeoff_measurement_harness import (
    build_record,
    run_bakeoff,
)
from autofirm.audit.candidate_a_hash_chain_log import HashChainLog
from autofirm.audit.candidate_b_consistency_proof import verify_consistency
from autofirm.audit.candidate_b_merkle_audit_log import MerkleAuditLog
from autofirm.audit.tamper_attack_classes import TamperAttackClass

SIZES = [4, 8, 16, 64, 256]


@pytest.fixture(scope="module")
def report():
    return run_bakeoff(SIZES)


# ----------------------- tamper-detection completeness --------------------- #


def test_candidate_b_detects_every_attack_class_at_every_size(report) -> None:
    for m in report.for_candidate("B"):
        assert m.all_attacks_detected, (m.tree_size, m.attacks_detected)


def test_candidate_b_detects_all_six_named_classes(report) -> None:
    expected = {c.value for c in TamperAttackClass}
    for m in report.for_candidate("B"):
        assert set(m.attacks_detected) == expected


def test_candidate_a_detects_in_place_edits_but_misses_truncation(report) -> None:
    for m in report.for_candidate("A"):
        # A catches edits that break a forward link...
        assert m.attacks_detected[TamperAttackClass.BIT_FLIP]
        assert m.attacks_detected[TamperAttackClass.REORDER]
        assert m.attacks_detected[TamperAttackClass.INSERT]
        assert m.attacks_detected[TamperAttackClass.DELETE]
        assert m.attacks_detected[TamperAttackClass.REPLAY]
        # ...but a suffix truncation is SILENT without an external STH (src 05).
        assert m.attacks_detected[TamperAttackClass.TRUNCATE] is False
        assert m.truncation_detected is False


def test_only_candidate_b_truncation_resistant(report) -> None:
    for m in report.for_candidate("B"):
        assert m.truncation_detected is True


# --------------------------- consistency proof ----------------------------- #


def test_candidate_b_consistency_proof_correct_at_every_size(report) -> None:
    for m in report.for_candidate("B"):
        assert m.consistency_proof_correct is True


def test_candidate_a_has_no_consistency_proof(report) -> None:
    for m in report.for_candidate("A"):
        assert m.consistency_proof_correct is False


# ----------------------- proof size / verification cost -------------------- #


def test_candidate_b_inclusion_proof_is_logarithmic(report) -> None:
    for m in report.for_candidate("B"):
        ceil_log2 = max(1, math.ceil(math.log2(m.tree_size)))
        assert m.inclusion_proof_nodes <= ceil_log2


def test_candidate_a_inclusion_proof_is_linear(report) -> None:
    for m in report.for_candidate("A"):
        assert m.inclusion_proof_nodes == m.tree_size


def test_candidate_b_verify_cost_far_below_candidate_a_at_scale(report) -> None:
    a = {m.tree_size: m for m in report.for_candidate("A")}
    b = {m.tree_size: m for m in report.for_candidate("B")}
    # At the largest size, B verifies a membership in O(log n) hashes; A in O(n).
    big = max(SIZES)
    assert b[big].verify_hash_ops < a[big].verify_hash_ops
    assert b[big].verify_hash_ops <= math.ceil(math.log2(big)) + 1


# --------------------------- crypto-shred (T1) ----------------------------- #


def test_candidate_b_tombstone_does_not_change_prior_sth() -> None:
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


def test_candidate_a_tombstone_keeps_chain_valid() -> None:
    log = HashChainLog()
    for i in range(5):
        log.append(build_record(i))
    pre_links = [e.link for e in log.entries()]
    log.tombstone(1, build_record(5, tombstoned=True))
    assert [e.link for e in log.entries()[:5]] == pre_links
    assert log.verify() is None
