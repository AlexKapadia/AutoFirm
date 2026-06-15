# BEST-PARTS — Configurable Reference Process Models (C-EPC)

## ADOPT (the formal backbone of AutoFirm's generalization layer)

1. **Adopt "one configurable reference model -> many individualized variants" as the core pattern
   for ALL AutoFirm playbooks.** This is the rigorous, peer-reviewed answer to B12's "any company"
   problem: don't author N industry playbooks; author ONE configurable playbook with marked
   **variation points**, and *derive* each industry's playbook by selecting variants. Directly
   mirrors the APQC spine+overrides split (source 04) but adds formal mechanism.

2. **Adopt the explicit design-time vs run-time decision split (claim 4).** This is the single most
   useful idea here. AutoFirm must distinguish:
   - **Configuration decisions** (design-time, per *industry/company class*) = which playbook
     variant to instantiate - resolved once from the `IndustryProfile`/NAICS key.
   - **Routing/operational decisions** (run-time, per *case*) = made during execution.
   Conflating them is the classic overfitting trap; keeping them separate is what makes the platform
   general AND auditable.

3. **Adopt configuration REQUIREMENTS + GUIDELINES (claim 3).** AutoFirm's variation points must
   carry: (a) **requirements** = hard predicates that keep a derived playbook *lawful/coherent*
   (e.g. "if regulated_tier=heavy then compliance-review step MUST be ON" - a fail-closed
   constraint, ties to A7); and (b) **guidelines** = recommended-but-overridable defaults per
   industry. This gives a principled, testable derivation, not ad-hoc if/else.

4. **Adopt ON / OFF / OPT variation-point semantics (claim 2).** Each playbook step is a function
   that an industry override can switch ON (mandatory), OFF (excluded), or OPT (optional/conditional)
   - a tiny, complete vocabulary that covers most cross-industry variation cleanly.

## REJECT
1. **REJECT the EPC notation itself.** The empirical paper (A) found C-EPC notation is "sufficient
   yet improvable" - usable but ergonomically limited. Take the *configuration semantics*, not the
   EPC diagram language. AutoFirm expresses variation points as typed data, not EPC graphs.
2. **REJECT unconstrained configuration.** Without configuration requirements, derived variants can
   become incoherent. Mandate that every variation point ships with at least its lawfulness
   predicate (no naked toggles).

## Build implication (concrete)
- Contract: `VariationPoint { step_id, mode: ON|OFF|OPT, requires: Predicate[], guideline_default }`;
  a playbook = invariant spine (source 04) + a set of variation points.
- `derive_playbook(industry_profile)` = design-time configuration: resolves each variation point
  from NAICS/GICS/business-model axes, ENFORCES all requirement predicates (fail-closed: refuse to
  emit an unlawful variant), applies guideline defaults otherwise. Run-time routing is a separate,
  later concern.
- Test: property-based - for ALL industry profiles in the fixed panel (and fuzzed profiles),
  `derive_playbook` emits a variant satisfying every requirement predicate; a profile that would
  violate a hard requirement (e.g. heavy-regulated with compliance OFF) is REFUSED, not silently
  produced. This is the determinism + fail-closed evidence for L2.B12.
