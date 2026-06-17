# Circuit Breaker, Retry-with-Backoff-and-Jitter, and Bulkhead — Resilience Patterns

**Workstream:** B1 multi-model-egress — reliability layer for provider outages
**Scope:** Canonical, primary-sourced write-ups of the three failure-isolation patterns AutoFirm's
self-hosted gateway needs to survive upstream LLM-provider outages, rate-limits, and slow dependencies.

---

## 1. Full citations / URLs

1. **Martin Fowler, "CircuitBreaker"**, martinfowler.com, published **6 March 2014**.
   <https://martinfowler.com/bliki/CircuitBreaker.html>
   (Explicitly attributes the pattern's popularisation to Michael Nygard.)
2. **Michael T. Nygard, "Release It! Design and Deploy Production-Ready Software"**, Pragmatic Bookshelf
   (1st ed. 2007; 2nd ed. 2018). *The origin of the Circuit Breaker stability pattern.* Cited here via
   Fowler (above) and Microsoft (below), which both name *Release It!* as the source.
3. **Microsoft, "Circuit Breaker pattern"**, Azure Architecture Center (Microsoft Learn).
   Authors: claytonsiemens77 et al.; doc `ms.date` 2025-02-05, page updated 2026-06-03.
   <https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker>
4. **Marc Brooker, "Exponential Backoff And Jitter"**, AWS Architecture Blog, **4 March 2015**.
   <https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/>
5. **Microsoft, "Bulkhead pattern"**, Azure Architecture Center (Microsoft Learn).
   `ms.date` 2026-03-19, page updated 2026-06-03.
   <https://learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead>

---

## 2. Faithful structured summary

### 2.1 Circuit Breaker — origin

Fowler (2014): *"In his excellent book Release It, Michael Nygard popularized the Circuit Breaker pattern
to prevent this kind of catastrophic cascade."* The pattern wraps a protected call in an object that
**monitors recent failures and trips open** to stop calls that are likely to fail, instead of repeatedly
retrying. This both protects the caller (fast-fail instead of blocking on timeouts) and gives the failing
dependency room to recover.

### 2.2 The state machine — reproduced EXACTLY (three states)

A circuit breaker is a **state machine** acting as a proxy for an operation that might fail. The three
states and their transitions (verbatim semantics from Microsoft Azure Architecture Center, consistent with
Fowler and Nygard):

- **Closed** — *"The request from the application is routed to the operation. The proxy maintains a count of
  the number of recent failures. If the call to the operation is unsuccessful, the proxy increments this
  count. If the number of recent failures exceeds a specified threshold within a given time period, the
  proxy is placed into the Open state and starts a time-out timer. When the timer expires, the proxy is
  placed into the Half-Open state."*
- **Open** — *"The request from the application fails immediately and an exception is returned to the
  application."* (Fast-fail; the protected call is **not** made.)
- **Half-Open** — *"A limited number of requests from the application are allowed to pass through and invoke
  the operation. If these requests are successful, the circuit breaker assumes that the fault that caused
  the failure is fixed, and the circuit breaker switches to the Closed state. The failure counter is reset.
  If any request fails, the circuit breaker assumes that the fault is still present, so it reverts to the
  Open state. It restarts the time-out timer so that the system can recover from the failure."*

**Transitions (exact):**

| From | To | Trigger (verbatim/derived) |
| --- | --- | --- |
| Closed | Open | "the failure threshold is reached" (recent failures exceed the threshold within the interval) |
| Open | Half-Open | "the time-out timer expired" |
| Half-Open | Closed | "the success count threshold is reached" (N consecutive successes) → **failure counter reset** |
| Half-Open | Open | "the operation failed" → **restart the time-out timer** |

**Failure threshold (exact):** Microsoft — *"The failure threshold triggers the Open state only when a
specified number of failures occur during a specified interval."* The Closed-state failure counter is
**time-based and automatically resets at periodic intervals**, so occasional, spread-out failures do not
trip the breaker. Fowler's canonical sample uses a default **`failure_threshold = 5`** and a
**`reset_timeout = 0.1`** (seconds) — these are *example defaults*, not part of the pattern; AutoFirm must
tune them per dependency.

**Reset timeout (exact):** the time-out timer started on entering Open; on expiry the breaker moves to
Half-Open. Microsoft notes a common extension: an **increasing time-out timer** (open a few seconds first,
then escalate to minutes if the fault persists).

**Half-open behaviour (exact, and the WHY):** Microsoft — *"The Half-Open state helps prevent a recovering
service from suddenly being flooded with requests... a flood of work can cause the service to time out or
fail again."* So only a *limited number* of trial calls are admitted.

**Circuit Breaker vs Retry (exact):** Microsoft — *"The Retry pattern enables an application to retry an
operation with the expectation that it eventually succeeds. The Circuit Breaker pattern prevents an
application from performing an operation that's likely to fail."* They compose: retry **through** a breaker,
but *"the retry logic should be sensitive to any exceptions that the circuit breaker returns and stop retry
attempts if the circuit breaker indicates that a fault isn't transient."*

### 2.3 Retry with exponential backoff and jitter — formulae reproduced EXACTLY

Source: Marc Brooker, AWS Architecture Blog (2015). The post compares four strategies; AutoFirm should use
**Full Jitter** (the prompt-specified target). All `random_between(a, b)` are uniform over `[a, b]`.
`base` = initial backoff interval; `cap` = max backoff; `attempt` = 0-indexed retry count;
`sleep` (in Decorrelated) carries the previous iteration's value.

```
# Plain capped exponential backoff (no jitter)
sleep = min(cap, base * 2 ** attempt)

# Full Jitter   <-- AutoFirm target
sleep = random_between(0, min(cap, base * 2 ** attempt))

# Equal Jitter
temp  = min(cap, base * 2 ** attempt)
sleep = temp / 2 + random_between(0, temp / 2)

# Decorrelated Jitter
sleep = min(cap, random_between(base, sleep * 3))
```

Brooker's experiments show that **jitter dramatically reduces contention/total work** versus naive
exponential backoff (which synchronises clients into retry storms); **Full Jitter** and **Decorrelated
Jitter** perform best on completion time and server load. Key takeaway (faithful): *backoff alone is not
enough — without jitter, capped exponential backoff still clusters retries; spreading retries randomly is
what cuts the load.*

> NOTE (could-not-fully-verify): the AWS post presents the formulae primarily as figures/graphs; the four
> expressions above are the algorithmic forms as stated in the post and as universally reproduced. The
> **Full Jitter** form `random_between(0, min(cap, base*2**attempt))` is verbatim from the source and is the
> one the prompt requires — treat it as authoritative. Always add a **max-attempts / max-elapsed cap** so
> retries terminate; pair with the circuit breaker so retries stop once the breaker reports a non-transient
> fault.

### 2.4 Bulkhead — reproduced faithfully

Microsoft — *"Isolate the elements of an application into pools so that if one element fails, the others
continue to function... makes an application tolerant of failure and stops a fault in one part of the system
from cascading across the rest."* Named after a ship's watertight compartments.

**Mechanism:** partition resources so a fault in one dependency cannot exhaust the resources needed for
others. Canonical form: *"a consumer that calls multiple services might be assigned a connection pool for
each service. If a service begins to fail, it only affects the connection pool assigned for that service.
The consumer can continue to use other services."* Also supports per-instance isolation (one client →
one service instance) and async isolation via separate queues.

