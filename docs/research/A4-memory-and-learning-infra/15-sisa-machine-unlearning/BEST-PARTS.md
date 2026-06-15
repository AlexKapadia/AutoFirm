# BEST-PARTS — Machine Unlearning (SISA)

## ADOPT
- **Quantify why external memory is the right deletion architecture.** SISA shows even an
  *optimized* weight-level forgetting still costs a multi-dataset-average retraining penalty
  (4.63x / 2.45x / 1.36x speed-ups are *over* full retraining — i.e. still bounded by retraining).
  Build implication: AutoFirm's durable memory stays in an **external index/DB** (folder 05) so the
  VF primitive is an O(1) exact drop+reindex, not a retraining job. This is a *measured* argument,
  not a preference.
- **Define "exact deletion" precisely for the test suite.** SISA's gold-standard definition (model
  state is *as if the sample had never been in the training set*) becomes AutoFirm's VF assertion:
  after delete, the record is unreachable by exact-match AND near-duplicate-embedding query, and the
  index state is identical to never-having-stored-it (modulo unrelated entries).

## REJECT / DEFER
- **Reject SISA-style weight-level unlearning as AutoFirm's primary deletion path** — AutoFirm hosts
  a third-party Claude model whose weights it cannot reshard or retrain; SISA is infeasible here.
  Its *value* is as the primary citation proving exact deletion is hard in-weights, which is exactly
  why external memory wins. (DEFER: SISA-style sharding could apply to any *local* fine-tuned helper
  model AutoFirm might later own — flagged for L2.A4, not adopted now.)

## Build implication (concrete)
Provides the **primary, peer-reviewed** (IEEE S&P) backbone for the safety/correctness-critical VF
claim — lifting it from "two surveys" to "two surveys + a top-venue primary with measured costs" —
and converts the external-memory architecture choice from an assertion into an evidence-backed,
cost-quantified decision feeding L2.A4.
