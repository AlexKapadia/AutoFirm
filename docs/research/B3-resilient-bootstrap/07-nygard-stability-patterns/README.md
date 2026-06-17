# Nygard — Stability Patterns (Circuit Breaker, Bulkhead, Fail Fast, Graceful Degradation)

> Research note for AutoFirm B3 (Resilient Bootstrap). Bar: institution-grade, primary-sourced
> (CLAUDE.md §3.3 / §4.6). Security distinction held to §5.6 (fail-closed by default).
> One folder per source; faithful structured summary + best-parts-to-take.

---

## 1. Citation

**Primary source.** Michael T. Nygard, *Release It! Design and Deploy Production-Ready
Software*, 2nd edition, The Pragmatic Bookshelf (Pragmatic Programmers), 2018. ISBN
978-1-68050-239-8. (1st edition 2007 — the edition that introduced and popularised the
Circuit Breaker pattern in software.)

- **Relevant material:** Part II, *Stability* — the **Stability Antipatterns** chapter
  (Cascading Failures, Chain Reactions, Slow Responses, Integration Points, Blocked Threads,
  Unbounded Result Sets) and the **Stability Patterns** chapter, which defines: **Timeouts**,
  **Circuit Breaker**, **Bulkheads**, **Steady State**, **Fail Fast**, **Let It Crash**,
  **Handshaking**, **Test Harnesses**, **Decoupling Middleware**, **Shed Load**, **Back
  Pressure**, **Governor**.

**Engineering reinforcement (capability-level fallback).** Netflix, *Hystrix Wiki — "How
it Works"* and *"Configuration"*, github.com/Netflix/Hystrix/wiki. Bulkhead via per-dependency
thread-pool isolation + `getFallback()` capability-level fallback. (Hystrix is now in
maintenance mode; cited as a faithful reference implementation of these patterns, not as a
recommended dependency.)

---

## 2. Faithful structured summary

### 2.1 Circuit Breaker — the three states (reproduced exactly)

The Circuit Breaker wraps a dangerous operation (typically a call to an integration point /
remote dependency) and **monitors for failures**. It is a finite state machine with **three
states**:

- **Closed** — *normal operation.* Calls pass straight through to the protected dependency.
  The breaker counts failures. While failures stay under the threshold, it remains Closed.
  When the **failure count crosses a configured threshold**, the breaker **trips** and
  transitions to **Open**.

- **Open** — *the dependency is presumed unhealthy.* Calls **fail immediately** (fail fast)
  **without attempting the dependency at all** — no thread is spent, no timeout is waited on.
  This is what protects the caller from being dragged down. The breaker stays Open for a
  configured **timeout / reset period**, after which it transitions to **Half-Open**.

- **Half-Open** — *trial / probe.* A **limited number of trial calls** are allowed through to
  test whether the dependency has recovered.
  - If the trial call(s) **succeed**, the breaker **resets to Closed** (normal operation
    resumes, failure count cleared).
  - If a trial call **fails**, the breaker **trips back to Open** and the timeout restarts.

State diagram (Nygard's model):

```
            failure threshold exceeded
   ┌───────────────────────────────────────────┐
   │                                             ▼
[CLOSED] ──(success: stay closed)        [OPEN] ──(reset timeout elapsed)──> [HALF-OPEN]
   ▲                                                                            │  │
   │ trial call SUCCEEDS (reset)                                                │  │
   └────────────────────────────────────────────────────────────────────────────┘
                                              trial call FAILS (re-trip) ◄──────┘
```

**Intent (exact).** Stop doing the thing that hurts. The Circuit Breaker prevents a failing
dependency from causing repeated, slow, resource-consuming failures in the caller; in the Open
state it **fails fast** and gives the dependency time to recover. State changes should be
**logged/monitored and alertable** — a tripped breaker is an operationally significant event,
not a silent one.

### 2.2 Bulkhead — partition resources so one failure can't sink the ship

Named after the **watertight compartments (bulkheads) in a ship's hull**: if the hull is
breached, only the breached compartment floods; the bulkheads keep the rest of the ship dry so
**the whole ship does not sink**. Applied to software, the Bulkhead pattern **partitions a
system's resources** (thread pools, connection pools, processes, instances, capacity) so that a
failure or resource exhaustion in **one partition is contained and cannot consume the resources
needed by the others**. One sick dependency therefore **cannot starve the entire process** of
threads/connections and bring down unrelated, healthy capability.

**Hystrix reinforcement.** Hystrix implements the Bulkhead by giving **each dependency its own
small, fixed-size thread pool**. When that pool is exhausted, commands for *that* dependency are
**immediately rejected** (and the fallback runs), so a single misbehaving dependency "cannot use
up all of the threads for failing external dependencies" — other dependencies keep their own
threads. The Hystrix tagline is literally *"when one service can sink the ship"* — the bulkhead
is what stops it.

### 2.3 Fail Fast

If you can determine **in advance** that a call will fail — a required resource (key,
connection, downstream) is unavailable, or a Circuit Breaker is Open — then **fail immediately**
rather than making the caller wait for a timeout. A fast failure is far cheaper than a slow one:
it returns resources (threads, sockets) instantly and lets the caller take its alternative path.
Slow responses are worse than no response, because they tie up the caller's resources — Fail
Fast is the antidote to the "Slow Responses" / "Blocked Threads" antipatterns.

### 2.4 Graceful Degradation (and Decoupling Middleware / Shed Load)

Rather than letting the loss of one capability take down the whole system, **degrade that
capability** and keep serving the rest. Nygard's supporting patterns:

- **Decoupling Middleware / asynchrony** — decouple components so a slow or absent dependency
  does not block the caller synchronously; the caller can proceed and the dependent feature is
  simply unavailable or deferred.
- **Shed Load / Back Pressure** — when overloaded, deliberately reject or slow incoming work at
  the boundary to keep the core stable, rather than collapsing under it.
- The combined effect: **a partial system is better than a dead system.** The optional feature
  goes dark; the platform stays up.

**Hystrix `getFallback()`** is the capability-level realisation: when a command fails, the
breaker is Open, or the bulkhead pool is exhausted, Hystrix invokes the command's **fallback**
(a cached value, a default, a "feature unavailable" response) instead of propagating the failure —
degrade *that* capability, keep the caller alive.

### 2.5 Fail-closed vs fail-open (security framing)

Nygard's stability patterns optimise for **availability** of non-critical features (degrade, don't
die). This must be read **together with** the security principle (AutoFirm CLAUDE.md §5.6, and the
classic fail-safe-defaults rule): a **security or compliance control fails CLOSED** — when a
permission, key, or check is missing or ambiguous it **refuses the action**, it does **not**
degrade to an insecure default. Graceful degradation applies to *non-critical features*;
**fail-closed applies to security**. The two are not in tension — you choose per capability:
degrade availability-oriented features, fail-closed on security/compliance ones. (Detailed
fail-open/fail-closed treatment is in the companion SRE note `08-google-sre-graceful-degradation`.)

