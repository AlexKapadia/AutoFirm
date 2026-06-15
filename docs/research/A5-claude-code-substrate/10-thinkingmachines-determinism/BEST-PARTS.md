# BEST-PARTS — LLM-inference determinism for AutoFirm

## ADOPT (as the binding stance on L1.A5.2 model-output determinism)

- **Adopt the explicit two-layer determinism model for AutoFirm (resolves L1.A5.2):**
  1. **Substrate/state layer is deterministic** — sessions, transcripts, `--resume`, settings
     precedence (sources 01/04/08) replay state faithfully.
  2. **Model-output layer is NOT inherently deterministic** — even at temperature 0, identical
     prompts can produce different completions because inference servers lack batch invariance
     (claim 1-3). AutoFirm does NOT control Anthropic's serving batch size, so it MUST assume the
     LLM layer is stochastic.
  Build implication (directly drives CLAUDE.md §3.5 hybrid design): any decision that must be
  reproducible/auditable to the unit (CLAUDE.md §3.11 "zero numerical errors on deterministic
  paths") is computed in **deterministic CODE**, not by the LLM. The LLM is a soft/advisory layer
  whose outputs are validated, never the source of a deterministic guarantee.
- **Adopt statistical validation for any LLM-driven decision (feeds A9.2).** Because the same
  input yields a distribution of outputs, AutoFirm's evaluation harness must use repeat-trial
  testing (run N times), report agreement rate / CIs, and set thresholds — exactly the "80 unique
  completions out of 1000" reality (claim 3). A single-run "it passed" is not evidence. This is
  the quantified rigor the evidence showcase (CLAUDE.md §3.10) needs.
- **Use the experiment's numbers as a calibration baseline** for AutoFirm's own determinism tests
  (e.g. measure completion-agreement rate across N identical agent runs; the "token 103 / 992-vs-8"
  example shows divergence can be a single-token flip with large downstream effect).

## REJECT

- **Reject any AutoFirm claim that LLM outputs are deterministic because temperature=0 or because
  `--resume` replays state.** The source directly refutes this (claim 2). Determinism via
  batch-invariant kernels is achievable only by controlling the inference server, which AutoFirm
  (a CLI consumer of a hosted model) does not.
- **Reject sole reliance on the LLM for safety-/correctness-critical numeric or rule decisions**
  (CLAUDE.md §3.5/§3.11) — push those to deterministic code paths with property-based tests.

## Concrete build implications
- Design rule (binding): deterministic core (auditable rules/arithmetic, exact-to-the-unit) +
  optional stochastic LLM layer; never let the stochastic layer own a must-be-reproducible output.
- Contract: LLM-driven outputs carry a confidence/agreement signal and are re-runnable for
  evidence.
- Test (A9.2): repeat-trial harness runs identical agent tasks N times, asserts agreement-rate
  thresholds and reports CIs; deterministic-code paths assert bit-identical outputs across runs.
