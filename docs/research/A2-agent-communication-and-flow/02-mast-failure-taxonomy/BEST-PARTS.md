# BEST-PARTS — MAST Failure Taxonomy

## What AutoFirm should ADOPT and why

1. **Treat MAST as the failure-mode test matrix for inter-team comms.** ADOPT all 14 modes as
   named adversarial test cases (CLAUDE S3.6). Build implication: A2's reliability suite must
   contain a deliberately-hunted test per FC2 mode — inject information withholding (FM-2.4),
   conversation reset (FM-2.1), reasoning-action mismatch (FM-2.6) — and assert the protocol
   detects/contains it. A green suite that does not exercise these is "too easy".

2. **Inter-agent misalignment is the dominant *comms* failure (36.94%).** ADOPT this as the
   priority ordering for A2: communication-protocol design must first kill FC2 modes. Build
   implication: the message contract (source 01) MUST make "critical data" explicit and
   mandatory (typed required fields) so FM-2.4 information-withholding fails closed, not silently.

3. **The "lossy game-of-telephone" insight -> typed, complete handoffs.** ADOPT structured,
   schema-validated handoffs over free-text chat between agents. Build implication: every
   handoff message validates against the receiver's input schema before send; missing required
   field = refuse (fail-closed), directly attacking context-loss-during-handoff.

4. **Verification is a first-class comms step (FC3 = 21.30%).** ADOPT an explicit verification
   message/role in the flow (premature-termination and incorrect-verification are real modes).
   Build implication: the workflow contract requires an affirmative "verified" message with
   evidence before a task is marked done — feeds A9 and CLAUDE S3.7 iterate-to-perfection loop.

## What AutoFirm should REJECT / note

- **REJECT the assumption that a better protocol alone fixes coordination.** The paper's own
  finding: protocol/context fixes are "often insufficient" for FC2; deeper role-discipline and
  social reasoning are needed. Build implication: pair the typed contract with hard role
  boundaries + supervision (orchestrator veto), not protocol design in isolation. This is why A2
  must connect to A1 (orchestration) and A6/A7 (audit/oversight), not stand alone.
- **REJECT free-form emergent chat as the default coordination substrate** — it concentrates
  exactly the FC2 failures this dataset measures.

## Concrete build implication / quantified targets
- A2 reliability gate: 14 MAST-derived adversarial tests, all 6+ FC2 modes covered, all killed
  by the protocol+supervision design (mutation-tested, CLAUDE S3.6).
- Baseline to beat: inter-agent misalignment ~36.9% of failures in ungoverned MAS — AutoFirm's
  golden metric for L2 is *measured* reduction of FC2-class failures vs this baseline, not
  asserted.
