# BEST-PARTS — W3C PROV-DM for AutoFirm

## ADOPT

1. **Adopt PROV's Entity / Activity / Agent triple as AutoFirm's canonical provenance vocabulary.**
   Every audited action AutoFirm records is modelled as an **Activity** (a subagent run, a tool
   call, a commit, a deploy) that **used** input **Entities** and **wasGeneratedBy** producing
   output Entities, **wasAssociatedWith** an **Agent** (a named subagent/role), which
   **actedOnBehalfOf** the orchestrator or the human principal.
   *Build implication:* the audit-event contract (drives L2.A6) has typed fields
   `{entity, activity, agent, used[], wasGeneratedBy, wasAssociatedWith, actedOnBehalfOf}`.

2. **Adopt `actedOnBehalfOf` as the delegation primitive for the agent org.** This is exactly the
   COO→subagent delegation chain in CLAUDE.md §2/§4.1. It lets an auditor reconstruct *who
   authorised whom* — essential for "roles-as-data audit trail" (L2.A6).

3. **Adopt `wasDerivedFrom` (with revision/quotation/primary-source subtypes) for artifact lineage.**
   Maps directly to git/branch lineage and to memory-record lineage (L2.A4): an output document
   `wasDerivedFrom` its sources, so AutoFirm can answer "which inputs drove this decision"
   (CLAUDE.md §3.11 explain-every-decision).

4. **Adopt the Bundle concept for provenance-of-provenance.** AutoFirm needs to record provenance
   *about the audit log itself* (who signed it, when it was sealed). Bundles give a standard way to
   make a provenance record a first-class, attributable Entity.

## REJECT / DEFER

- **Reject mandating PROV-N / PROV-O (RDF/OWL) serialisation as the on-disk format.** PROV-DM is a
  *conceptual* model; its RDF/XML serialisations add ontology tooling overhead AutoFirm does not
  need at the substrate layer. **Adopt the model; reject the heavy serialisation** — persist as the
  typed JSON audit contract above, exportable to PROV-JSON only if an external auditor requests it.
- **Defer the Collections/Alternate components.** Not load-bearing for the audit trail; revisit only
  if AutoFirm needs set-membership provenance.

## Why (cited)
PROV-DM is the W3C Recommendation that FHIR Provenance (source 02) explicitly maps onto, so adopting
PROV gives AutoFirm a vocabulary that is already interoperable with a major regulated-domain audit
standard — institution-grade by construction (CLAUDE.md §3.2).
