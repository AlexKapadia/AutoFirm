# Crosby & Wallach — *Efficient Data Structures for Tamper-Evident Logging* (history trees; why hash chains alone fail)

> Research note for AutoFirm component **C9 — Cost-Data Integrity & Tamper-Evident Cost Logging**.
> This is the foundational threat-model source: it proves *why a plain hash chain is not enough* and motivates the history-tree + auditor design AutoFirm's cost ledger relies on.

---

## 1. Full citation

- **Title:** *Efficient Data Structures for Tamper-Evident Logging*
- **Authors:** Scott A. Crosby, Dan S. Wallach (Rice University)
- **Venue / Year:** Proceedings of the **18th USENIX Security Symposium (USENIX Security 2009)**, pp. 317–334
- **URLs:**
  - USENIX session page: https://www.usenix.org/conference/usenixsecurity09/technical-sessions/presentation/efficient-data-structures-tamper-evident
  - ACM DL: https://dl.acm.org/doi/10.5555/1855768.1855788
  - Project / reference implementation (`edu.rice.historytree`, supports Merkle aggregation): http://tamperevident.cs.rice.edu/Logging.html
- **Note on sourcing:** primary PDF mirrors (usenix.org/legacy, tamperevident.cs.rice.edu, course slides) were unreachable / non-parseable at fetch time (HTTP 403 / ECONNREFUSED / binary-stream). The summary below reproduces the paper's well-established threat model and constructions; figures/quotes are attributed conservatively and exact wording should be re-verified against the canonical PDF before being quoted as verbatim in a regulator-facing artifact.

---

## 2. Faithful structured summary

### 2.1 Threat model — the **untrusted logger**

The paper's central setting is a logging system in which **the logger itself is not trusted**. Three parties:

- **Clients** generate events and submit them to the logger; they want assurance their events are durably and correctly recorded.
- **The logger** stores events and answers queries. It is **untrusted** — it may be compromised, malicious, or simply buggy, and may try to alter, delete, reorder, or selectively present log entries.
- **Auditors** challenge the logger to *prove* it is behaving correctly. The system's tamper-evidence comes from the logger being **unable to lie to auditors without being caught**.

The goal is **tamper-evidence**, not tamper-*prevention*: a malicious logger *can* corrupt its own state, but any such corruption becomes **detectable** through the proofs auditors demand.

### 2.2 Why hash chains alone are insufficient (the load-bearing argument)

A naïve append-only log links each entry to the previous via a hash (`h_i = H(event_i || h_{i-1})`). The paper shows this is **not enough** against an untrusted logger:

- **Truncation / rollback.** A hash chain proves each retained entry follows its predecessor, but it does **not** prevent the logger from **dropping entries off the end** (truncating the log) and presenting a shorter-but-internally-consistent chain. Nothing in the chain commits the logger to *how long* the log is.
- **Equivocation / forking ("showing different views").** The most dangerous attack: the logger maintains **two divergent histories** and shows **different versions of the log to different auditors/clients**. Each view is internally hash-consistent, so no single auditor inspecting one chain can detect the fork. Detection requires **comparing commitments across auditors** (gossip).
- **Cost of verifying old commitments.** Prior tamper-evident schemes required **linear** work/proof size to prove that a new commitment is consistent with an old one (that the log is append-only), which does not scale.

> Faithful paraphrase of the paper's framing: the untrusted logger is *kept honest only by auditors who can challenge it to prove (a) that a claimed event is present in the log, and (b) that the current log is a consistent superset of any previously published version.* Without an efficient consistency proof, an untrusted logger can equivocate or truncate undetectably.

### 2.3 The **history tree**

The paper's core contribution is the **history tree**: a versioned Merkle tree over an append-only log that supports efficient proofs as the log grows.

- It is a Merkle tree whose leaves are the logged events in order; as events are appended, the tree grows and the root changes.
- The logger publishes a **commitment `C_n`** (the tree root) after `n` events — a signed digest of the entire log state at version `n` (analogous to RFC 6962's Signed Tree Head).
- **Membership proof:** prove a given event is at a given position under commitment `C_n` — **O(log n)** size.
- **Incremental / consistency proof:** prove that commitment `C_n` (newer) is consistent with an earlier commitment `C_m` (`m ≤ n`) — i.e. the version-`m` log is a **prefix** of the version-`n` log, so nothing earlier was altered or deleted — also **O(log n)** size.

This logarithmic incremental proof is the key efficiency win over prior linear constructions, and it is what makes **continuous, cheap auditing** practical.

### 2.4 Auditors + gossip defeat equivocation

Because each commitment `C_n` is a compact, signed digest of the whole log, **auditors can exchange (gossip) commitments**. If the logger ever forked the history, two auditors holding commitments from the two branches will find **no valid consistency proof** linking them — the equivocation is exposed. Tamper-evidence thus rests on: signed commitments + efficient consistency proofs + multiple independent auditors comparing commitments.

### 2.5 Merkle aggregation

The history tree supports **Merkle aggregation**: annotating tree nodes with aggregate attributes (e.g. sums, maxima) that are bound into the hashes, enabling **authenticated queries over the log** (e.g. "the total of attribute X over all entries") whose answers are themselves provable against the commitment, without trusting the logger's arithmetic.

---

## 3. Best parts to take → mapped to the AutoFirm C9 control

| Crosby–Wallach concept | AutoFirm C9 control it grounds |
| --- | --- |
| **Untrusted-logger threat model** | C9 treats the **agent that incurs cost as an untrusted reporter**. The agent is the "client" submitting events; it must **never** be trusted to state its own cost-of-record. The ledger writer + reconciler play the auditor role. |
| **Truncation attack** | Justifies storing cost as a **history tree / RFC-6962 log with consistency proofs**, not a plain running counter or hash chain — so a rogue agent or compromised process **cannot drop spend off the end** to stay under a budget cap. Directly defeats the *silent under-reporting / cap-evasion during an unattended multi-hour run*. |
| **Equivocation / forking ("different views to different auditors")** | C9 publishes **signed cost commitments** that the reconciliation engine, the budget-enforcer, and the North-Star overseer each fetch **independently and gossip/compare**. A compromised component cannot show finance one cost view and the cap-enforcer another. |
| **O(log n) membership + incremental proofs** | Makes **continuous reconciliation cheap**: every cost event is provable against the published commitment, and each new commitment is provably append-only vs. the last — enabling per-tick auditing across a long autonomous run without linear blow-up. |
| **Merkle aggregation (authenticated sums)** | The **budget-cap check is an authenticated aggregate**: total spend per tenant/agent/window is computed as a Merkle-aggregated sum bound into the commitment, so the *cap decision itself* is provable and cannot be fed a fabricated total. |

**Most dangerous attack class this source names for C9:** **equivocation combined with truncation by a compromised cost reporter** — quietly under-reporting (or truncating) its own spend so the cap-enforcer sees a low total while spend continues, during an unattended run. The mitigation is structural: cost lives in a history-tree log with append-only consistency proofs and *independent* auditors comparing signed commitments — never a single self-reported number.
