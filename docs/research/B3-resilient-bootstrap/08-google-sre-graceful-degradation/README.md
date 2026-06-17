# Google SRE — Graceful Degradation, Load Shedding & Fail-Static / Fail-Open vs Fail-Closed

> Research note for AutoFirm B3 (Resilient Bootstrap). Bar: institution-grade, primary-sourced
> (CLAUDE.md §3.3 / §4.6). Security distinction held to §5.6 (fail-closed by default).
> One folder per source; faithful structured summary + best-parts-to-take.

---

## 1. Citation

**Primary source.** Betsy Beyer, Chris Jones, Jennifer Petoff, and Niall Richard Murphy (eds.),
*Site Reliability Engineering: How Google Runs Production Systems*, O'Reilly Media, 2016. ISBN
978-1-491-92912-4. Free online edition: https://sre.google/sre-book/.

Relevant chapters:
- **Chapter 21 — Handling Overload.** Written by Alejandro Forero Cuervo; edited by Sarah
  Chavis. https://sre.google/sre-book/handling-overload/
- **Chapter 22 — Addressing Cascading Failures.** Written by Mike Ulrich.
  https://sre.google/sre-book/addressing-cascading-failures/

**Reinforcement (fail-static / defense-in-depth / fail-open vs fail-closed).** Heather Adkins,
Betsy Beyer, et al., *Building Secure and Reliable Systems*, O'Reilly, 2020 (free online),
**Chapter 8 — Design for Resilience** (graceful degradation, defense in depth, and the
**fail-safe / fail-secure** discussion). https://google.github.io/building-secure-and-reliable-systems/raw/ch08.html

---

## 2. Faithful structured summary

### 2.1 Graceful degradation — serve degraded (lower-fidelity) responses (Ch. 21, quoted)

> "One option for handling overload is to serve **degraded responses**: responses that are not
> as accurate as or that contain less data than normal responses, but that are easier to
> compute."

Examples given (Ch. 21): **searching only a percentage of candidates** instead of the entire
corpus, and **using locally-cached results** that may be stale but are cheaper to access.

Core philosophy (Ch. 21, quoted):

> "A well-behaved backend, supported by robust load balancing policies, should accept only the
> requests that it can process and reject the rest gracefully."

The progression is explicit (Ch. 21): when even degraded responses become impossible —

> "Under extreme overload, the service might not even be able to compute and serve degraded
> responses. At this point it may have no immediate option but to serve errors."

So the ladder is: **full response → degraded (lower-fidelity) response → reject gracefully
(load shed) → error.** Degrade before you shed; shed before you collapse.

### 2.2 Load shedding & graceful degradation (Ch. 22, quoted)

Load shedding **drops** incoming traffic as a server approaches overload (e.g. returning **HTTP
503** above a per-task resource threshold), to keep the server stable and doing useful work
rather than tipping into collapse.

> "**Graceful degradation** takes the concept of **load shedding** one step further by reducing
> the amount of work that needs to be performed."

> "a search application might only search a **subset of data stored in an in-memory cache**
> rather than the full on-disk database or **use a less-accurate (but faster) ranking
> algorithm** when overloaded."

Implementation guidance from Ch. 22: decide **which metrics trigger degradation** (CPU, latency,
queue length, thread usage), **what degraded mode does**, and **which layer implements it**;
keep degraded-mode paths exercised so they actually work when needed.

### 2.3 Preventing cascading failures when a dependency is unavailable (Ch. 22)

Principles directly relevant to "an optional dependency is absent/unreachable":
1. **Route downward, avoid intra-layer cycles** — keep the request path acyclic; don't let
   backends proxy to each other (it amplifies load during failure).
2. **Deadline propagation** — don't keep working on a request whose client deadline has expired;
   abandoned work is wasted resource that feeds cascading exhaustion.
3. **Test noncritical-backend failure explicitly** — verify that an **unavailable non-essential
   backend does NOT cause frontend resource exhaustion** or take the whole frontend down. This is
   the SRE statement of the bulkhead idea: a non-critical dependency going dark must not sink the
   ship.

### 2.4 Fail-static / fail-open vs fail-closed

**Fail-static** (from *Building Secure and Reliable Systems*, Ch. 8): when a dependency is
unavailable, a system should **"keep working with its last known good state"** rather than
crashing — e.g. continue serving the last good configuration / cached data instead of failing
when the config server is unreachable. The principle: **the absence of a dependency degrades to a
safe, stable, predictable behaviour, not to chaos.** It deliberately *limits the blast radius* of
a dependency outage and avoids a "thundering herd" recovery.

