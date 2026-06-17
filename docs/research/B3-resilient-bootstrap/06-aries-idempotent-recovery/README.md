# W3 / B3-06 — ARIES: "Repeating History" + Idempotent Redo via LSN (Why Replay-After-Crash Is Safe)

**Workstream:** W3 — resilient, idempotent bootstrap that can crash mid-apply and resume safely.
**Research question:** What is the canonical recovery principle that makes it *safe to replay* a sequence of completed operations after a crash without double-applying them — and how does ARIES guarantee idempotent redo?
**Status:** **Secondary / reinforcing source.** We take only the *redo-from-log / idempotent-replay* principle and the *repeating-history* recovery idea. The full ARIES locking / partial-rollback / CLR machinery is out of scope for W3.
**Date accessed:** 2026-06-17.

---

## 1. Full Citation

1. **C. Mohan, D. Haderle, B. Lindsay, H. Pirahesh, P. Schwarz — "ARIES: A Transaction Recovery Method Supporting Fine-Granularity Locking and Partial Rollbacks Using Write-Ahead Logging."** *ACM Transactions on Database Systems (TODS)*, Vol. 17, No. 1, March 1992, pp. 94–162. DOI: 10.1145/128765.128770. ACM DL: https://dl.acm.org/doi/10.1145/128765.128770 — dblp: https://dblp.org/rec/journals/tods/MohanHLPS92.html — **GRADE: High** (peer-reviewed; the foundational primary reference for write-ahead-logging recovery; implemented in IBM DB2, OS/2 EE Database Manager, Starburst, QuickSilver, Wisconsin EXODUS/Gamma).
2. **"the morning paper" (A. Colyer) faithful summary of ARIES.** URL: https://blog.acolyer.org/2016/01/08/aries/ — accessed 2026-06-17 — **GRADE: Medium-High** (secondary, high-fidelity; used to reproduce the three principles and the LSN-idempotency rule verbatim).

---

## 2. Faithful Structured Summary

### 2.1 The three principles of ARIES (reproduced)

1. **Write-Ahead Logging (WAL):** "the log records representing changes to some data must already be on stable storage before the changed data is allowed to replace the previous version" — i.e. **the log is durable before the data.** The log is the authoritative record of intent.
2. **Repeating History During Redo:** on restart, "ARIES repeats history, with respect to those updates logged on stable storage (i.e. in the log), but whose effects on the database pages did not get reflected on nonvolatile storage." Recovery **first re-applies every logged update — including those of uncommitted ("loser") transactions — to bring the system exactly back to its pre-crash state**, and only then undoes the losers.
3. **Logging Changes During Undo:** rollbacks are themselves logged (via compensation log records, CLRs), so a crash *during recovery* is also recoverable. *(Out of scope for W3 — listed for fidelity only.)*

### 2.2 "Repeating history" defined (the part W3 cares about)

The key recovery insight: rather than trying to figure out a clever minimal-repair, **recovery deterministically replays the durable log forward from a checkpoint, reconstructing the exact pre-failure state.** Because the log is the source of truth and replay is forward and deterministic, the post-recovery state is well-defined regardless of *when* the crash happened.

### 2.3 LSN-based idempotency — why replay is SAFE to repeat (reproduced EXACTLY)

The danger of any "replay the log" scheme is **double-application**: re-doing an update that *already* reached stable storage would corrupt state. ARIES eliminates this with the **Log Sequence Number (LSN)**:

> "ARIES uses a log sequence number (LSN) in each page to correlate the state of a page with respect to logged updates of that page."

The redo rule (verbatim):

> "A log record's update will be redone **if the affected page's LSN is less than the log record's LSN**."

Mechanism: every page stores the LSN of the **most recent update already reflected in it**. During redo, for each log record ARIES compares `page.LSN` to `record.LSN`:
- `page.LSN < record.LSN` → the update is **not yet reflected** → **re-apply it.**
- `page.LSN >= record.LSN` → the update is **already reflected** → **skip it.**

This comparison is what makes redo **idempotent**: replaying the same log any number of times converges to the same correct state, because each individual update is applied **at most once per page**. "already-applied changes are skipped, preventing duplicate application."

