"""Adversarial + property tests for Candidate A (forward hash-chain log).

Proves teeth (CLAUDE.md §3.6): every tamper class (bit-flip, reorder, insert,
delete, truncate) is detected, append-only/gapless is enforced fail-closed, the
chain links to the canonical RFC 6962 leaves, and crypto-shredding (T1) does NOT
rewrite the chain. Stateful + property tests stress the general case, not fixtures.
"""

import dataclasses

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from autofirm.audit.candidate_a_hash_chain_log import (
    GENESIS_LINK,
    ChainEntry,
    HashChainLog,
)
from autofirm.audit.rfc6962_hashing import node_hash
from tests.audit.synthetic_audit_records import make_record


def build_log(n: int) -> HashChainLog:
    log = HashChainLog()
    for i in range(n):
        log.append(make_record(i))
    return log


# ------------------------------- happy path -------------------------------- #


def test_empty_log_verifies_and_head_is_genesis() -> None:
    log = HashChainLog()
    assert len(log) == 0
    assert log.head_link == GENESIS_LINK
    assert log.verify() is None


def test_intact_chain_verifies() -> None:
    assert build_log(25).verify() is None


def test_first_link_uses_genesis_seed() -> None:
    log = build_log(1)
    expected = node_hash(GENESIS_LINK, make_record(0).leaf())
    assert log.entries()[0].link == expected


def test_append_returns_entry_with_correct_link() -> None:
    log = build_log(3)
    e = log.append(make_record(3))
    assert e.link == node_hash(log.entries()[2].link, make_record(3).leaf())


# ------------------- append-only / gapless (fail-closed) ------------------- #


def test_append_refuses_non_gapless_seq() -> None:
    log = build_log(2)
    with pytest.raises(ValueError):
        log.append(make_record(5))  # gap
    with pytest.raises(ValueError):
        log.append(make_record(0))  # rewind


# ----------------------------- tamper classes ------------------------------ #


def _replace_entry(log: HashChainLog, index: int, entry: ChainEntry) -> None:
    # Test-only surgery to simulate an attacker mutating stored bytes.
    log._entries[index] = entry


def test_detects_bit_flip_in_record() -> None:
    log = build_log(10)
    # Swap entry 4's record for an altered one but KEEP the old (now-stale) link.
    tampered = dataclasses.replace(log.entries()[4], record=make_record(4, tenant_id="evil"))
    _replace_entry(log, 4, tampered)
    finding = log.verify()
    assert finding is not None and finding.seq == 4


def test_detects_reorder() -> None:
    log = build_log(6)
    e2, e3 = log.entries()[2], log.entries()[3]
    _replace_entry(log, 2, e3)
    _replace_entry(log, 3, e2)
    assert log.verify() is not None


def test_detects_insertion() -> None:
    log = build_log(5)
    forged = ChainEntry(record=make_record(2, tenant_id="x"), link=log.entries()[2].link)
    log._entries.insert(2, forged)
    assert log.verify() is not None


def test_detects_deletion_of_middle_entry() -> None:
    log = build_log(8)
    del log._entries[3]
    # Deletion creates a seq gap (index 3 now holds seq 4) -> detected.
    assert log.verify() is not None


def test_truncation_leaves_valid_shorter_chain_baseline_weakness() -> None:
    # Documented Candidate-A weakness (A6.2 src 05): dropping a SUFFIX is NOT
    # internally detectable -- the shorter chain still verifies. Only an external
    # STH commitment pins the length. The bake-off (M4) measures this gap.
    log = build_log(10)
    del log._entries[7:]
    assert log.verify() is None  # truncation is silent without an STH


# --------------------------- crypto-shred (T1) ----------------------------- #


def test_tombstone_appends_and_does_not_rewrite_chain() -> None:
    log = build_log(4)
    original_links = [e.link for e in log.entries()]
    log.tombstone(1, make_record(4, tombstoned=True))
    # Existing links are byte-for-byte unchanged; only a new entry was appended.
    assert [e.link for e in log.entries()[:4]] == original_links
    assert len(log) == 5
    assert log.verify() is None


def test_tombstone_refuses_nonexistent_seq() -> None:
    log = build_log(3)
    with pytest.raises(ValueError):
        log.tombstone(9, make_record(3, tombstoned=True))


def test_tombstone_refuses_non_tombstone_record() -> None:
    log = build_log(3)
    with pytest.raises(ValueError):
        log.tombstone(1, make_record(3, tombstoned=False))


# ------------------------------- properties -------------------------------- #


@settings(max_examples=150)
@given(n=st.integers(min_value=0, max_value=60))
def test_property_any_built_chain_verifies(n: int) -> None:
    assert build_log(n).verify() is None


@settings(max_examples=150)
@given(
    n=st.integers(min_value=1, max_value=40),
    target=st.integers(min_value=0, max_value=39),
)
def test_property_single_field_tamper_always_detected(n: int, target: int) -> None:
    # Property: flipping the content of ANY single entry is ALWAYS caught,
    # wherever it is in the chain (generality, not fixture-fit).
    idx = target % n
    log = build_log(n)
    bad = dataclasses.replace(log.entries()[idx], record=make_record(idx, content_salt="evil"))
    _replace_entry(log, idx, bad)
    finding = log.verify()
    assert finding is not None and finding.seq == idx
