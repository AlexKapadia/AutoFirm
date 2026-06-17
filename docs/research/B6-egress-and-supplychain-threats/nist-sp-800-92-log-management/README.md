# NIST SP 800-92 — *Guide to Computer Security Log Management* (log integrity, access restriction, separation)

> Research note for AutoFirm component **C9 — Cost-Data Integrity & Tamper-Evident Cost Logging**.
> This source grounds the *operational integrity controls* around the cost ledger: protecting log integrity in storage/transit, restricting who can write the authoritative record, and detecting unauthorized modification.

---

## 1. Full citation

- **Title:** *Guide to Computer Security Log Management* (NIST Special Publication 800-92)
- **Authors:** Karen Kent, Murugiah Souppaya (NIST)
- **Publisher / Year:** U.S. National Institute of Standards and Technology, **September 2006**
- **URL (canonical PDF):** https://nvlpubs.nist.gov/nistpubs/legacy/sp/nistspecialpublication800-92.pdf
- **Landing page:** https://csrc.nist.gov/pubs/sp/800/92/final
- **Revision in progress (informative):** *NIST SP 800-92r1 ipd — Cybersecurity Log Management* — https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-92r1.ipd.pdf
- **Sourcing note:** the canonical PDF was retrieved but could not be machine-parsed into text by the fetch tool (1.7 MB binary stream). The summary below reflects SP 800-92's well-established, widely-cited guidance on log protection; specific control wording should be re-verified against the canonical PDF before being quoted verbatim in a regulator-facing artifact.

---

## 2. Faithful structured summary

SP 800-92 is NIST's foundational guidance on planning, developing, and operating a **security log-management** capability. For C9 the relevant theme is **protecting the confidentiality and integrity of log data** so that records cannot be altered or destroyed undetectably.

### 2.1 Logs must be protected from alteration and destruction

The guide stresses that logs *"contain records of system and network security"* and must be **protected from breaches of their confidentiality and integrity**. It warns that logs **improperly secured in storage or in transit** are *"susceptible to intentional and unintentional alteration and destruction,"* and that such compromise *"could … allow malicious activities to go undetected."* The integrity of **archived** logs must be protected as well.

### 2.2 Recommended log-integrity controls

SP 800-92 recommends standard mechanisms to make tampering detectable and to harden storage, including:

- **Cryptographic integrity protection** — message digests / checksums and **digital signatures** over log records so that unauthorized modification is detectable.
- **Write-once / append-only storage** (e.g. write-once media) so committed records cannot be overwritten.
- **File-integrity / hashing checks** to detect after-the-fact modification.
- **Protecting log data in transit** (e.g. transmitting logs over an encrypted/authenticated channel to a central log server).

### 2.3 Access restriction & separation (least privilege)

The guide emphasises **restricting access to log data** and applying least privilege: only authorized roles may read or manage logs, and — critically for tamper-evidence — log integrity is strengthened when logs are **moved off the generating host to a separate, hardened log server** so that compromise of the monitored system does not grant the ability to rewrite the authoritative log. Centralisation + restricted write access supports the separation of "the system being logged" from "the system that holds the record of record."

### 2.4 Purpose: detection + auditability

The objective of these controls is to **detect unauthorized modification or destruction** of log data and to preserve logs as **reliable evidence** for audit and investigation. (The forthcoming r1 revision reframes log management around modern, high-volume cybersecurity needs but retains integrity/confidentiality protection as a core requirement.)

---

## 3. Best parts to take → mapped to the AutoFirm C9 control

| SP 800-92 control | AutoFirm C9 control it grounds |
| --- | --- |
| **Cryptographic integrity (digests/signatures) over log records** | Reinforces C9's RFC-6962/history-tree design: each cost record is hashed and the tree root is **signed** (Signed Cost-Tree Head). Tampering is cryptographically detectable, not merely policy-prohibited. |
| **Write-once / append-only storage** | The cost ledger is **append-only** at the storage layer (no in-place update/delete path), satisfying NIST's write-once intent and making the *hide-spend-by-editing* attack physically unavailable. |
| **Protect logs in transit** | Cost events and reconciliation traffic to/from the provider billing API travel over **TLS/authenticated channels** (AutoFirm §5.6 "TLS in transit"); attested-usage data is integrity-protected end to end. |
| **Restrict access / least privilege to logs** | The cost-of-record ledger is writable **only** by the deterministic cost computer + reconciler (scoped credentials); **agents have no write path** to it. Directly enforces *"the spender is not the scorekeeper."* |
| **Separate the logging system from the logged system** | The cost ledger is **decoupled from the agents** that incur cost — a compromised agent host cannot reach in and rewrite the authoritative record, mirroring NIST's "ship logs to a separate hardened log server." |
| **Purpose: detect unauthorized modification, preserve evidence** | Frames C9's audit goal: the cost ledger is **regulator-grade evidence** — provably unaltered, with any tampering detectable — feeding the `evidence/` showcase and the reconciliation/alert path. |

**Key C9 framing this source supports:** NIST SP 800-92 supplies the *operational hardening* that surrounds the cryptographic ledger — append-only storage, signed/hashed records, encrypted transit, least-privilege write access, and physical separation of the cost-record store from the spending agents. Together with RFC-6962 (the verifiable container), Crosby–Wallach (why hash chains alone fail), and FinOps/COSO reconciliation (cost is checked against the provider's meter, never self-reported), it closes C9's loop: **an agent can neither choose its cost-of-record, edit it after the fact, nor hide it — and any attempt is detectable.**
