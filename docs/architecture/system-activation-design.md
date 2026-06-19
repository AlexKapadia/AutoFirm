# System Activation & Flawless One-Command Setup — Design (W3 / Phase-2e)

> Status: design draft for implementation (W3 / Phase-2e). NOT yet implemented; no source code here.
> Grounded in docs/research/B7-system-activation-and-setup/ (sources 01-06) and the real package layout
> under src/autofirm/, building on docs/research/B3-resilient-bootstrap/ (idempotency / crash-resume /
> degraded-mode — reused, not re-derived). Institution-grade bar (CLAUDE.md sections 2, 3.2, 4.8).

## 0. Problem: the system is assembled but never composed
Every package under src/autofirm/ is a clean, dependency-injection-ready building block — each primary
class takes its collaborators via keyword-only constructor injection with no hidden global state (verified:
comms/inter_agent_message_bus.py, access/credential_broker.py, org/org_lifecycle_engine.py,
substrate/session_lifecycle_engine.py, heartbeat/heartbeat_scheduler.py, ...). But:
- There is NO composition root — nothing imports-and-wires the packages into one object graph.
- There is NO CLI entrypoint — pyproject.toml has no [project.scripts].
- There is NO supervisor — nothing starts or keeps alive the long-lived loops (heartbeats, comms bus, operate loop).
- There is NO post-activation self-test — nothing proves the wired system actually serves end-to-end.
- "Setup" today = make install (env only). It converges the environment (B3) but never activates the platform.

Result: the codebase FEELS FRAGMENTED — a bag of excellent parts with no single "turn it on" door. B7 fixes
exactly this without re-fragmenting (no heavy new runtime deps, no DI container).

## 1. The flawlessly-simple entrypoint
A single Typer app (source 06) exposed via pyproject.toml:

    [project.scripts]
    autofirm = "autofirm.runtime.cli_entrypoint:app"

Four self-documenting verbs (auto --help, PowerShell + bash completion):

| Command | What it does | Exit code |
| --- | --- | --- |
| autofirm up | THE one command. (1) Converge the environment via the B3 bootstrapper (check()->apply() over the step DAG: venv, deps, migrations). (2) Load PlatformConfig from env once. (3) Call the composition root factory build_platform(config) to construct + wire the whole object graph (degraded-binding per capability). (4) Hand the graph to the PlatformSupervisor, which starts the long-lived loops and keeps them up. (5) Run the post-activation self-test (readiness probes). Prints a GREEN/DEGRADED summary. | 0 if no REQUIRED/SECURITY probe FAILED (DEGRADED optional capabilities allowed); non-zero otherwise. |
| autofirm status | Re-run readiness probes on the live (or freshly-built read-only) platform; print every capability + supervised loop with its state (ready / degraded / open / down) and the reason. Level-triggered snapshot (source 04). | 0 unless a REQUIRED/SECURITY capability is down. |
| autofirm doctor | B3 read-only check() of every bootstrap step (never apply()); prints observed-vs-desired per step. The environment self-knowledge surface. | 0 if no step FAILED (DEGRADED allowed). |
| autofirm down | Cooperative cancel of every supervised loop; wait for drain (audit flush, ledger fsync). Graceful disposability (12-Factor IX). | 0 on clean drain. |

autofirm up is idempotent: a second run re-converges (no-op per B3) and re-activates to the SAME live state.
This single command is the whole "set up AND activate" requirement.

## 2. The composition root (cure for fragmentation)
ONE and only one module composes the graph (source 01 — Seemann; source 02 — factory shape):

    src/autofirm/runtime/                       (NEW package — the activation layer)
      platform_config.py                PlatformConfig: typed, loaded once from env at the CLI edge.
      platform_composition_root.py      build_platform(config) -> Platform. The ONLY module that
                                        imports + constructs every other package. Pure DI (hand-wired,
                                        no container). The only allowed cross-package new-up site.
      platform_runtime.py               Platform: the composed object graph (holds the wired services +
                                        the capability registry); no business logic.
      platform_supervisor.py            PlatformSupervisor: starts/keeps-up the long-lived loops (source 03).
      platform_readiness_selftest.py    The post-activation readiness probe set (source 04).
      cli_entrypoint.py                 Typer app: up / status / doctor / down (source 06).

