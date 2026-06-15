# SUMMARY — Elnozahy et al. "A Survey of Rollback-Recovery Protocols in Message-Passing Systems"

## Full citation
- **Title:** A Survey of Rollback-Recovery Protocols in Message-Passing Systems
- **Authors:** E. N. (Mootaz) Elnozahy, Lorenzo Alvisi, Yi-Min Wang, David B. Johnson
- **Year:** 2002
- **Venue:** ACM Computing Surveys, Vol. 34, No. 3, pp. 375–408
- **DOI:** 10.1145/568522.568525
- **URL:** https://dl.acm.org/doi/10.1145/568522.568525 ; https://www.cs.utexas.edu/~lorenzo/papers/SurveyFinal.pdf

## Ontology questions informed
- **L1.A3.3** Checkpoint / handoff / resume mechanisms & state externalization (PRIMARY — the canonical taxonomy of checkpoint/recovery).
- Feeds **L2.A3** (resume protocol design) and **L1.A5.2** (resumability/idempotency of CLI sessions).

## GRADE tier
- **High.** Peer-reviewed ACM Computing Surveys (a top survey venue), foundational and canonical for checkpoint/recovery theory. No material down-rate. (The formal definitions below are the survey's well-established, widely-reproduced taxonomy; primary-text page locators to be back-filled when the PDF is read verbatim — see reproducibility note.)

## Key concepts (the checkpoint/recovery taxonomy)
- **Two families:** **checkpoint-based** recovery (relies solely on checkpointing to restore system state) vs. **log-based** recovery (checkpointing + logging of nondeterministic events).
- **Checkpoint-based sub-types:**
  - **Coordinated checkpointing** — processes coordinate to save a consistent global state; simple recovery, no domino effect, but synchronization overhead.
  - **Uncoordinated checkpointing** — processes checkpoint independently; risks the **domino effect** (cascading rollbacks) and useless checkpoints.
  - **Communication-induced checkpointing** — piggybacks protocol info on messages to force checkpoints that prevent the domino effect, without full coordination.
- **Log-based recovery** relies on the **piecewise-deterministic (PWD) assumption**: execution is deterministic between nondeterministic events; by logging and replaying those events "in their exact original order," a process can "deterministically recreate its pre-failure state even if not checkpointed."
- **Domino effect:** uncoordinated rollbacks can cascade backward through dependent processes, potentially undoing all progress.
- **Consistent global state / recovery line:** a saved global state with no orphan messages (received but, after rollback, never sent) — the safe state the system rolls back to.

## Reproducibility note
The PDF (cs.utexas.edu mirror) is the authoritative text; the WebFetch text-extractor could not decode the compressed streams, so the definitions above are reproduced from two independent search-engine extractions of this exact survey plus its widely-reproduced canonical taxonomy. **OPEN ITEM:** before treating any specific page-locator quote as load-bearing, read the PDF verbatim and attach section/page numbers. The taxonomy structure (coordinated/uncoordinated/comm-induced; checkpoint vs log; PWD; domino) is the relied-upon, uncontested content.
