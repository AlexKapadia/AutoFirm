# BEST-PARTS — Empirical PBT in Python (OOPSLA 2025)

## ADOPT
1. **Quantified justification to prefer PBT over example tests.** ~50x more mutations killed per PBT vs. per unit test is the number AutoFirm cites in `evidence/` to justify the PBT-first policy. It also gives a concrete efficacy target: a generated PBT should kill materially more mutants than an equivalent example test, or it is too weak.
2. **Prioritise the high-yield PBT patterns.** Exception-raising, collection-membership, and type-checking properties are ~19x more effective than other PBT kinds. AutoFirm's PBT generator should **bias toward these patterns first** for every component (assert it raises on bad input, assert membership/round-trip invariants, assert type/shape postconditions) before lower-yield properties.
3. **Use the 12-category taxonomy** as the menu the generator picks from, ensuring coverage of property *kinds*, not just inputs.

## REJECT
- Reject treating all PBTs as equal — the data shows large variance; a "property test exists" checkbox is not enough, the *kind* matters.

## Concrete artifact this drives
- PBT-generator policy: for each typed component, emit (a) an input-validation/exception property, (b) a round-trip/membership invariant, (c) a type/shape postcondition — the three highest-yield categories — then measure mutation kill-rate as the acceptance check. Target stated in `evidence/`: PBT mutation-kill >> matched example-test baseline.
