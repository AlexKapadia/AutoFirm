# W5 / B5-10 — Billing Reconciliation & Append-Only / Hash-Chained Audit Ledger

**Workstream:** W5 — 100%-accurate cross-model spend/cost accounting.
**Research question:** How do we reconcile our computed costs against provider invoices to a zero-drift target, and how do we make the cost ledger tamper-evident, append-only, and auditable using a standard hash-chained Merkle structure?
**Date accessed:** 2026-06-17.

---

## 1. Full Citations

1. **B. Laurie, A. Langley, E. Kasper — "Certificate Transparency," RFC 6962.** IETF, June 2013. URL: https://www.rfc-editor.org/rfc/rfc6962 (also https://datatracker.ietf.org/doc/html/rfc6962). Accessed 2026-06-17. **GRADE: High** (IETF standards-track RFC; the primary source for the Merkle leaf/node hashing W5 uses). Fetched from rfc-editor.org; datatracker mirror returned 403.
2. **Double-entry bookkeeping & append-only ledger principle** — corroborated across QuickBooks (Intuit) "Double-Entry Bookkeeping Guide," Wikipedia "Double-entry bookkeeping," and Microsoft Learn "Undo a posting using a reversing entry" (Dynamics 365 Business Central). URLs: https://quickbooks.intuit.com/global/resources/bookkeeping/double-entry-bookkeeping-guide/ ; https://en.wikipedia.org/wiki/Double-entry_bookkeeping ; https://learn.microsoft.com/en-us/dynamics365/business-central/finance-how-reverse-journal-posting — accessed 2026-06-17. **GRADE: Medium-High** (professional/standard accounting references; the underlying principle is GAAP-standard but the specific AICPA clause is **unverified by direct fetch**).
3. **Account reconciliation best practice (three-way reconciliation, variance thresholds)** — Clio "Reconciliation in Accounting," Numeric "Transaction Reconciliation," AccountantsLawLab "Three-Way Bank Reconciliation." URLs: https://www.clio.com/blog/reconciliation-accounting/ ; https://www.numeric.io/blog/transaction-reconciliation-guide ; https://www.accountantslawlab.com/blog/three-way-bank-reconciliation-gymnastics — accessed 2026-06-17. **GRADE: Medium** (professional practice references; no single AICPA primary clause fetched — **AICPA-specific text unverified**).

---

## 2. Faithful Structured Summary

### 2.1 RFC 6962 §2.1 — Merkle Hash Tree — EXACT formulae (verbatim)

RFC 6962 defines the Merkle Tree Hash (`MTH`) over an ordered list of `n` entries `D[n] = {d(0), d(1), ..., d(n-1)}` using `SHA-256` and `||` for concatenation.

**Hash of an empty list — hash of the empty string:**

```text
MTH({}) = SHA-256().
```

**Leaf hash (one-entry list), with 0x00 domain-separation prefix:**

```text
MTH({d(0)}) = SHA-256(0x00 || d(0)).
```

**Interior node hash (n > 1), with 0x01 domain-separation prefix:**

```text
MTH(D[n]) = SHA-256(0x01 || MTH(D[0:k]) || MTH(D[k:n]))
```

where (verbatim) **"let k be the largest power of two smaller than n (i.e., k < n <= 2k)."**

Domain separation (verbatim):

> "Note that the hash calculations for leaves and nodes differ. This domain separation is required to give second preimage resistance."

The `0x00` (leaf) vs `0x01` (node) prefix is **mandatory and load-bearing**: without it an attacker could present an interior node as if it were a leaf (second-preimage attack). The empty-string hash is reserved for the empty tree only.

### 2.2 Account reconciliation methodology

