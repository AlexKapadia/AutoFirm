# SUMMARY — Six Sigma & DMAIC

## Full citation
- **Origin (primary corporate):** Motorola, Inc. — Six Sigma quality program; term coined by
  **Bill Smith** (Motorola engineer) in **1986/1987**. Target: **3.4 defects per million
  opportunities (DPMO)**.
- **Foundational practitioner book:** Harry, M. & Schroeder, R. (2000). *Six Sigma: The Breakthrough
  Management Strategy.* Currency/Doubleday. ISBN 0-385-49437-8.
- **Peer-reviewed/independent reference:** *Six Sigma Method* — StatPearls (NIH/NCBI Bookshelf) —
  https://www.ncbi.nlm.nih.gov/books/NBK589666/ ; Lean Enterprise Institute "Six Sigma" —
  https://www.lean.org/lexicon-terms/six-sigma/ ; ASQ, "The Confusion Over Six-Sigma Quality" —
  https://asq.org/quality-progress/articles/the-confusion-over-six-sigma-quality

## Ontology questions informed
- **L1.B11.1** (primary, quality/process control). Feeds **L2.B11**, **L2.B14** (delivery quality).

## GRADE tier
- **High** for the DMAIC structure and the DPMO definition: corroborated independently by NIH
  StatPearls (peer-reviewed reference), LEI, and ASQ (the quality standards body).
- **Down-rate:** the famous "$16B+ savings at Motorola" figure is a company self-report (Moderate/Low,
  not independently audited here) → treated as supporting color, NOT a relied-upon claim.
- **Caveat (ASQ):** the "1.5-sigma shift" assumption underlying the 6σ→3.4-DPMO mapping is debated;
  recorded as a known nuance, not asserted as exact universal truth.

## Key claims (faithful)

### The Six Sigma target (exact)
A "Six Sigma" process produces **3.4 defects per million opportunities (DPMO)** — i.e., process
output is statistically expected to be within specification ~99.99966% of the time. This figure
incorporates a conventional **1.5σ long-term process shift** (Motorola convention): a process
centered at ±6σ from the spec limit short-term yields 3.4 DPMO long-term after the 1.5σ shift. (Without
the shift, ±6σ ≈ 0.002 DPMO — ASQ notes this discrepancy.)

### DMAIC — the five-phase improvement cycle (for existing processes)
1. **Define** — the problem, customer (CTQ — critical-to-quality) requirements, project scope/goals.
2. **Measure** — collect data; establish the baseline process capability (e.g., DPMO, sigma level).
3. **Analyze** — identify root cause(s) of variation/defects (data-driven).
4. **Improve** — implement and verify solutions that address root cause.
5. **Control** — sustain the gain (control charts, SPC, standard work) so the process doesn't regress.

> Related variant: **DMADV / DFSS** (Define-Measure-Analyze-Design-Verify) for *new* process/product design.

### Core idea
Reduce **variation** (not just the mean) so output reliably meets customer specification; defects are
defined relative to customer CTQ requirements; decisions are data-driven and statistically grounded.

## Reproducibility note
DMAIC phases and the 3.4-DPMO definition are confirmed in NIH StatPearls (NBK589666) and the LEI
lexicon; the 1.5σ-shift nuance in ASQ. All cited above.