(Each file is < 300 lines per CLAUDE.md 5.7; split further by responsibility if needed.)

### 2.1 Wiring graph (what build_platform constructs, in dependency order)
The root builds leaves first, then composes upward (constructor injection all the way down):

    LAYER 0  foundations (no cross-deps)
      Clock(s)                       <- injected (real wall clock at edge; deterministic in tests)
      IdGenerator
      AppendOnlyAuditSink            (audit/append_only_audit_sink, comms/append_only_audit_sink)
      KillSwitchEpoch                (modelgateway/kill_switch_epoch)     # global fail-closed switch (5.6)

    LAYER 1  access & egress (depend on L0)
      SecretSource / CredentialBroker   (access/credential_broker)            <- audit, clock
      VirtualKeyResolver                (modelgateway/cli_gateway_env_injection) <- credential broker
      HttpTransport                     (injected; degrade-aware)
      OpenAiCompatibleGatewayClient     (modelgateway/openai_compatible_gateway_client)
                                           <- transport, key resolver, kill-switch   # DEGRADES if no key
      AppendOnlyCostLedger              (costledger/append_only_cost_ledger)  <- clock, audit
           (gateway calls are metered into the cost ledger)

    LAYER 2  knowledge & registry (depend on L0/L1)
      SemanticEmbeddingBackend          (memory/semantic_embedding_backend)   # DEGRADES if backend absent
      VersionedMemoryStore -> AgentMemoryLayer (memory/agent_memory_layer)    <- embedding, clock
      LiveCapabilityRegistry            (capabilities/live_capability_registry) <- descriptors from every L1+ svc
           (the registry is the COHESION LEDGER: every capability registers here with its breaker state)

    LAYER 3  comms bus (depends on L0)
      DynamicAgentRegistry              (comms/dynamic_agent_registry)
      InterAgentMessageBus              (comms/inter_agent_message_bus)       <- registry, audit, clock,
                                           dedup, dead-letter, ordering

    LAYER 4  org + sessions (depend on L1-L3)
      DynamicOrg / OrgLifecycleEngine   (org/org_lifecycle_engine)           <- state, clock, ids
      SessionLifecycleEngine            (substrate/session_lifecycle_engine) <- launcher, credential broker,
                                           comms bus  (single-writer guard, resume saga)

    LAYER 5  front door + market intel + heartbeats (depend on L2-L4)
      FrontDoorRequestDispatcher        (frontdoor/front_door_request_dispatcher) <- role index, comms bus, audit
      DailySensingHeartbeat             (market_intel/daily_sensing_heartbeat)    <- gateway, green-light gate
      HeartbeatScheduler                (heartbeat/heartbeat_scheduler)       <- clock
           (register: north-star review beat, design beat, market-sensing beat, auto-resume watchdog 4.8)

    LAYER 6  build-&-operate loop (the platform reason to exist; depends on all)
      CompanyBuildFlow / CompanyOperateFlow (e2e/company_build_flow, company_operate_flow)
      EndToEndValidationHarness         (e2e/end_to_end_validation_harness)
           <- org engine, session engine, comms bus, memory, gateway, cost ledger, front door, finance suite

    Platform  =  assembled graph (all the above) + LiveCapabilityRegistry + the supervised loop set.

The composition root RETURNS Platform; it runs no business logic (Seemann separation). The supervisor and
CLI run it. This single wiring site is what turns the "bag of packages" into one cohesive runtime.

## 3. Graceful degradation & self-healing (reuse B3, applied at assembly)
Activation NEVER hard-blocks (mandate; CLAUDE.md 3.2 fail-closed; B3 degraded-mode spec). The factory
applies B3 degraded-mode policy PER CAPABILITY at bind time (deferred-binding, source 02):

