# 01 — Event Sourcing & CQRS as an append-only growth log

> Workstream B4 (dynamic capability registry). This source establishes the
> foundational architecture for W4: **current capability state = pure replay of
> an append-only event stream.** It is the load-bearing pattern beneath the
> `CapabilityRegistryEvent` log and the `live registry derived by pure replay`.

## Full citation

- **Martin Fowler, "Event Sourcing"**, martinfowler.com (eaaDev), first published
  **2005**. <https://martinfowler.com/eaaDev/EventSourcing.html>
- Supporting / corroborating (read for the CQRS split and snapshot mechanics):
  - **Greg Young**, *CQRS Documents* / "CQRS and Event Sourcing" — the canonical
    statement that the write model is an append-only event stream and read models
    are projections. (Young coined CQRS; primary community-authoritative source.)
  - **Microsoft Azure Architecture Center**, "Event Sourcing pattern".
    <https://learn.microsoft.com/azure/architecture/patterns/event-sourcing>
    (Professional/primary engineering reference; used only to corroborate the
    snapshot + projection mechanics, not to define the pattern.)

## Faithful structured summary (principles reproduced exactly)

**Definition (Fowler, verbatim):** *"Capture all changes to an application state
as a sequence of events."* — and — *"Event Sourcing ensures that all changes to
application state are stored as a sequence of events."*

**Core mechanism — state is derived, never stored as truth.** The current state is
reconstructed by *"starting from a blank application state and then applying the
events to reach the desired state."* The event log is the system of record;
application state is *"purely derivable from the event log."* This is the precise
property W4 relies on: **the live registry is a deterministic fold over the log.**

State reconstruction is a left fold:

```
state_n = fold(apply, EMPTY_STATE, [e_0, e_1, ..., e_{n-1}])
        = apply(apply(... apply(EMPTY_STATE, e_0) ..., e_{n-2}), e_{n-1})
```

`apply` must be a **pure function** of `(state, event)`. Given the same ordered
event sequence, replay yields identical state on every run (determinism).

**Append-only store.** Fowler: *"use an append-only store to record the full
series of actions taken on that data."* Events are never mutated or deleted in
place; correction is a *new compensating event*, never an edit. This is what makes
the log a faithful, reconstructable audit trail.

**Snapshots (performance optimisation, NOT source of truth).** To avoid replaying
from genesis each time, a system may persist a *snapshot* of state at sequence `k`,
then replay only `[e_k ... e_n]`. Fowler: store the current application state and
*"if someone wants the special features that Event Sourcing offers then that
additional capability is built on top."* Critically, a snapshot is **cache, not
record** — it must be reconstructible from the log, and is discardable.

**CQRS pairing (Young).** Command Query Responsibility Segregation separates the
*write model* (the append-only command/event stream — single source of truth) from
*read models* (projections rebuilt from the stream, optimised per query). Multiple
independent read models (timeline, graph, count) can be regenerated from the same
log without touching the write side. This is exactly how W4 serves *several*
visual views (growth timeline, role→capability graph) from *one* event log.

**Why this gives reconstructable, auditable growth.** Because state is a pure
function of an immutable ordered log: (a) any historical state is recoverable by
replaying to a chosen sequence (`org-evolution replay`); (b) the *difference*
between two states is exactly the slice of events between them (capability growth
is literally visible as log segments); (c) the log is tamper-evident if combined
with a hash chain (see source 02-rfc6962 cross-link); (d) no "current value"
column can silently drift from history, because there is no authoritative current
value — only the fold.

## Best parts to take (mapped to the W4 design)

1. **`CapabilityRegistryEvent` = the append-only event stream.** Adopt Fowler's
   rule literally: capabilities are never stored as a mutable list. The registry's
   "current capability set" is the **pure replay** (`fold`) of the event log.
   *Maps to:* W4 "live registry derived by pure replay".
2. **`apply(state, event)` is a pure, total, deterministic reducer.** No clocks,
   no I/O, no randomness inside the fold — identical input sequence ⇒ identical
   capability set, every run. Test with property-based determinism over N repeats
   and over shuffled-but-causally-valid sequences. *Maps to:* CLAUDE.md §3.11
   determinism + W4 generality.
3. **Correction = compensating event, never mutation.** A withdrawn capability
   (e.g. role FIRED) is a *new* `CAPABILITY_RETIRED` event, not a deletion. The
   log only grows. *Maps to:* W4 "append-only / audited", CLAUDE.md §3.8 no-graveyard.
4. **CQRS read models = the visual showcase.** Build the timeline, the live
   role→capability graph, and the count-over-time series as *independent
   projections* of the one log, each regenerable on demand. Snapshots may
   accelerate replay at thousands of capabilities but are cache only. *Maps to:*
   W4 "how growth is SHOWN" + evidence/ showcase.
5. **Snapshots are an optimisation, never authority.** If a snapshot exists at seq
   `k`, it must equal `fold(apply, EMPTY, events[:k])` — test this invariant
   explicitly so a corrupt/forged snapshot can never become the truth. *Maps to:*
   security fail-closed (a snapshot that disagrees with replay is rejected).

## Cross-links

- **02 (RFC 6962)** — makes the append-only log *tamper-evident* via hash-chaining.
- Existing repo source: `A6-governance-and-auditability/06-rfc6962-certificate-transparency`.
- Existing repo source: `A6-governance-and-auditability/05-ma-tsudik-secure-logging`
  (forward-secure append-only logging — corroborates immutability guarantees).
