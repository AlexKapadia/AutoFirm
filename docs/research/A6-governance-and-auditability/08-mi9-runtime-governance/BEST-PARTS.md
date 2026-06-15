# BEST-PARTS — MI9 for AutoFirm

## ADOPT
1. **Adopt Agent Semantic Telemetry as the content model for audit events** — capture goals + actions + state changes, not just raw tool calls. This makes the audit trail *explanatory* (CLAUDE.md §3.11 "explain every decision") and feeds drift detection. Maps onto the PROV Activity + GAAT GTS span (sources 01/07).
2. **Adopt Goal-Conditioned Drift Detection as a first-class North Star control.** CLAUDE.md §2's North Star/CCO heartbeat is exactly "is the run still tracking the declared objective?" MI9 gives a concrete mechanism: compare agent behaviour to declared goals and flag divergence — directly implementing the ~30-min alignment review as an automated signal feeding it.
3. **Adopt graduated containment as the enforcement ladder** (corroborates GAAT's graduated GEB, source 07): warn → reduce capability → isolate → terminate. The top rung is CLAUDE.md §5.6's global kill-switch. Proportional response avoids halting a healthy long-horizon run on a minor signal (CLAUDE.md §4.8 watchdog non-invasiveness).
4. **Adopt Continuous Authorization Monitoring** — re-check least-privilege at runtime, not just at spawn (CLAUDE.md §5.6 least-privilege, fail-closed). Permissions are re-evaluated against current context (e.g. an agent that escalated scope is caught).
5. **Adopt the FSM-based conformance engine pattern for the agent-lifecycle audit** (spawn → scoped → running → retired) — ties to L2.ORG dynamic agent-org; illegal state transitions are refused and logged.
6. **Adopt the Agency-Risk Index** to set the *strength* of audit + the *tier* of HITL gating per agent: higher-risk agents (more tools, write access, external calls) get heavier logging and tighter authorization (risk-proportional governance).

## REJECT / DEFER
- **Reject any claim that runtime governance replaces tamper-evident logging.** MI9 governs behaviour; it does not by itself make the log immutable — pair it with sources 03/04/06. Adopt as the *enforcement* layer over a tamper-evident *audit* layer.
- **Defer the exact FSM/risk-index formalism** to L2 implementation; AutoFirm's states differ.

## Why (cited)
MI9 supplies the runtime-enforcement vocabulary (drift, graduated containment, continuous authz) that turns A6's passive audit trail into A7's active control — and operationalises the North Star heartbeat (CLAUDE.md §2) as automated drift detection. Independent corroboration of GAAT's closed-loop thesis.