### 2.4 The three recovery phases (context)

- **Analysis** — scan forward from the last checkpoint; determine the dirty pages and the set of in-flight transactions at crash time.
- **Redo** — **repeat history**: re-apply all logged updates (idempotently, via the LSN rule) to restore the exact pre-crash state.
- **Undo** — roll back the loser (uncommitted) transactions in reverse order, logging the undos via CLRs. *(W3 has no "undo" — its steps are forward-only and idempotent; see §3.)*

### 2.5 Why this generalises beyond databases

The paper explicitly states ARIES "is applicable not only to database management systems but also to persistent object-oriented languages, **recoverable file systems and transaction-based operating systems**" — i.e. the redo-from-log + idempotency-via-marker pattern is a general crash-recovery principle, not a DB-only trick. That is exactly why it ports to a bootstrap's completed-steps ledger.

---

## 3. Best Parts to Take — mapped to W3 (resilient bootstrap)

W3's bootstrap applies an ordered list of steps; a crash can hit between or during any step. ARIES gives us the principle that makes **resume = safe forward replay**.

1. **"Repeating history" → resume by re-running the step list from the top, not by guessing where it stopped.** On restart, W3 walks its ordered steps in sequence — the same deterministic forward pass ARIES's redo phase performs. The durable completed-steps ledger (B3-05, atomic-rename) plays the role of ARIES's **log on stable storage**.
2. **Idempotent redo via a per-step `check()` ≈ the LSN comparison.** ARIES skips a redo when `page.LSN >= record.LSN` — the update is already reflected. W3's analogue: **each step exposes a `check()` (a "is this already done?" probe). If `check()` passes, resume skips the step; otherwise it applies it.** This is the LSN idempotency rule expressed as a desired-state check — the redo is "redo-only" (forward-only), never undo. A step that was half-applied before the crash is simply re-applied; because each step is idempotent, re-applying a fully-or-partially-done step converges to the same correct state.
3. **Log-before-data discipline → mark-after-effect (and rely on `check()` for the gap).** ARIES insists the log is durable before the data. W3's safe ordering: perform the step's effect, then atomically append/replace the ledger marking it done. If a crash lands **after the effect but before the marker**, the ledger under-counts — but `check()` detects the already-applied effect on resume and skips re-doing it (or harmlessly re-applies it, since steps are idempotent). The ledger is an *optimisation/audit record*; **`check()` is the real idempotency guarantee** — exactly ARIES's "skip if already reflected."
4. **Forward-only is simpler than full ARIES — and that's deliberate (Simplicity First).** W3 deliberately takes **only redo/repeating-history + idempotency**, and drops undo/CLR/fine-grained-locking. Bootstrap steps are designed to be **idempotent and forward-only**, so there is no "loser transaction" to roll back — eliminating the most complex half of ARIES while keeping the crash-safety guarantee.
5. **Determinism + zero-error replay.** Like ARIES's deterministic redo, W3's resume must produce **identical results on repeated runs** (CLAUDE.md determinism + zero-numerical-error bars). Property/determinism tests: crash-inject between every (effect, marker) boundary and after every step, then assert the resumed bootstrap reaches the identical final state as an uninterrupted run.

### Cross-link to A3 (long-horizon autonomy)
> **A3/08 (García-Molina & Salem, sagas)** uses a *log of completed forward steps and pending compensations* to drive recovery of long-running business workflows; **A3/09 (Elnozahy et al., rollback-recovery survey)** surveys checkpoint + message-log replay for long-running distributed processes. ARIES is the **canonical, foundational redo-from-log + LSN-idempotency mechanism those higher-level patterns inherit** — a saga's forward-recovery replay and a message-log replay are both "repeat history idempotently," and both depend on a per-step *already-done* marker analogous to ARIES's LSN. **A3 = agent/business-level recovery semantics (compensation, coordinated rollback over long horizons); B3 = the bootstrap-level crash-resume primitive (idempotent forward replay of a step list from a crash-atomic ledger).** B3-06 supplies the *why replay is safe* principle; B3-05 supplies the *how the ledger is written crash-atomically*; A3/08+A3/09 build the long-horizon semantics on top. Complementary, non-overlapping layers.
