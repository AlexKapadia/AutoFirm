# BEST-PARTS — ISO/IEC 42001 for AutoFirm

## ADOPT
1. **Adopt A.6.2.8 event-logging scope as AutoFirm's audit-event category list:** security/access events (authn attempts, permission changes, intrusion signals) AND data-handling movements (input, output, export, redaction, **deletion**). This is more specific than EU AI Act Art. 12 and gives a concrete checklist for *what* the audit log captures — every credential use, every tool call, every data egress, every deletion (CLAUDE.md §5.6 "every sensitive action and external call").
2. **Adopt pre-defined retention AND deletion policy as a hard requirement.** Records control mandates that retention/deletion be defined up-front and enforced by tooling, not convention. This gives AutoFirm deletion-with-verification (ties to L1.A4.4 memory deletion-verify and FHIR `entity.role=removal`, source 02) — and a deletion is itself a logged, tamper-evident event.
3. **Adopt the documented-information set (clause 7.5) as AutoFirm's governance artifact inventory:** policy, scope, risk assessment + Statement of Applicability, impact assessments, operational logs, internal audit reports, model cards, decision records. Maps onto docs/ + evidence/ (CLAUDE.md §3.10) so AutoFirm is *audit-ready / certifiable* by construction.
4. **Adopt "traceable audit trails + accountability over lifecycle" as the binding tie between A6's audit log and the agent org** — every decision record traces to the responsible agent/principal (PROV actedOnBehalfOf, source 01; RMF GOVERN accountability, source 11).

## REJECT / DEFER
- **Reject pursuing formal certification now.** AutoFirm adopts the *controls* (which improve the build) without the certification overhead; revisit certification when a client requires it (L2.B10).
- **Defer the full PDCA management-system wrapper**; A6 takes the technical logging/records controls, not the whole AIMS bureaucracy at this stage.

## Why (cited)
ISO/IEC 42001 supplies the most concrete *records/logging control list* of the three compliance anchors — turning "log sensitive actions" into a specific, certifiable set of event categories and a mandatory retention/deletion discipline, making AutoFirm's A6 layer institution-grade and auditable (CLAUDE.md §3.2).