**Benefits (verbatim list):** isolates consumers/services from cascading failures; preserves partial
functionality on a single failure; enables differentiated quality-of-service (priority pools).
**Implementation primitives:** processes, thread pools, semaphores, separate containers/VMs, separate queues
(cited frameworks: **resilience4j**, **Polly**). Microsoft explicitly flags: *"AI and inference workloads
often require strict bulkheads because of deployment-level quotas and concurrency limits, for example,
isolating Azure OpenAI deployments per workload or per tenant."* — directly relevant to AutoFirm.
Microsoft recommends **combining bulkheads with retry, circuit breaker, and throttling**.

---

## 3. Best parts to take → AutoFirm (W1 selection + W5 cost-exactness)

- **W1 deterministic core wraps every upstream provider/model endpoint in a per-endpoint circuit breaker.**
  State machine exactly as §2.2: Closed → Open on failure-threshold-within-interval; Open → Half-Open on
  reset-timeout; Half-Open → Closed on N consecutive successes (reset counter) / → Open on any failure
  (restart timer). This is a **deterministic, regulator-defensible** policy — thresholds/timeouts are
  config, not learned (the learned router may *re-rank* healthy endpoints, but must never override an OPEN
  breaker → fail-closed). Per-endpoint breakers satisfy Microsoft's "resource differentiation" caveat: one
  provider tripping must not block a healthy alternate.
- **Retry only with Full Jitter + cap + max-attempts**, and **only through** the breaker — stop retrying the
  instant the breaker reports a non-transient fault. Use `sleep = random_between(0, min(cap, base*2**attempt))`.
  This prevents retry storms against a recovering provider (Brooker) and avoids double-counting cost on
  retried-but-billed calls (W5: attribute cost per *actual upstream attempt*, see gateway folders).
- **Bulkhead the egress pool per provider (and per tenant).** Separate connection/concurrency pools per
  upstream so one provider's outage or quota-exhaustion cannot starve the others — exactly Microsoft's
  AI-inference guidance. Pair with the breaker + jittered retry as a three-layer stack (bulkhead isolates,
  breaker fast-fails, jittered retry recovers transient blips).
- **Map to gateway features:** LiteLLM's `cooldown_time` + `allowed_fails` *is* a circuit-breaker cooldown;
  OpenRouter's `provider.order` + `allow_fallbacks` is provider-level failover. The AutoFirm deterministic
  layer should treat these as the *outer* breaker and add its *own* breaker so behaviour is gateway-agnostic
  and exactly testable (determinism tests over repeated runs).
- **Effectiveness evidence (W5/evidence showcase):** the breaker state machine and the jitter formula are
  both exactly testable — property/determinism tests on transitions and boundary tests on the threshold
  (5th failure trips, 4th does not) feed the `evidence/` showcase with zero numerical error.
