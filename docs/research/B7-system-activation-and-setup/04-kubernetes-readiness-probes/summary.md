# Readiness / Liveness / Startup Probes — Kubernetes

## Citation (exact)
- Kubernetes Documentation, "Liveness, Readiness and Startup Probes".
  https://kubernetes.io/docs/concepts/workloads/pods/probes/

## Faithful summary
Kubernetes distinguishes three probe types that the kubelet runs against a container; the key insight for
B7 is that "started" and "ready" are different states:

- Readiness probe — "Indicates whether the application running in the container is ready to accept
  requests." If ready, Services matching the pod send traffic to it; if not, the endpoints controller
  removes the pod from all matching Services. Readiness probes are useful "when waiting for an application
  to perform time-consuming initial tasks, such as establishing network connections, loading files, and
  warming caches", and also later in the lifecycle "when recovering from temporary faults or overloads".
- Liveness probe — indicates if the container is operating; if it fails, the kubelet kills and restarts the
  container. (Detects deadlock/hang in an otherwise-running process.)
- Startup probe — indicates whether the application has started; other probes do not begin functioning
  until the startup probe succeeds. Protects slow-starting apps from being killed by an eager liveness probe.

Core principle: a component being constructed/launched is NOT proof it can serve. A separate readiness check
must actively confirm end-to-end serving capability (connections open, caches warm, dependencies reachable)
before the system is declared live. Probes are level-triggered observations, re-run continuously, so a
component that becomes unhealthy is automatically taken out of rotation and a recovered one is put back.

## Best parts to take -> AutoFirm
- Post-activation self-test = a readiness probe set. After build_platform + supervisor start, run a
  readiness suite that proves each wired capability can actually serve, not merely that it was constructed:
  - model gateway: a cheap probe call succeeds (or capability correctly reports degraded if no key) —
    "ready to accept requests".
  - cost ledger: a write+read round-trip and append-only invariant holds.
  - comms bus: deliver a synthetic loopback envelope and assert it routes + audits.
  - capability registry: enumerates the live capabilities and their breaker states.
  - memory layer: store+recall a synthetic record.
  - org engine / front door: a synthetic human request routes to a role.
  - audit sink: append + tamper-evident verify of one record.
  This is exactly the "smoke test that proves the system is actually working end-to-end" the mandate asks for.
- Distinguish started vs ready (startup vs readiness). autofirm up must WAIT (startup-probe style) for slow
  initialisations (embedding backend warm-up, DB migration) before running readiness — never report green
  on a half-warmed system.
- Liveness/restart maps to the supervisor (folder 03). status re-runs the readiness probes on demand
  (level-triggered), so a capability that fell over since boot shows as degraded, and one that recovered
  shows as ready — self-healing visibility without a restart.
- Exit-code contract. up exits 0 only if no REQUIRED/SECURITY readiness probe failed (DEGRADED optional
  capabilities are allowed and reported) — consistent with B3 doctor exit-code contract.

## Cross-link (no duplication)
B3 doctor checks desired-state membership of the ENVIRONMENT (is the venv present? is gitleaks on PATH?).
B7-04 readiness checks the RUNNING SYSTEM end-to-end (does a gateway call actually return? does an envelope
actually route?). Static config check vs live serving check — complementary, not duplicate. B7 readiness
reuses B3 criticality (REQUIRED/SECURITY/OPTIONAL) to decide which probe failures block green.
