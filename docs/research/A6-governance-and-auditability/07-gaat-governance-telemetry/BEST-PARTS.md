# BEST-PARTS — GAAT for AutoFirm

## ADOPT
1. **Adopt the closed-loop framing: telemetry MUST drive enforcement, not just dashboards.** This is the core L1.A6.3 lesson and aligns with CLAUDE.md §5.6 fail-closed + the §2 North Star/kill-switch. AutoFirm's audit/telemetry pipeline is wired to a *policy engine that can act* (pause, downgrade, kill), closing the "observe-but-do-not-act gap." *Build implication:* L2.A6/L2.A7 — the audit bus feeds a real-time policy evaluator with intervention authority.
2. **Adopt OpenTelemetry as the telemetry substrate, extended with a Governance Telemetry Schema.** Reuse the OTel ecosystem (spans, traces) and add governance attributes (agent role, on-behalf-of, tool risk class, tenant_id, decision rationale). This keeps AutoFirm interoperable with standard observability while making spans auditable — and the governance attributes map cleanly onto PROV/FHIR fields (sources 01/02).
3. **Adopt OPA-compatible declarative policy rules.** Policies-as-data (Rego/OPA) keep enforcement auditable, versionable, and testable (CLAUDE.md §5.7 code-org, §3.6 tests-with-teeth on policies). Declarative rules are reviewable by the North Star/compliance lens.
4. **Adopt graduated intervention (Enforcement Bus) rather than binary allow/deny.** Matches MI9's graduated containment (source 08): escalate from warn → throttle/reduce-capability → isolate → kill, proportional to detected risk. The global kill-switch (CLAUDE.md §5.6) is the top rung.
5. **Adopt the "Trusted Telemetry" idea: the telemetry/audit stream itself is cryptographically provenance-tracked** — i.e. sign the spans (ties straight to tamper-evidence sources 03/04/06). Governance data an attacker can edit is worthless.
6. **Use the sub-200 ms enforcement latency as a *target/threshold* for AutoFirm's evidence/ charts** (CLAUDE.md §3.10) — but re-measure on AutoFirm's own workload; do not cite GAAT's numbers as AutoFirm's results (generality, §3.9).

## REJECT / DEFER
- **Reject citing GAAT's VPR/latency numbers as AutoFirm evidence.** They are preprint-stage and from a different system; adopt the *architecture and metrics-to-measure*, not the values (DEPTH-RUBRIC §6 overfit guard).
- **Defer the specific 5-layer wire protocol**; AutoFirm's substrate is the Claude Code CLI + MCP, so the integration points differ (L2.A5).

## Why (cited)
GAAT is the most directly on-target source for L1.A6.3: it operationalises "governance-aware telemetry + closed-loop enforcement" with a concrete, evaluated architecture, and explicitly ties enforcement to cryptographic provenance — unifying the A6 governance, audit, and tamper-evidence threads.
