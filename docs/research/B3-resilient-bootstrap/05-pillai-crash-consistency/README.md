# W3 / B3-05 — Crash-Consistent State via Atomic Rename: Why `write-temp → fsync → rename` Is the Basis of a Crash-Safe Checkpoint Record

**Workstream:** W3 — resilient, idempotent bootstrap that can crash mid-apply and resume safely from durable state (filesystem + version control).
**Research question:** What is the *correct* way to write a checkpoint / state-ledger record to the filesystem so that a crash at any instant leaves the record either fully-old or fully-new — never torn — and why is the atomic-rename protocol the right primitive for it?
**Date accessed:** 2026-06-17.

---

## 1. Full Citations

1. **T. S. Pillai, V. Chidambaram, R. Alagappan, S. Al-Kiswany, A. C. Arpaci-Dusseau, R. H. Arpaci-Dusseau — "All File Systems Are Not Created Equal: On the Complexity of Crafting Crash-Consistent Applications."** *Proceedings of the 11th USENIX Symposium on Operating Systems Design and Implementation (OSDI '14)*, Broomfield, CO, October 2014, pp. 433–448. University of Wisconsin–Madison. USENIX presentation page: https://www.usenix.org/conference/osdi14/technical-sessions/presentation/pillai — ACM DL: https://dl.acm.org/doi/10.5555/2685048.2685082 — **GRADE: High** (peer-reviewed, the seminal primary source on application-level crash consistency; this is THE key source for W3). Note: the USENIX page returned HTTP 403 on direct fetch this pass; author list, venue, and headline findings reproduced from the USENIX/ACM/Illinois-Experts records and the faithful technical summary below.
2. **A. Rajimwale et al. / "the morning paper" (A. Colyer) faithful technical summary of Pillai et al.** URL: https://blog.acolyer.org/2016/02/11/fs-not-equal/ — accessed 2026-06-17 — **GRADE: Medium-High** (secondary but high-fidelity, quotes the paper's atomicity/ordering distinctions verbatim; used to reproduce phrasing, not as the primary).
3. **Murat Demirbas — paper review of Pillai et al. (OSDI'14).** URL: http://muratbuffalo.blogspot.com/2015/04/all-file-systems-are-not-created-equal.html — accessed 2026-06-17 — **GRADE: Medium** (secondary review; corroborates persistence = atomicity + ordering).
4. **Linux Kernel Mailing List / POSIX `rename(2)` discussions on the safe atomic-rename sequence** (Ts'o, Hellwig et al.). URLs: https://lkml.iu.edu/hypermail/linux/kernel/0904.1/01180.html (safe/unsafe atomic `rename()`) and https://lkml.iu.edu/hypermail/linux/kernel/1011.3/02074.html (atomic non-durable file write API) — accessed 2026-06-17 — **GRADE: High** (primary engineering sources; reproduce the exact `fsync(tmp) → rename → fsync(dir)` sequence and POSIX rename-atomicity semantics).
5. **`python-atomicwrites` documentation** — implementation reference for the same protocol. URL: https://python-atomicwrites.readthedocs.io/ — accessed 2026-06-17 — **GRADE: Medium** (corroborating implementation reference; relevant because W3 is Python).

---

## 2. Faithful Structured Summary

### 2.1 The core finding of Pillai et al. (OSDI '14)

The paper presents the **first comprehensive study of application-level crash-consistency protocols** layered on modern file systems. Its central result:

> Applications use complex update protocols to persist state, and the **correctness of these protocols is highly dependent on subtle behaviours of the underlying file system**, which the authors term **persistence properties**.

Across **11 file systems** and a set of widely-used applications, they found **60 crash vulnerabilities** — points where an application's update protocol assumes a persistence property the file system does not actually guarantee. They built two tools: **BOB** (empirically tests which persistence properties a file system provides) and **ALICE** (analyses an application's update protocol and finds the crash vulnerabilities).

### 2.2 "Persistence" = atomicity + ordering (the two properties that matter)

The paper decomposes crash behaviour into two independent **persistence properties**:

- **Atomicity (of a single system call):** whether the updates from *one* system call complete entirely or not at all. The paper's own example: a `write` might leave the file size updated **but the content not written** — i.e. a torn single-call update.
- **Ordering (between system calls):** whether multiple system calls persist in the order they were issued. The paper's example: if two calls persist out of order, after a crash `f2` might contain `"qq"` **while `f1` does not yet contain `"pp"`** — even though `f1` was written first.

> "persistence properties vary widely among file systems, and even among different configurations of the same file system … it is risky to assume that any particular property will be supported by all file systems."

**Out-of-order persistence was the single largest failure mode** — 27 of the 60 vulnerabilities came from applications assuming ordering the file system did not provide.

### 2.3 Why `rename()` is the right primitive — atomic replacement

POSIX `rename(2)` is the one widely-relied-upon **atomic replacement** operation:

> Atomicity in POSIX means the filename "will only appear in one place, never two or zero, as represented by the kernel to userland."

So **at the directory-entry level, a crash leaves the target name pointing at either the old inode or the new inode — never a partially-overwritten, torn file.** This is exactly the property a checkpoint record needs: a reader (or a resuming process) always sees a *complete* prior record or a *complete* new record.

**Crucial caveat the paper hammers home:** rename being *operationally* atomic in the running kernel **does not by itself guarantee atomicity across a crash/reboot**. The directory-entry swap can persist *before* the new file's data does, so a naïve `write(tmp); rename(tmp, target)` can — on a crash — leave the target name pointing at a **zero-length / partially-written file**. The atomicity of rename only helps if the new file's data is **already durable before the rename's effect persists.** Ordering must be enforced explicitly.

### 2.4 The crash-safe atomic-update protocol (reproduced EXACTLY)

The correct, portable sequence — the "safe rename" / "create-and-rename" protocol — is **five steps, in this order**:

```text
1. open/create a NEW temp file on the SAME filesystem (same directory) as the target
2. write() the full new contents to the temp file
3. fsync(tmp_fd)            # flush the temp file's DATA + metadata to stable storage
4. rename(tmp, target)      # atomic directory-entry swap: old-or-new, never torn
5. fsync(dir_fd)            # flush the PARENT DIRECTORY entry so the rename itself is durable
```

Verbatim from the primary engineering sources (source 4):

> "On POSIX, `fsync` is invoked on the temporary file after it is written (to flush file content and metadata), and on the parent directory after the file is moved (to flush filename)."

> "the common practice is to write updated data to a temporary file, ensure it's safe on stable storage, then rename the temporary file to the original file name, which ensures … other readers get one copy of the data or another."

**Why each step is load-bearing:**
- **Step 3 (`fsync(tmp)`) before step 4 (`rename`)** enforces the *ordering* the paper warns about: the new data is durable *before* the directory entry can flip. Skip it and a crash can yield the famous **zero-length-file** outcome ("the destructive rename succeeds, but the resulting file is zero-length").
- **Step 4 (`rename`) gives atomicity:** the target name is never observed as a torn file.
- **Step 5 (`fsync(dir)`)** makes the *rename itself* durable; without it the directory entry may be lost on crash and the target reverts to the old inode (or vanishes).
- **Same-filesystem requirement:** `rename` is only atomic within one filesystem; across mount points it degrades to copy-then-unlink, which is not atomic.

This protocol is the basis of every crash-safe checkpoint/state-record write: **the on-disk state record is replaced as one indivisible step**, so a crash mid-write can never corrupt the previously-good record.

---

## 3. Best Parts to Take — mapped to W3 (resilient bootstrap)

The bootstrap's durable resume state must survive a crash at **any** instant during `apply`. Pillai et al. tells us exactly how to write it.

1. **Write the completed-steps ledger / state record via atomic rename, never in place.** W3's durable ledger (which steps have completed) is written with the five-step `write-temp → fsync → rename → fsync(dir)` protocol. A crash mid-apply therefore leaves the ledger either fully-old (last good checkpoint) or fully-new — **never torn**. This is a hard correctness invariant, not a nicety: a torn ledger would make resume undecidable.
2. **Enforce ordering explicitly — do not trust the filesystem's default.** The biggest failure class in the paper is out-of-order persistence. W3 must `fsync` the temp record *before* the rename, and `fsync` the directory *after*, on every checkpoint write. Never assume the host filesystem orders these for us.
3. **One ledger file, replaced atomically, is the single source of "what's done."** Resume reads the durable ledger (plus git — see cross-link) to learn which steps already completed; because the ledger is always a complete record, resume logic never has to reason about partial writes.
4. **Same-directory temp + atomic replace; no lock files, no multi-file protocols.** The paper shows multi-file / ordering-dependent protocols are where vulnerabilities breed. W3 keeps the protocol to a single atomically-replaced file to minimise the persistence properties it depends on.
5. **Test it like the paper does.** W3's crash-resume tests should inject crashes between each of the five steps (and reorder fsyncs) and assert the resumed bootstrap is always correct — the ALICE/BOB philosophy of *testing the persistence assumptions*, not trusting them.

### Cross-link to A3 (long-horizon autonomy)
> **A3/08 (García-Molina & Salem, sagas / compensating transactions)** and **A3/09 (Elnozahy et al., rollback-recovery / checkpointing survey)** operate at the **long-horizon agent-work** layer — multi-step business operations that may need *semantic* compensation or coordinated rollback after partial failure. **B3 (this folder) operates one layer below them, at the bootstrap level:** it concerns how a *single durable state record / checkpoint* is physically written to disk so that it is crash-atomic in the first place. A3/09's checkpoint *is only as good as the atomic-write primitive underneath it* — this is that primitive. A3/08's saga log (the record of which forward steps have run and which compensations are pending) must itself be persisted crash-atomically — again, via the protocol here. **B3 = the crash-safe substrate; A3 = the agent-level recovery semantics built on top of it.** They complement, they do not overlap.
