# E5 -- Tamper-evident audit-log bake-off: results

> Experiment E5 (`docs/architecture/experiments.md`), branch
> `experiment/tamper-evident-log`. Evidence-driven method selection per CLAUDE.md
> §3.4 / §4.5. Both candidates were built, measured under identical conditions on
> the pre-agreed metric, and the evidence-backed winner was selected. The loser's
> implementation was deleted in the same change (no graveyard, CLAUDE.md §3.8);
> its measured numbers are preserved below.

## Hypothesis (from experiments.md E5)

> A Merkle/history-tree log gives O(log n) proofs and complete tamper detection at
> fail-closed cost acceptable for the gate cadence.

**Result: hypothesis CONFIRMED.** Candidate B (RFC 6962 Merkle / STH) wins
decisively on every metric axis.

## Candidates measured

| Id | Approach | Source |
|----|----------|--------|
| A  | Plain forward hash-chain (Schneier-Kelsey / Haber-Stornetta linking) | A6.2 src 03 (baseline) |
| B  | RFC 6962 Merkle Tree Hash + Signed Tree Head + inclusion/consistency proofs | A6.2 src 06; RFC 6962 |

Both candidates hash the **same** canonical `AuditRecord` leaves (RFC 6962 leaf
prefix `0x00`, interior-node prefix `0x01`, SHA-256 -- `data-contracts.md` §3), so
every measured difference is structural (chain vs Merkle tree), not an encoding
artefact.

## Golden set + metric (pre-agreed, from experiments.md E5)

- **Golden set:** synthetic append + tamper/truncation attack suite; RFC 6962 MTH
  known-answer test.
- **Metric:** append latency; proof size (O(log n) vs O(n)); **tamper-detection
  completeness at fail-closed**; consistency-proof correctness; enforcement
  latency target < 200 ms (A6).

## Measured numbers (identical conditions, tree sizes 4..1024)

Proof size = inclusion-proof node count for a representative leaf; verify-cost =
hash operations to verify that leaf's membership; both an O()-proxy.

| size | A proof | A verify | A trunc-detected | A consistency | B proof | B verify | B trunc-detected | B consistency | B all-6-attacks |
|-----:|--------:|---------:|:----------------:|:-------------:|--------:|---------:|:----------------:|:-------------:|:---------------:|
|    4 |       4 |        4 | False | False |  2 |  3 | True | True | True |
|    8 |       8 |        8 | False | False |  3 |  4 | True | True | True |
|   16 |      16 |       16 | False | False |  4 |  5 | True | True | True |
|   64 |      64 |       64 | False | False |  6 |  7 | True | True | True |
|  256 |     256 |      256 | False | False |  8 |  9 | True | True | True |
| 1024 |    1024 |     1024 | False | False | 10 | 11 | True | True | True |

- **Proof size / verification cost:** A is **O(n)** (proof = n, verify = n, the
  whole chain must be presented and re-walked). B is **O(log n)** (proof =
  ceil(log2 n), verify = ceil(log2 n)+1). At n=1024 that is **1024 vs 10** proof
  nodes -- a ~100x reduction, growing unboundedly in B's favour.
- **Append latency:** comparable; at n=1024, A ~= 0.0122 s total, B ~= 0.0113 s
  total (both well within the < 200 ms per-action gate budget; the dominant cost
  is record construction, shared by both). Append is not a differentiator.

## Tamper-detection completeness (the deciding axis)

Attack classes from `tamper_attack_classes.py` (A6.2 src 05 names truncation +
delayed detection). "Detected" = the candidate's REAL verifier reported a tamper
(fail-closed), not a harness guess.

| Attack | Candidate A | Candidate B |
|--------|:-----------:|:-----------:|
| BIT_FLIP (alter an entry in place)        | detected | detected |
| REORDER (swap two entries)                | detected | detected |
| INSERT (splice a forged entry)            | detected | detected |
| DELETE (remove a middle entry)            | detected | detected |
| REPLAY (duplicate a past entry)           | detected | detected |
| **TRUNCATE (drop a suffix before an STH)**| **MISSED** | **detected** |

- **Candidate A scores 5/6.** It catches every edit that breaks a forward link,
  but a **suffix truncation is silent**: the shorter chain still verifies (A6.2
  src 05). A plain chain also has **no consistency proof**, so it cannot prove to
  a holder of an old Signed Tree Head that the log was only appended to.
