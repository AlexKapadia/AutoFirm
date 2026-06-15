# SYNTHESIS — A6 Governance, Auditability & Provenance

Branch A6 answers three L1 questions (QUESTION-ONTOLOGY.md): L1.A6.1 provenance models,
L1.A6.2 immutable append-only audit logs & tamper-evidence, L1.A6.3 governance-aware
telemetry & closed-loop enforcement. This synthesis surveys the full option space per question,
gives an ADOPT/REJECT verdict each, and states the concrete, cited recommendation for AutoFirm.
It is literature-only (Layer 1): it frames what L2.A6 should DO, it does not build it.

---

## L1.A6.1 — Provenance model: full space surveyed

| Option | Verdict | Why (cited) |
|---|---|---|
| W3C PROV-DM (Entity/Activity/Agent + 7 relations) | ADOPT (model) | Standard, interoperable; maps what/when/who + delegation actedOnBehalfOf onto the agent org (src 01). |
| FHIR Provenance + AuditEvent split | ADOPT (pattern) | Regulated-domain-proven 2-record split: durable lineage vs. operational security log; no-update/no-delete invariant (src 02). |
| PROV-N / PROV-O RDF serialisation | REJECT | Heavy ontology tooling unneeded at the substrate; adopt the model, persist as typed JSON (src 01). |
| Ad-hoc / bespoke event schema | REJECT | Not interoperable, not auditor-recognised; fails institution-grade bar (CLAUDE.md 3.2). |

Recommendation: the audit-event contract uses the PROV triple (Entity / Activity / Agent) with
wasGeneratedBy, used, wasAssociatedWith, actedOnBehalfOf, wasDerivedFrom, and emits TWO records per
sensitive action (FHIR-style): a Provenance lineage assertion (why an artifact exists, CLAUDE.md
3.11) and an AuditEvent security-log entry (append-only). Required non-null fields: recorded (when),
agent.who + onBehalfOf (who / on-whose-behalf).

---

## L1.A6.2 — Tamper-evident append-only log: full space surveyed

| Option | Verdict | Why (cited) |
|---|---|---|
| Plain forward hash chain (Schneier-Kelsey / Haber-Stornetta linking) | ADOPT as baseline only | Founding primitive; detects mid-log edits (src 03). BUT O(n) proofs and silently truncatable (src 05). |
| History tree (Crosby-Wallach) | ADOPT (data structure) | O(log n) inclusion + consistency proofs at production throughput; untrusted-logger/auditor trust model (src 04). |
| CT-style Merkle log + Signed Tree Heads (RFC 6962) | ADOPT (reference design) | Internet-scale-proven append-only log; STH gossip detects equivocation; exact SHA-256 MTH recurrence as test oracle (src 06). |
| FssAgg forward-secure aggregate sig (Ma-Tsudik) | ADOPT insight / DEFER mechanism | Names truncation + delayed-detection attacks; forward-security adopted; aggregate-sig as primary rejected (src 05). |
| Blockchain / DLT ledger | REJECT | Consensus overhead unjustified for a single-operator log; external anchoring of an STH is far cheaper (src 03/06). |
| Write-once / convention-only append-only | REJECT | Not cryptographically tamper-evident; fails fail-closed bar (CLAUDE.md 5.6). |

Recommendation: audit log = append-only events sealed in a history-tree / CT-style Merkle log
(src 04/06), publishing a Signed Tree Head commitment at every gate (CLAUDE.md 3.13) to an external
anchor (distributed-trust insight, src 03). Threat model MUST name truncation and delayed-detection
(src 05) and defend via consistency proofs + forward-secure signing keys. Implementation MUST use
RFC 6962 leaf/node domain-separation prefixes (0x00 / 0x01) — a zero-error, mutation-tested detail
(CLAUDE.md 3.6 / 3.11). Data layer refuses UPDATE/DELETE on audit records (FHIR invariant, src 02).

---

## L1.A6.3 — Governance telemetry & closed-loop enforcement: full space surveyed

