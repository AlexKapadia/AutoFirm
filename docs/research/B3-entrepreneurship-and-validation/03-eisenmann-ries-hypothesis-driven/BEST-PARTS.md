# BEST-PARTS — Eisenmann, Ries & Dillard (2011/2013)

## ADOPT
1. **Build-Measure-Learn as the validation loop control flow.** AutoFirm's opportunity-validation
   playbook (L2.B3) implements BML as an explicit iterate-to-perfection loop (CLAUDE SS3.7): smallest
   test -> measure real signal -> update the hypothesis ledger -> pivot/continue/stop.
2. **Validated learning as the success metric, not output volume.** Score a validation run by
   *hypotheses resolved with evidence*, never by artifacts produced.
3. **Encode boundary conditions as a gating rule.** Lean/MVP testing applies under HIGH uncertainty;
   for well-understood or high-stakes/regulated domains the playbook down-weights cheap-MVP testing
   and routes to deterministic analysis / heavier validation. Build implication: an
   uncertainty-classification step that selects the validation strategy, industry-parameterized
   against the fixed industry panel (heavy-regulated rows — fintech, healthcare — get stricter gates).

## REJECT / DEFER
- **Reject treating this note as effectiveness evidence** — it is definitional; cite the RCTs for
  "does it work" (DEPTH-RUBRIC SS1).
- **Defer MVP *type* selection** (concierge, Wizard-of-Oz, landing-page, smoke-test) to L2.B3 design;
  catalogue here, choose by industry later.

## Build implication
A typed `BusinessModelHypothesis` contract (vision -> falsifiable claims) plus a BML loop executor are
the core of L2.B3. The falsifiability framing makes every validation verdict explainable (SS3.11) and
testable for determinism (SS3.6).
