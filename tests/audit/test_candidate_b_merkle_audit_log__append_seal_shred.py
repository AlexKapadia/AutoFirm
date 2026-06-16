"""Adversarial tests for the append-driven Merkle audit log (Candidate B wrapper).

Covers the log interface directly (CLAUDE.md §3.6): gapless append, STH seal,
inclusion against a sealed root, consistency across seals including the equal-size
(no-append) case, fail-closed tombstone, and the read-only snapshots. These kill
mutants on the wrapper that the metric-level harness tests do not reach directly.
"""

import pytest

from autofirm.audit.candidate_b_consistency_proof import verify_consistency
from autofirm.audit.candidate_b_merkle_audit_log import MerkleAuditLog
from autofirm.audit.candidate_b_merkle_tree_hash import merkle_tree_hash
from tests.audit.synthetic_audit_records import make_record


def build(n: int) -> MerkleAuditLog:
    log = MerkleAuditLog()
    for i in range(n):
        log.append(make_record(i))
    return log


def test_len_and_root_match_primitives() -> None:
    log = build(5)
    assert len(log) == 5
    assert log.root() == merkle_tree_hash(log.leaf_inputs())


def test_append_refuses_non_gapless_seq() -> None:
    log = build(3)
    with pytest.raises(ValueError):
        log.append(make_record(7))
    with pytest.raises(ValueError):
        log.append(make_record(0))


def test_seal_commits_size_and_root() -> None:
    log = build(6)
    sth = log.seal(make_record(0).timestamp)
    assert sth.tree_size == 6
    assert sth.root_hash == log.root().hex()


def test_inclusion_against_sealed_root_holds_and_forged_fails() -> None:
    log = build(10)
    root = log.root()
    assert log.verify_inclusion(4, root) is True
    # A forged input at index 4 cannot reconstruct the sealed root.
    assert log.verify_inclusion_of_input(b"forged", 4, root, log.inclusion_proof(4)) is False


def test_consistency_equal_size_no_append_is_consistent() -> None:
    log = build(8)
    sth = log.seal(make_record(0).timestamp)
    # Nothing appended since the seal: equal-size path -> consistent (root matches).
    proof, ok = log.prove_consistency(sth)
    assert proof == []
    assert ok is True


def test_consistency_equal_size_detects_rewrite() -> None:
    log = build(8)
    sth = log.seal(make_record(0).timestamp)
    # An STH claiming the same size but a DIFFERENT root must be rejected.
    forged_sth = sth.model_copy(update={"root_hash": merkle_tree_hash([b"x"]).hex()})
    _, ok = log.prove_consistency(forged_sth)
    assert ok is False


def test_consistency_after_appends_verifies() -> None:
    log = build(4)
    sth = log.seal(make_record(0).timestamp)
    for i in range(4, 12):
        log.append(make_record(i))
    proof, ok = log.prove_consistency(sth)
    assert ok is True
    assert verify_consistency(
        sth.tree_size, len(log), bytes.fromhex(sth.root_hash), log.root(), proof
    )


def test_consistency_refuses_old_larger_than_current() -> None:
    log = build(3)
    # An old STH bigger than the current tree is structurally impossible.
    big_sth = log.seal(make_record(0).timestamp).model_copy(update={"tree_size": 9})
    _, ok = log.prove_consistency(big_sth)
    assert ok is False


def test_tombstone_appends_without_breaking_consistency() -> None:
    log = build(5)
    sth = log.seal(make_record(0).timestamp)
    log.tombstone(2, make_record(5, tombstoned=True))
    assert len(log) == 6
    _, ok = log.prove_consistency(sth)
    assert ok is True


def test_tombstone_fail_closed() -> None:
    log = build(4)
    with pytest.raises(ValueError):
        log.tombstone(99, make_record(4, tombstoned=True))  # nonexistent seq
    with pytest.raises(ValueError):
        log.tombstone(1, make_record(4, tombstoned=False))  # not a tombstone


def test_records_and_leaf_inputs_are_snapshots() -> None:
    log = build(3)
    recs = log.records()
    leaves = log.leaf_inputs()
    assert len(recs) == 3
    assert len(leaves) == 3
    # Mutating the returned list must not affect the log (read-only snapshot).
    leaves.append(b"intruder")
    assert len(log.leaf_inputs()) == 3