- Missing provider key / gateway unreachable -> the model-gateway capability binds in degraded (breaker
  open), audited capability.degraded{cap=provider:X, reason=key_absent}. The platform still builds and
  comes up; every key-independent capability runs; calls to X are refused-for-X (fail-closed for that
  capability only — bulkhead). A heartbeat-driven re-probe closes the breaker when the key returns
  (self-heal). [B3 2.1 rows 1-2]
- Embedding backend / state store absent -> memory/stateful capability degrades; stateless work proceeds;
  re-probe restores. [B3 2.1]
- Analysis-only deps absent (matplotlib/graphviz) -> only the evidence/plotting capability degrades;
  runtime untouched (preserves ADR-001 5 runtime/analysis split). [B3 2.1 last row]
- SECURITY control unavailable (secret-scanner missing, audit sink unwritable) -> FAIL CLOSED for the gated
  path (refuse the dependent action), reported by status/doctor; never silently degraded to "off". Unrelated
  platform functions continue. [B3 2.1 security rows; CLAUDE.md 5.6]
- Self-heal / crash-resume. up is idempotent and forward-only (B3 contract). A crash mid-activation re-runs
  to the same converged+live state via the B3 atomic-rename ledger (05, 06). The auto-resume watchdog (4.8)
  re-invokes up, which is a no-op if already live (the watchdog never starts a second loop).
- Loop liveness. A supervised loop that crashes is restarted with backoff (B3-07 circuit breaker applied to
  process liveness); one that keeps crashing trips open and is reported, never silently dead.

Net rule: OPTIONAL -> degrade that capability + audit + re-probe (platform up). SECURITY/REQUIRED ->
converge if possible, else fail closed for that path and report. NEVER a whole-platform hard block.

## 4. Post-activation self-test (proves it actually works)
After supervisor start, platform_readiness_selftest.py runs a readiness probe per capability (source 04 —
"ready to accept traffic", not merely constructed). It proves the wired system serves END-TO-END:

| Probe | Asserts | On failure |
| --- | --- | --- |
| gateway reachability | a cheap probe call returns (or capability correctly reports degraded if no key) | OPTIONAL -> degraded |
| cost ledger round-trip | a write+read round-trips; append-only + canonical-hash invariant holds | REQUIRED -> red |
| comms loopback | a synthetic envelope routes through the bus, is deduped, and is audited | REQUIRED -> red |
| capability registry | enumerates live capabilities + breaker states; count > 0 | REQUIRED -> red |
| memory store+recall | a synthetic record stores and recalls with expected ranking | OPTIONAL -> degraded |
| org + front door | a synthetic human request routes to a role via the dispatcher | REQUIRED -> red |
| audit tamper-evident | append one record, then verify the Merkle/RFC6962 proof | SECURITY -> fail closed |
| kill-switch honored | with kill-switch engaged, a gateway call is refused | SECURITY -> fail closed |

All probes use SYNTHETIC data only (no PII, no real keys required to pass the no-secrets path). status
re-runs this set on demand (level-triggered self-knowledge).

## 5. Acceptance bar (quantified)
W3/Phase-2e activation is DONE only when ALL hold (institution-grade gate, CLAUDE.md 4.2):

1. One command, fresh clone -> live + self-tested. From a clean clone with NO secrets present, a single
   autofirm up converges the env, builds + wires the full graph, starts the supervised loops, and passes the
   readiness self-test, exiting 0 — on WINDOWS AND LINUX, same command, byte-for-byte same verb set
   (12-Factor X parity). Target: < 60 s on a warm machine for the no-network degraded path.
2. Idempotent re-run = asserted no-op + same live state. A second autofirm up performs ZERO environment
   mutations (B3 check() true for every step; mutation-counter == 0, asserted) and re-activates to the
   IDENTICAL capability/loop state set. 100% of re-runs converge; 0 spurious mutations.
