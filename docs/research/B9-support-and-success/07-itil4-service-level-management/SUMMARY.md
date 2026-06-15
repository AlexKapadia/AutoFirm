# SUMMARY — ITIL Service Level Management (SLA / OLA / Underpinning Contract; support tiers & escalation)

## Full citation
- **Primary standard:** AXELOS / PeopleCert, *ITIL® 4: Service Level Management practice guide* (ITIL 4 Foundation, 2019; SLM practice). AXELOS Ltd.
- **Predecessor:** *ITIL v3 Service Design* (2011), Service Level Management process.
- **Corroborating professional references (verification of definitions):**
  - IT Process Maps, *Service Level Management (ITIL)*, https://wiki.en.it-processmaps.com/index.php/Service_Level_Management
  - Matrix42 Service Desk Guide, *SLA / OLA / UC*, https://docs.matrix42.com/service-desk-basics/3383708_service-level-agreement-sla-operation-level-agreement-ola-underpinning-contract-uc

## Ontology question informed
- **L1.B9.1** — the support-tier / SLA / escalation operating model (the structural foundation of support ops).

## What the source claims (faithful)
- **Service Level Management (SLM)** "aims to negotiate Service Level Agreements with the customers and to design services in accordance with the agreed service level targets," and is "responsible for ensuring that all Operational Level Agreements and Underpinning Contracts are appropriate, and to monitor and report on service levels" (IT Process Maps, ITIL).
- **Three agreement types (exact distinctions):**
  - **SLA** — "An agreement between an IT service provider and a **customer**. The SLA describes the IT service, documents service level targets, and specifies the responsibilities of the IT service provider and the customer." (external/customer-facing)
  - **OLA (Operational Level Agreement)** — "An agreement between an IT service provider and **another part of the same organization**. An OLA supports the IT service provider's delivery of services to customers." (internal, supports the SLA)
  - **Underpinning Contract (UC)** — a contract with an **external third-party supplier** that underpins the SLA.
- **SLA targets** typically include **response time (reaction time)** and **resolution time (solution time)**, plus **availability**, **escalation procedures**, and **service hours**. In service-desk tooling, response + resolution times and the service-time profile are mandatory for computing **escalation points**.
- **Support tiers & escalation:** the Service Desk is the single point of contact (Tier 1); unresolved tickets escalate to specialist tiers (Tier 2/3) via:
  - **Functional escalation** — passing to a team with more expertise/privilege (horizontal, by skill).
  - **Hierarchical escalation** — informing/involving higher management (vertical, by authority), typically triggered by SLA-breach risk.

## Source-quality grade (GRADE-adapted)
- **Tier: Moderate–High.** ITIL is the de-facto **professional standard** for IT service management; definitions are stable and globally adopted. The official AXELOS publication is the primary; the wiki/vendor pages are corroborating pointers, not the citation of record.
- **Down-rate (minor):** ITIL is a best-practice framework, not an empirically-validated theory; it is prescriptive rather than tested. For *definitional* and *operating-model* content this is acceptable (it is the standard everyone implements).

## Reproducibility note
SLA/OLA/UC definitions and functional-vs-hierarchical escalation are reproducible verbatim from the ITIL glossary and the two corroborating professional references; the response/resolution-time + service-hours structure of an SLA is standard across all ITSM tooling.
