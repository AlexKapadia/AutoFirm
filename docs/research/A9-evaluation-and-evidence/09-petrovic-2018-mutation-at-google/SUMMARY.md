# SUMMARY — State of Mutation Testing at Google

## Full citation
- **Title:** State of Mutation Testing at Google
- **Authors:** Goran Petrovic, Marko Ivankovic
- **Year:** 2018
- **Venue:** Proceedings of the 40th International Conference on Software Engineering: Software
  Engineering in Practice (ICSE-SEIP '18), Gothenburg, Sweden
- **DOI/URL:** 10.1145/3183519.3183521 | https://research.google/pubs/state-of-mutation-testing-at-google/

## Questions informed
- **L1.A9.3** Mutation testing -- INDUSTRIAL-SCALE practice (PRIMARY, practitioner-primary data).

## GRADE tier: Moderate-High
Peer-reviewed ICSE-SEIP (practice track) with primary industrial measurements from Google. Primary
quantitative data from a real deployment (up-rate); practice-track + single-organization (mild
down-rate for generalizability). Net: Moderate-High. The scale numbers are primary measurements.

## Key claims (exact numbers, with context)

### Scale of deployment
- Google's monolithic repository contains "approximately 2 billion lines of code."
- The approach was empirically validated by "evaluating more than 70,000 diffs, testing 1.1
  million mutants and surfacing 150,000 actionable findings during code review."

### The core technique: make mutation feasible at scale
- "diff-based" mutation: create mutants only on lines in a code-review diff (not the whole repo).
- "arid lines" suppression: omit "lines of code without statement coverage" and lines "determined
  to be uninteresting" (arid). "A diff-based approach greatly reduces the number of lines in which
  mutants are created, and the suppression of arid lines cuts the number of potential mutants
  further; combined, these two approaches make mutation analysis feasible even for colossal complex
  systems."

### Productive vs. unproductive mutants
- "Not all mutants are perceived by developers as being useful/productive" -- many mutants are not
  worth writing a test for. Developers can flag a surviving ("living") mutant as unproductive
  "with a single click," and this feedback is tracked as a quality metric. The system optimizes for
  *productive* mutants surfaced at code-review time.

### The motivating finding (coverage insufficiency)
- "Code coverage is used at Google as a measure of test suite effectiveness, but coverage alone
  might be misleading, as in many cases where statements are covered but their consequences are not
  asserted upon." -- mutation catches the covered-but-unasserted gap.

## Reproducibility note
Scale numbers (2B LOC; 70,000 diffs; 1.1M mutants; 150,000 findings) and the arid-line / diff-based
/ productive-mutant concepts extracted from the official Google Research listing and the ICSE-SEIP
'18 record. The "covered but consequences not asserted upon" statement is the load-bearing
qualitative claim corroborating CLAUDE.md §3.6 and source 02. Numbers quoted verbatim.