3. Degraded-mode never blocks. With any single OPTIONAL dependency removed (no provider key, gateway down,
   analysis deps absent), autofirm up still reaches UP, degraded and exits 0; exactly the removed capability
   reports degraded; it auto-restores within one re-probe interval once the dependency returns. With a
   SECURITY control absent, the dependent path is refused (fail-closed) and reported, and unrelated
   capabilities stay up — verified to NEVER silently proceed and NEVER block the platform. Quantify: 0
   whole-platform hard-blocks across the full degraded-mode matrix (B3 2.1 rows).
4. Crash-resume converges. Injecting a crash at every (side-effect, ledger-write) boundary during up and
   re-running yields a final live state IDENTICAL to an uninterrupted up (B3 crash-injection harness extended
   to cover the activation steps). 100% of injection points converge.
5. Self-test catches a broken wiring. A deliberately mis-wired graph (e.g. gateway not metered into the cost
   ledger) MUST make the self-test FAIL — the suite has teeth (CLAUDE.md 3.6), not a tautology.

These are encoded as the W3 activation acceptance suite (adversarial + crash-injection + cross-OS in CI).
Coverage/mutation gates remain necessary-not-sufficient (3.6); the signal is items 1-5 holding.

## 6. What is FRAGMENTED today, and how this makes it cohesive
| Fragmentation (today) | Cohesion (this design) |
| --- | --- |
| No composition root — packages never wired together; the real dependency graph is invisible. | One platform_composition_root.build_platform() wires every package in dependency order; the graph is explicit and auditable (source 01/02). |
| No [project.scripts] / CLI — no single "turn it on" door; setup is implicit tribal knowledge. | One autofirm Typer entrypoint with up/status/doctor/down, auto --help + completion (source 06). |
| "Setup" = make install only — converges the ENV but never ACTIVATES the platform. | autofirm up = converge (B3) + compose + supervise + self-test in one command (source 03/05). |
| Long-lived loops (heartbeats, comms bus, market sensing, operate loop) have no owner that starts/keeps them up. | PlatformSupervisor declares the loop inventory once and keeps them alive with backoff/circuit-break (source 03). |
| No proof the assembled system actually serves — only unit tests of isolated parts. | Post-activation readiness self-test proves end-to-end serving across capabilities (source 04). |
| Capabilities exist but their live availability/breaker state is not surfaced anywhere. | LiveCapabilityRegistry is the cohesion ledger; status renders every capability + breaker + loop state. |
| Degradation logic (B3) exists as a spec but has no assembly site to apply it. | The factory applies B3 degraded-binding per capability at construction; degraded never blocks (source 02 + B3). |
| Env config read ad hoc; import-time side effects risk. | One typed PlatformConfig loaded at the CLI edge; import autofirm stays side-effect-free (source 02). |

## 7. Implementation notes (for the W3 builder; not built here)
- New package src/autofirm/runtime/ (activation layer). Files listed in 2; each < 300 lines (5.7).
- New runtime-edge dep: typer (pulls click) — CLI edge only, lives in runtime/cli_entrypoint.py; does NOT
  touch deterministic engine code, so the runtime/analysis split (ADR-001 5) and import-linter contract are
  unaffected. Add to [project.dependencies] with a justifying comment; keep AnyIO (ADR-001 7) for the
  supervisor event loop.
- Add [project.scripts] autofirm = "autofirm.runtime.cli_entrypoint:app".
- Reuse the B3 bootstrapper for the env-converge phase of up (do not reimplement idempotency).
- Cross-OS: the supervisor must use AnyIO cancellation (works on Windows + Linux); avoid POSIX-only signals —
  down uses cooperative cancellation, not SIGTERM-only.
- Tests live under tests/ mirroring runtime/, named test_<module>__<behaviour>.py, including the
  crash-injection + cross-OS + mis-wiring (negative) acceptance cases of 5.
