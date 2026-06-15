# SUMMARY — HL7 FHIR Provenance & AuditEvent Resources (R4)

## Full citation
- **Title:** FHIR Provenance Resource & AuditEvent Resource (HL7 FHIR Release 4, v4.0.1)
- **Author/Org:** Health Level Seven International (HL7), managed collaboratively with DICOM and IHE.
- **Year:** 2019 (FHIR R4 normative/STU release; resources maintained ongoing).
- **Venue/Publisher:** HL7 International.
- **URL:** https://hl7.org/fhir/R4/provenance.html and https://hl7.org/fhir/R4/auditevent.html

## Question(s) informed
- **L1.A6.1** Provenance models (FHIR-Provenance/AuditEvent-style "what/when/who").
- **L1.A6.2** Immutable audit logs (AuditEvent's no-update/no-delete stance).

## GRADE tier
**High.** Official HL7 standard, deployed at national scale in regulated healthcare; explicitly grounded in IHE ATNA and mapped to W3C PROV (source 01) — independent corroboration of the provenance vocabulary.

## Key content — Provenance resource
Documents "entities and processes involved in producing, delivering, or influencing a resource. It establishes foundations for assessing authenticity, enabling trust, and ensuring reproducibility." Key elements:
- **target** (1..*): resources created/updated by the activity.
- **occurred[x]** (0..1): the period/dateTime the activity took place.
- **recorded** (1..1, REQUIRED): "The instant when the activity was recorded."
- **policy** (0..*): policy/plan defining the activity.
- **agent** (1..*): actors taking responsibility — sub-fields `type`, `role`, `who` (1..1 REQUIRED), `onBehalfOf` (0..1).
- **entity** (0..*): resources used — `role` (derivation, revision, quotation, source, removal), `what` (1..1 REQUIRED).
- **signature** (0..*): digital signatures on target references.

## Key content — AuditEvent resource
"The primary purpose of this resource is the maintenance of security audit log information." Critically (verbatim): *"Servers that provide support for AuditEvent resources would not generally accept update or delete operations on the resources, as this would compromise the integrity of the audit record."*

## Provenance vs. AuditEvent (the design split)
- **Provenance** = record-keeping *assertion* prepared by the application that initiates create/update — "covers 'Generation' of 'Entity'" in W3C PROV terms.
- **AuditEvent** = created *as events occur* to track/audit them — "covers 'Usage' of 'Entity' and all other 'Activity'." They overlap but serve different roles: Provenance is the durable lineage claim; AuditEvent is the operational security log.

## W3C PROV mapping (quoted)
"In terms of W3C Provenance the FHIR Provenance resource covers 'Generation' of 'Entity' with respect to FHIR defined resources for creation or updating."

## Reproducibility note
Element cardinalities and the no-update/no-delete quote are from the R4 resource pages above (Provenance §Content, AuditEvent §Scope and Usage).
