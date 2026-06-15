# SUMMARY — The Interdisciplinary Study of Coordination (Coordination Theory)

## Full citation
- **Title:** The Interdisciplinary Study of Coordination
- **Authors:** Thomas W. Malone (MIT, Center for Coordination Science), Kevin Crowston
  (Univ. of Michigan School of Business Administration)
- **Year:** 1994
- **Venue:** ACM Computing Surveys, Vol. 26, No. 1, pp. 87–119.
- **URL/DOI:** https://doi.org/10.1145/174666.174668 ;
  PDF: https://crowston.syr.edu/sites/default/files/acmcs94.pdf

## Questions informed
- **L1.A1.4** (coordination-cost / information-processing view of coordination) — PRIMARY, foundational.
- **L1.A1.1** (what coordination patterns manage, and how) — PRIMARY (dependency→mechanism mapping).
- L1.A2.* (communication as dependency management) — supporting cross-branch.

## GRADE tier
**High.** Foundational, heavily-cited peer-reviewed ACM Computing Surveys article; the canonical
definition of coordination theory across disciplines. Pre-LLM, so *indirect* for LLM agents
(down-rate for indirectness) but the dependency/mechanism abstraction is domain-independent and
explicitly designed to span computer science, economics, and organization theory.

## Key claims (faithful, with locators)

### Definition (load-bearing)
- "**Coordination is managing dependencies between activities.**" (§2.1)
- Therefore "further progress should be possible by characterizing different kinds of dependencies
  and identifying the coordination processes that can be used to manage them."

### Dependency taxonomy → coordination processes (Table 1, faithful)
| Dependency between activities | Example coordination processes |
|---|---|
| **Shared resources** (limited resource used by multiple tasks) | "first come/first serve," priority order, budgets, managerial decision, market-like bidding |
| **Producer/consumer** → **Prerequisite constraints** (producer must finish before consumer) | Notification, sequencing, tracking |
| **Producer/consumer** → **Transfer** | Inventory management, just-in-time |
| **Producer/consumer** → **Usability** (output usable by consumer) | Standardization, user surveys, participatory/concurrent design |
| **Simultaneity constraints** (activities at same/different times) | Scheduling, synchronization |
| **Task/subtask** (goal decomposed into subgoals) | Goal selection, goal decomposition |

### Task assignment as a shared-resource problem
- Assigning the "scarce time of actors to the tasks they will perform" is itself a shared-resource
  dependency; "all the resource allocation methods … are potentially applicable for task assignment."

### Usability via standardization
- A common way to manage usability is "**standardization, creating uniformly interchangeable outputs
  in a form that users already expect**" (the assembly-line approach) — bridges to org-theory
  standardization-of-outputs (cross-ref L1.A2.3).

### Cross-discipline grounding
- Models "consistent with a number of previous theories about human organizational design (e.g.,
  March & Simon 1958; Galbraith 1973; Williamson 1985)" — directly links to source 07 (Galbraith).

## Reproducibility note
Definition and the Table-1 dependency→mechanism mapping extracted via pdftotext (the WebFetch route
failed on the binary PDF; the local pdftotext extraction succeeded and is the source of record). The
dependency typology is the load-bearing item AutoFirm relies on for its coordination design.