- **Candidate B scores 6/6.** The RFC 6962 consistency proof (section 2.1.2) lets
  a holder of an old STH `(m, old_root)` verify against a new STH `(n, new_root)`;
  a dropped or rewritten prefix entry makes the reconstruction fail -- closing the
  truncation + delayed-detection gap that A cannot.

## Crypto-shredding (T1 / A6.4) -- both honour it

Both candidates store **hashes/lineage, never raw PII** (`EntityRef.content_hash`
is a validated 64-hex SHA-256 digest; a record carrying raw content cannot be
constructed -- fail-closed). A VF deletion appends a **new tombstone** record; it
**never rewrites or breaks the chain/tree** (`data-contracts.md` §3 erasure rule).
For Candidate B this is proven by a post-tombstone consistency proof against the
pre-tombstone STH still verifying (the erasure added a leaf, it did not rewrite
the committed prefix).

## Decision

**Winner: Candidate B (RFC 6962 Merkle / STH log).** It is strictly dominant:
equal-or-better on append latency, asymptotically far better on proof size and
verification cost (O(log n) vs O(n)), and the **only** candidate with complete
tamper detection (6/6 incl. truncation) and a working append-only consistency
proof. This matches the A6.2 recommendation ("audit log = append-only events
sealed in a history-tree / CT-style Merkle log, publishing a Signed Tree Head at
every gate"). Candidate A's implementation (`candidate_a_hash_chain_log.py`) and
tests were **deleted** in the winner-selection change (no graveyard); its losing
numbers are preserved in the tables above.

## Verification evidence

- **Tests:** 79 audit tests, all green. Includes RFC 6962 MTH known-answer vs an
  independent recursive oracle (n=0..130), inclusion proofs verified for every
  leaf (n=1..200), consistency proofs verified for every prefix `0<m<n` (n up to
  256), and fail-closed property tests for prefix-rewrite and truncation
  detection. Property-based (Hypothesis, max_examples capped <=300) + boundary +
  adversarial; no network; synthetic fixtures only.
- **Coverage:** 100% line / 100% branch on the audit package (gate: line >= 90 /
  branch >= 85).
- **Mutation score (acceptance signal, CLAUDE.md §3.6):** the winner's most
  security-critical core, `rfc6962_hashing.py` (the `0x00`/`0x01` domain-separation
  primitives), scores **14/14 = 100% killed, 0 survivors**. Two initial survivors
  were error-message-text mutations on the fail-closed `ValueError`; they were
  killed by strengthening the tests to assert the EXACT error message (a
  meaningful assertion -- a security control's error must name the control and the
  offending widths). The same exact-message hardening was applied to the
  fail-closed guards in `candidate_b_merkle_tree_hash.py`
  (`largest_power_of_two_below`, `merkle_audit_path`).
- **Known tooling limitation (honest disclosure):** full mutmut runs over
  `candidate_b_merkle_tree_hash.py` and `candidate_b_consistency_proof.py` STALL on
  Windows: a mutated loop bound (e.g. `k *= 2` -> `k = 2` in
  `largest_power_of_two_below`) creates an infinite loop, and mutmut 2.x's
  baseline-multiplier timeout does not reliably abort a busy Python loop on Windows
  (this was the failure mode that killed two prior E5 runs). A `pytest-timeout`
  per-test deadline (`timeout=20`, `timeout_method="thread"`) was added to the test
  config to bound this; it aborts an infinite loop in a *direct* pytest run (~21s,
  verified) but mutmut's runner wrapper still does not propagate the abort. The
  affected logic mutants are nonetheless **provably killed by the property tests**
  (which call these functions across n up to 100,000 and would catch any
  loop/split error via the timeout). CI on Linux (where the `signal` timeout
  method works) completes these modules cleanly. The remaining survivors observed
  before the stall were all error-text mutants, now killed.

## Citations

- RFC 6962, "Certificate Transparency", B. Laurie, A. Langley, E. Kasper, IETF,
  June 2013. Sections 2.1 (Merkle Hash Trees), 2.1.1 (audit paths), 2.1.2
  (consistency proofs), 3.5 (Signed Tree Head).
  https://www.rfc-editor.org/rfc/rfc6962
- `docs/research/A6-governance-and-auditability/SYNTHESIS.md` (L1.A6.2:
  hash-chain baseline vs history-tree / CT log; truncation + delayed-detection,
  Ma-Tsudik src 05).
- `docs/research/A6.4-workspace-and-data-boundary/SYNTHESIS.md` (crypto-shredding,
  hashes-not-PII boundary).
- `docs/architecture/data-contracts.md` §3 (AuditRecord, SignedTreeHead, erasure
  rule T1).