Reconciliation compares **internal records (our computed cost ledger)** against an **external source (the provider's invoice / usage export)** to confirm the figures agree and to surface drift:

- **Three-way reconciliation:** three independent record sets must agree exactly — e.g. (1) our per-record computed costs, (2) the provider's itemized usage export, (3) the provider's billed invoice total. "The grand total ... must equal the [ledger] and adjusted [statement] balance **exactly**."
- **Line-up:** "lining up internal records—your general ledger, subledgers, or accounting system—against external statements ... to catch errors, prevent fraud, and maintain audit-ready books."
- **Variance / tolerance thresholds:** "Set thresholds—auto-clear differences below a certain amount, route larger variances for review." Small, explained differences (e.g. provider's own rounding) auto-clear; anything above tolerance is escalated and resolved. The *target is zero drift*; the tolerance only governs what is auto-cleared vs. investigated.
- **Resolution:** identified differences are explained (timing, provider rounding, our error) and corrected via new entries, never by overwriting (see §2.3).

### 2.3 Double-entry immutability — append-only, corrections by reversing entry

> "Financial ledgers or audit trails in double-entry accounting are append-only, and historical entries are never deleted."

> "In a traditional accountant's ledger, you can add new lines, but you can never erase or change what's already been written."

> "Reversal entries cancel out the original erroneous postings, and you must make new entries for the correction." / "After you reverse an entry, you must make the correct entry."

> "Simply deleting an inaccurate journal entry can raise suspicion should your business be audited. Instead, by reversing the original entry, you'll maintain an audit trail that documents the changes."

> "the change becomes another dated ledger event, not a silent rewrite. This creates compliance by default."

Principle: a posted ledger entry is **immutable**. Every correction is a **new dated reversing entry plus a new correct entry** — the original error stays visible. This is exactly what an append-only hash-chained log enforces *cryptographically*: you literally cannot rewrite a prior leaf without breaking every downstream hash.

---

## 3. Best Parts to Take → W5 Mapping

- **Hash-chained, append-only `UsageCostRecord` ledger using RFC 6962 hashing.** Each record's leaf hash is computed with the **0x00 prefix**; the running chain/tree head combines children with the **0x01 prefix** exactly as specified. Reproduce verbatim:

  ```text
  leaf_hash(entry)        = SHA-256(0x00 || entry_bytes)
  node_hash(left, right)  = SHA-256(0x01 || left || right)
  empty_tree              = SHA-256(<empty string>)
  k = largest power of two with k < n <= 2k    # split point for n entries
  ```

  Tamper-evidence: altering any historical `UsageCostRecord` changes its `0x00` leaf hash and therefore every `0x01` ancestor up to the head — detectable on the next verification.
- **Corrections are reversing entries, never edits.** A mis-priced record is fixed by appending (a) a reversing record and (b) a corrected record — the original leaf is never mutated, preserving both the accounting audit trail and the hash chain.
- **Reconciliation = our cost ledger vs. provider usage export vs. provider invoice, three-way, zero-drift target.** Per-record and total comparison; differences within a documented **tolerance** auto-clear, larger variances are flagged and resolved; every resolution is itself an appended reversing/adjusting entry.
- **Determinism + security tests:** byte-exact leaf/node hash vectors (including the empty-tree hash); a fuzz/property test that any single-byte mutation of any historical record is detected by chain re-verification; mutation-test that swapping the `0x00`/`0x01` prefixes (or dropping them) is caught (second-preimage guard); reconciliation tests that drive a synthetic provider export with injected discrepancies and assert correct auto-clear vs. escalate behaviour and that the corrected ledger reconciles to zero.

## 4. RED Flags

- **Editing or deleting a posted ledger row** — destroys the audit trail and breaks the hash chain; corrections must be *reversing entries*.
- **Omitting / swapping the 0x00 (leaf) vs 0x01 (node) domain-separation prefix** — opens a second-preimage attack; the prefixes are mandatory.
- **Treating a non-zero reconciliation variance as acceptable without explanation** — the target is zero drift; tolerance governs auto-clear, not silent acceptance.
- **Reconciling only the invoice total and not the line items** — masks offsetting per-record errors; three-way, item-level reconciliation is required.
- **Hashing the record without canonical/deterministic serialization** — non-reproducible leaf hashes; entry bytes must be canonical before hashing.
