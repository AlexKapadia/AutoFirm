# BEST-PARTS — Claessen & Hughes QuickCheck (PBT)

## ADOPT
1. **Property-based testing is mandatory for every parser, validator, classifier, and engine** in client code (already CLAUDE.md §3.6/§5.5). This source is the foundational justification. AutoFirm's client-delivery engine generates PBTs by default for these component types, in the language-native PBT lib (Hypothesis/fast-check/jqwik/PropEr).
2. **Stateful / model-based testing for any API or service.** The Hughes evidence (AUTOSAR, Dropbox) shows random *command-sequence* testing against a model finds deep stateful/protocol bugs example tests miss. For client products with stateful APIs, AutoFirm should generate a model and fuzz command sequences — not just single-call property checks.
3. **Shrinking is non-negotiable.** Adopt only PBT libraries with automatic counterexample shrinking, so agent-readable minimal failing cases drive the iterate-to-perfection loop.

## REJECT
- Reject hand-rolled random testing without shrinking/distribution monitoring — it produces noisy, non-minimal failures agents cannot act on cleanly.
- Treat the "hundreds of bugs" testimony as directional only (vendor source); the *quantified* PBT-efficacy claim is carried by source 04.

## Concrete artifact this drives
- A `pbt-generator` step in the client-delivery engine that, given a typed contract (from the CTO data contracts), emits property tests + a stateful model harness; output feeds the same mutation gate (source 01) to prove the PBTs actually have teeth.
