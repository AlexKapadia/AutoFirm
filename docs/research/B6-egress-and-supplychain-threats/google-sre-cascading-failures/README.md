# Addressing Cascading Failures — Google SRE Book, Ch. 22

## 1. Full citation

- **Title:** *Site Reliability Engineering: How Google Runs Production Systems* — Chapter 22, "Addressing Cascading Failures"
- **Authors / Org:** Mike Dahlin, Vivek Rau, Betsy Beyer (Ed.); Google LLC. Published by O'Reilly Media.
- **Year:** 2016
- **URL:** https://sre.google/sre-book/addressing-cascading-failures/

Related chapter for overload mechanics:
- "Handling Overload" — https://sre.google/sre-book/handling-overload/

## 2. Faithful structured summary

**Definition (load-bearing, exact):** A cascading failure is *"a failure that grows over time as a result of positive feedback."* The mechanism: *"a portion of an overall system fails, increasing the probability that other portions of the system fail."* A single replica fails under load → its load redistributes to surviving replicas → they too cross their capacity → the failure propagates until the whole service is down (a "crash-loop").

**Most common cause — overload.** When one cluster/replica fails, traffic redirects to the remaining infrastructure beyond its capacity, causing progressive deterioration in success rate.

**Resource-exhaustion failure modes the chapter enumerates:**
- **CPU:** increased latency, growth in in-flight requests, queue buildup, thread starvation.
- **Memory:** task eviction, GC death-spirals, reduced cache hit rate.
- **Threads / file descriptors:** health-check failures, connection-setup failures.

**Mitigations (the canonical set):**
- **Load shedding & graceful degradation:** return HTTP `503` when overloaded; serve *reduced-quality* results (fewer images, cheaper algorithm) rather than failing wholesale — preserve stability over completeness.
- **Retry management:** *"Always use randomized exponential backoff when scheduling retries."* Enforce **per-request retry limits** and a **service-wide retry budget** (e.g. 60 retries/min) to prevent retry amplification stacking across layers.
- **Deadline / timeout propagation:** set an absolute deadline high in the stack and propagate a *reduced* deadline downward; each stage should *"check the deadline left at each stage before attempting to perform any more work."*
- **Circuit breaking / early rejection:** servers should *"fail early and cheaply"* rather than burn resources on requests already past their client deadline.
- **Testing:** *"Load test components until they break"* to find the breaking point; test cold-cache scenarios; verify noncritical backend failures do **not** cascade upstream.

**Emergency recovery tactics:** add capacity incrementally; temporarily disable health checks if they worsen the crash-loop; drop traffic aggressively (down to ~1% throughput) to let caches warm and the system stabilize; eliminate batch loads; then ramp traffic back gradually after fixing root cause.

## 3. Best parts to take → AutoFirm controls

- **Grounds the egress-GATEWAY-as-SPOF threat row.** The gateway is AutoFirm's *single chokepoint*: by definition a positive-feedback overload there cascades platform-wide for an unattended run. This chapter is the authoritative basis for treating it as a cascading-failure risk, not just an availability one.
- **Degraded-mode mitigation = "graceful degradation."** The chapter's *"serve reduced-quality results rather than fail wholesale"* directly grounds AutoFirm's design: if the gateway is overloaded/down, the platform should **fail the affected capability closed and degrade**, never hard-block the whole run. CLI agents (Anthropic-only) degrade to direct-to-Anthropic with a loud audited downgrade; programmatic any-model traffic fails *that* capability closed.
- **Circuit breakers + throttling at the gateway** map 1:1 to the gateway's stated PEP duties (throttling, circuit breakers). *"Fail early and cheaply"* justifies the circuit-breaker tripping before the gateway's own resources exhaust.
- **Retry budgets + backoff-with-jitter** must be enforced *inside* the gateway and in every agent client, or AutoFirm's many parallel CLI sessions become a self-inflicted retry-storm DoS against their own chokepoint.
- **Deadline propagation** grounds per-session short-TTL request deadlines so a stalled upstream cannot pin gateway threads indefinitely.
- **"Load test until it breaks"** is a direct mandate for the evidence/ showcase: prove the gateway's breaking point and the degraded-mode handoff with adversarial load tests, not assertion.