---

## 3. Best-parts-to-take → AutoFirm W3 `degraded_mode_policy`

The W3 bootstrap/doctor decides, per optional dependency, what happens when it is **absent or
unreachable**. Nygard's patterns map directly onto a per-capability policy:

| Nygard pattern | W3 degraded-mode mechanism |
| --- | --- |
| **Bulkhead** | Each optional capability (a provider key, an external gateway) is an **isolated compartment** at bootstrap. A missing/unreachable one is contained to its own compartment: **it cannot block the rest of the bootstrap** or starve healthy capabilities. The platform comes UP with the working capabilities; only the affected one is dark. |
| **Circuit Breaker (Closed→Open→Half-Open)** | The **doctor/bootstrapper IS the breaker** for each capability. On repeated/initial failure to reach a dependency it **trips that capability Open** (capability marked `degraded`, fails fast — no hanging on dead gateways), **emits an audit event**, and **reports** it in the bootstrap report. On a reset interval it goes **Half-Open** and **re-probes**; on success the capability **resets to Closed** (re-enabled) — so a key/gateway that comes back is picked up automatically without a restart. |
| **Fail Fast** | A capability known-Open is short-circuited instantly — callers get an immediate "capability unavailable / degraded" instead of waiting on timeouts to a dead provider. |
| **Graceful Degradation / Decoupling / fallback (`getFallback`)** | A missing **non-critical** optional dependency → **disable/degrade ONLY that capability**, keep the platform UP, surface its degraded status. Where a sensible lower-fidelity fallback exists (cached/default), serve it and label it degraded. |
| **§5.6 fail-closed (security)** | A missing/ambiguous **security or compliance** capability (auth, secrets manager, audit sink, kill-switch, tenant-isolation check) **fails CLOSED — the bootstrap refuses to enable the dependent action**; it is **never** silently degraded to an insecure default. This is the hard exception to graceful degradation. |

**Concrete W3 rule per missing optional dependency:**
1. Detect absence/unreachability (probe at bootstrap).
2. **Classify the capability: security/compliance vs non-critical feature.**
3. If **non-critical** → **bulkhead-isolate + trip the breaker Open** for that capability:
   mark `degraded`, **emit an append-only audit event** (what capability, why, when), keep the
   platform UP, report it. Re-probe on the breaker's Half-Open interval; reset to Closed when it
   returns.
4. If **security/compliance** → **fail CLOSED**: refuse to enable the dependent action, audit
   the refusal. Do **not** degrade to insecure.
5. Never let one missing capability hard-block the whole bootstrap (anti-pattern: whole-platform
   block on one absent key).

### Design implications for the W3 degraded-mode policy table
1. **Add a `criticality` column** (`security` | `non-critical`) that **selects the failure mode**:
   `non-critical → degrade/bulkhead+breaker`, `security → fail-closed/refuse`. This is the single
   decision that keeps §5.6 intact while still keeping the platform up.
2. **Model each capability as a breaker with explicit state** (`closed/open/half-open` ⇒
   `enabled / degraded / probing`) plus a **mandatory audit event on every transition** and a
   **re-probe interval** — so degradation is observable, reversible, and auto-recovers when the
   key/gateway returns, never silent.

---

### Sources
- Michael T. Nygard, *Release It!* 2nd ed., Pragmatic Bookshelf, 2018 (1st ed. 2007).
- [Netflix/Hystrix Wiki — How it Works](https://github.com/Netflix/Hystrix/wiki/how-it-works)
- [Netflix/Hystrix Wiki — Configuration](https://github.com/Netflix/Hystrix/wiki/configuration)