**Fail-open vs fail-closed** (the availability-vs-security tradeoff):
- **Fail-open** — when the system/check fails, it **allows** the action through. Chosen when
  **availability is prioritised over security**. (Classic example: a network appliance that, on
  failure, passes all traffic so connectivity is preserved.)
- **Fail-closed (fail-secure)** — when the system/check fails, it **denies/blocks** the action.
  Chosen when **security/safety is prioritised over availability**. (The appliance blocks all
  traffic on failure.)

**The rule.** The choice is **per capability, by what's at stake**: *fail-closed when
safety/security is primary; fail-open (degrade) only when availability is critical and the
residual risk is acceptable.* A **security or compliance check must fail CLOSED** — an
authorization, authentication, secret-resolution, or audit dependency that is missing or
ambiguous **must refuse the action**, never silently fall open to an insecure default. This is
the SRE/secure-systems statement of the same rule AutoFirm CLAUDE.md §5.6 mandates: *"Fail
closed: when a permission, key, or check is missing or ambiguous, refuse the action rather than
proceeding."*

---

## 3. Best-parts-to-take → AutoFirm W3 `degraded_mode_policy`

| SRE concept | W3 degraded-mode mechanism |
| --- | --- |
| **Graceful degradation (serve lower-fidelity)** | When an **optional, non-critical** dependency (a provider key, an external gateway) is absent/unreachable, **degrade ONLY that capability** — disable it or serve a lower-fidelity fallback (cached/default) — and **keep the platform UP**. Degrade the response; don't kill the system. |
| **Fail-static (last known good)** | Where a degraded capability has a safe last-known-good (cached config, last successful result), the bootstrapper serves **that** in degraded mode rather than erroring — predictable, bounded behaviour while the dependency is down. |
| **Load-shedding ladder (degrade → reject gracefully → error)** | A missing capability must **reject its own dependent requests gracefully** (clear "capability unavailable / degraded" status), not propagate an opaque crash; a missing capability must **never** become a whole-platform error. |
| **Test noncritical-backend failure (Ch. 22)** | A missing **non-critical** dependency **must not exhaust the bootstrap** or block unrelated capabilities — the bootstrap proves it stays up with that capability dark (bulkhead). |
| **Fail-open vs fail-closed (per capability)** | The policy table carries an explicit **fail mode per capability**: non-critical → **fail-open/degrade**; security/compliance → **fail-closed**. |
| **§5.6 fail-closed (binding)** | A missing/ambiguous **security or compliance** capability (auth, secrets manager, audit sink, kill-switch, tenant isolation) **fails CLOSED — refuse the dependent action and audit the refusal.** Never silently degrade to insecure. This overrides graceful degradation for security. |

**Per missing optional dependency, the W3 rule (SRE-grounded):**
1. Probe the dependency at bootstrap.
2. **Classify: security/compliance vs non-critical feature** → this selects fail-closed vs
   degrade.
3. **Non-critical** → graceful degradation: disable/degrade ONLY that capability (serve
   fail-static last-known-good where available), **emit an append-only audit event**, keep the
   platform UP and report the degraded status; re-probe and restore when it returns.
4. **Security/compliance** → **fail CLOSED**: refuse the dependent action, audit the refusal.
5. A non-critical missing dependency **must never** exhaust or hard-block the whole bootstrap
   (Ch. 22 "test noncritical-backend failure").

### Design implications for the W3 degraded-mode policy table
1. **`fail_mode` is a first-class column driven by `criticality`.** `non-critical →
   degrade (fail-open / fail-static)`; `security/compliance → fail-closed (refuse)`. This single
   classification reconciles SRE's availability-first degradation with §5.6's security-first
   refusal — they coexist, chosen per capability.
2. **Specify the degraded behaviour explicitly per capability** (the SRE "what does degraded mode
   do?" question): *which fallback* (disabled / last-known-good cached / lower-fidelity),
   *which trigger* (absent key vs unreachable gateway), *which audit event*, and *the re-probe
   interval that restores it* — so degradation is deliberate, observable, fail-static, and
   self-healing rather than ad hoc.

---

### Sources
- [Google SRE Book — Ch. 21 Handling Overload](https://sre.google/sre-book/handling-overload/)
- [Google SRE Book — Ch. 22 Addressing Cascading Failures](https://sre.google/sre-book/addressing-cascading-failures/)
- [Building Secure and Reliable Systems — Ch. 8 Design for Resilience](https://google.github.io/building-secure-and-reliable-systems/raw/ch08.html)
