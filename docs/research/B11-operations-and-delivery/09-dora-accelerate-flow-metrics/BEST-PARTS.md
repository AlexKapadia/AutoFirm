# BEST-PARTS — DORA / Accelerate

## What AutoFirm should ADOPT

### 1. The Four Keys as AutoFirm's OWN delivery-operations dashboard — ADOPT
AutoFirm is fundamentally a software/services delivery operation, so the DORA Four Keys are the
**directly applicable, evidence-backed** operations KPIs for both AutoFirm itself and the software it
ships for clients (L2.B14). **Build implication:** instrument Deployment Frequency, Lead Time, Change
Failure Rate, and Time-to-Restore over AutoFirm's commit/gate history (it commits+pushes at every
gate, §3.13 — the raw events exist for free), and report them as numeric, tiered KPIs in `evidence/`.

### 2. "Speed and stability are not a trade-off" — ADOPT as a design principle
This is a load-bearing, replicated finding: you do NOT trade quality for velocity. **Build
implication:** it is the empirical justification for CLAUDE's whole stance — small batches + tests
-with-teeth + fast gates produce *both* faster delivery AND fewer defects. AutoFirm should refuse the
false choice of "ship fast OR ship safe" and optimize the four keys jointly.

### 3. Lean lineage → close the B11 loop (Little's Law made measurable) — ADOPT
DORA operationalizes lean flow: small batch → low WIP → (by Little's Law, 05) short Lead Time, and
high Deployment Frequency. **Build implication:** Lead Time for Changes IS the "W" of Little's Law for
the software value stream; cutting WIP (kanban limits, 01; DBR rope, 04) is the mathematically-grounded
lever to improve it. This ties every B11 source into one coherent, testable delivery model.

### 4. Elite/High/Medium/Low tiers → a benchmark scale — ADOPT (definitions only)
**Build implication:** AutoFirm can grade a client's (or its own) delivery maturity on the four-key
tiers. Use the *tier definitions/structure*; compute the client's actual placement from their real
data rather than asserting published threshold numbers (which drift yearly).

## What AutoFirm should REJECT / bound
- **REJECT importing specific year's threshold numbers** (e.g. "Elite = deploy on-demand, LT < 1hr")
  as fixed truths — they change across annual reports and would overfit to one survey year. Cite the
  *metric definitions and tier structure*; derive placement from the client's data.
- **REJECT four-keys as the ONLY ops metrics.** They cover software *delivery*; pair with SCOR (03,
  physical/supply ops), service-profit chain (06, service ops), and quality DPMO (08) per industry
  (B12). DORA leads for digital/SaaS panel rows, not for, e.g., restaurant supply ops.
- **REJECT gaming-prone single-metric optimization** (e.g. inflating Deployment Frequency with empty
  deploys) — the four keys must be reported together (speed AND stability) to be meaningful.

## Concrete build implications
- **Component:** `operations/dora_metrics` — computes DF, LT, CFR, MTTR from commit/deploy/incident
  events; assigns a tier from the client's own distribution.
- **Contract:** Lead-Time-for-Changes is wired to the same `littles_law` primitive (05) as the
  software value stream's W; delivery KPIs report speed AND stability jointly (never one alone).
- **Test:** deterministic unit tests for each of the four metrics over synthetic event logs
  (boundary cases: zero deploys, all-failed deploys); a test that the dashboard refuses to report a
  speed metric without its paired stability metric (anti-gaming guard).