| Option | Verdict | Why (cited) |
|---|---|---|
| GAAT (governance schema over OpenTelemetry + OPA rules + graduated Enforcement Bus + trusted telemetry) | ADOPT (architecture) | Closes the observe-but-do-not-act gap; telemetry drives real-time enforcement; signs the telemetry (src 07). |
| MI9 runtime governance (agency-risk index, drift detection, graduated containment, continuous authz, FSM conformance) | ADOPT (enforcement vocabulary) | Drift detection = automated North Star; risk-proportional containment; runtime least-privilege (src 08). |
| Verifiability-first + lightweight audit agents (Gupta, OPERA) | ADOPT (principle + test rig) | Detect-over-prevent axiom; separate read-only audit agent; challenge-response attestation; OPERA = governance tests-with-teeth (src 09). |
| Observe-only dashboards (OpenTelemetry/Langfuse alone) | REJECT as sufficient | The observe-but-do-not-act gap: violations caught only after damage (src 07). Use OTel as substrate, not the whole answer. |
| Static / train-time alignment only | REJECT as sufficient | Misses deployment-time risk; runtime governance required (src 08). |
| NIST AI RMF (GOVERN/MAP/MEASURE/MANAGE) | ADOPT (organising frame) | Government-standard closed loop: MEASURE must feed MANAGE; accountability under GOVERN (src 11). |
| ISO/IEC 42001 records/logging controls (A.6.2.8, clause 7.5) | ADOPT (control list + retention) | Concrete event-category checklist + mandatory retention/deletion; certifiable (src 12). |
| EU AI Act Art. 12 | ADOPT (binding floor) | Legal requirement: automatic lifetime logging; event taxonomy (a/b/c); >=6-month retention (src 10). |

Recommendation: wire telemetry -> policy engine -> enforcement as a closed loop (GAAT, src 07) on
an OpenTelemetry substrate extended with a governance schema carrying the PROV/FHIR fields; policies
are declarative OPA-style data (testable, versioned). Enforcement is graduated containment (MI9, src
08): warn -> throttle/reduce-capability -> isolate -> global kill-switch (CLAUDE.md 5.6). A separate
read-only audit agent (verifiability-first, src 09 = CLAUDE.md 2 North Star) consumes the
tamper-evident log + telemetry, runs goal-conditioned drift detection (automating the ~30-min North
Star heartbeat, CLAUDE.md 4.7), and gates high-risk actions via challenge-response attestation. The
stack is organised along NIST RMF GOVERN/MAP/MEASURE/MANAGE (src 11), captures the ISO 42001 A.6.2.8
event categories with a defined retention/deletion policy (src 12), and meets the EU AI Act Art. 12
lifetime-logging floor (src 10).

---

## Cross-cutting integrated picture (for L2.A6 / L3.PLATFORM)

The three sub-questions compose into ONE fail-closed governance plane:
1. Provenance (A6.1) defines the CONTENT of every audit record (PROV triple + FHIR split).
2. Tamper-evidence (A6.2) makes that record UNFORGEABLE and append-only (history-tree/CT log, STH
   commitments at gates, external anchoring, truncation-resistant, no UPDATE/DELETE).
3. Closed-loop governance (A6.3) makes the record ACTIONABLE (telemetry -> OPA policy -> graduated
   enforcement), watched by a separate read-only audit agent, organised by NIST RMF and ISO 42001,
   and legally required by EU AI Act Art. 12.

A6/A7 veto (RESEARCH-PROGRAM 5.2): governance is fail-closed; if the audit log cannot be written or
sealed, the action is refused, not proceeded with. This veto is binding on every other branch.

## Evidence-chart targets for evidence/ (CLAUDE.md 3.10)
- Tamper-evidence: proof size O(log n) vs O(n) curve (src 04); known-answer test of RFC 6962 MTH
  recurrence (src 06).
- Governance test rig (OPERA-style, src 09): detection rate + time-to-detection of injected
  malicious/faulty agent actions (mutation-testing analogue for governance, CLAUDE.md 3.6).
- Enforcement latency distribution (target <200 ms, re-measured on AutoFirm workload, NOT GAAT
  numbers, generality 3.9).
- Compliance cross-walk: AutoFirm controls -> NIST RMF subcategories / ISO 42001 controls / EU AI
  Act Art. 12 (a/b/c).

## Source-count check (DEPTH-RUBRIC 1)
- Tamper-evidence (safety-critical): >=3 independent primaries — Haber-Stornetta (03),
  Crosby-Wallach (04), RFC 6962 (06), + Ma-Tsudik attacks (05). PASS.
- Provenance model (important): W3C PROV (01) + FHIR (02), independent. PASS.
- Closed-loop enforcement (architecture): GAAT (07) + MI9 (08) + Verifiability-first (09),
  independent; + 3 compliance anchors (10/11/12). PASS.
