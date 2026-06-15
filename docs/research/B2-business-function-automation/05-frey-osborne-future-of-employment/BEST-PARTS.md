# BEST-PARTS — Frey & Osborne → AutoFirm

## ADOPT
- **The three engineering-bottleneck axes as AutoFirm's automatability-SCORING rubric.** For every
  leaf function/task in the taxonomy (sources 01/03), AutoFirm scores how *hard-to-automate* it is
  along Perception-and-Manipulation, Creative-Intelligence, and Social-Intelligence. **Build
  implication:** `automatability/bottleneck_scoring.py` produces a per-task vector on these 3 axes;
  high scores on any axis → keep human-in-the-loop / flag for HITL gate (CLAUDE §A7.2).
  This is *general* (the axes are task properties, not industry-specific) → satisfies §3.9.
- **The wages/education ↔ automatability negative correlation** is a useful *sanity prior* for
  AutoFirm's effort allocation: high-routine, low-discretion tasks are the highest-confidence
  automation targets and should be sequenced first in a client build.
- **The probability-bin scheme (>0.7 high / 0.3–0.7 medium / <0.3 low)** gives AutoFirm a ready,
  citable thresholding for its own automation decisions — but applied at the *task* level (see
  REJECT below), not the occupation level.

## REJECT / use-with-care
- **REJECT the occupation-level unit of analysis and the bare 47% headline.** The single most
  important lesson from the surrounding literature (source 07 Arntz/OECD: 9% on a task-based method;
  source 06 McKinsey: <5% of jobs fully automatable) is that **whole occupations rarely automate;
  individual tasks do.** AutoFirm must score at the *Activity/Task* level of the APQC hierarchy,
  NOT at the job level. Citing 47% without this caveat is a misrepresentation risk.
- **Reject the hand-labelled training set as a fixed ground truth.** 70 expert labels from 2013 are
  pre-LLM and stale; AutoFirm's scoring must be re-derived against current capability evidence
  (source 09 Eloundou) — Frey-Osborne supplies the *axes/method*, not the *current scores*.

## Concrete build implication
- Component: `automatability/bottleneck_scoring.py` — scores each taxonomy *task* on the 3 bottleneck axes (0–1), thresholded into high/med/low automation suitability; tasks high on Social or Creative intelligence are auto-routed to a HITL gate.
- Test it drives: a boundary test asserting tasks scored >0.7 on Social-Intelligence (e.g. "negotiate a contract", "console an upset customer") are NEVER auto-executed without HITL — a fail-closed teeth test (mutate the threshold, assert the gate still fires).
