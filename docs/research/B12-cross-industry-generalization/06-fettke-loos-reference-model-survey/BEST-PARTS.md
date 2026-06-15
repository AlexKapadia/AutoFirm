# BEST-PARTS — Fettke, Loos & Zwicker (Reference Model Survey)

## ADOPT
1. **Adopt the two-property definition of a "general playbook".** A reference model = generic +
   recommendation. So an AutoFirm playbook is "general" (passes B12) iff it is BOTH (a) reusable
   across the industry class (universality) AND (b) normative best-practice (recommendation), not a
   one-off. This gives QA a crisp, citable acceptance test for "is this playbook actually general?"
   beyond "it ran for one company."

2. **Adopt the explicit similarity assumption as a PROOF OBLIGATION (claim 4).** The most important
   takeaway: generality is an *empirical* claim that enterprises are similar enough along the spine.
   Therefore AutoFirm must EMPIRICALLY VALIDATE generality against the fixed industry panel (the
   B12 golden set) rather than assume it - directly justifying CLAUDE.md §4.5 / the panel test.
   A playbook that only "works" because the test firms happened to be similar is overfit.

3. **Adopt the multi-dimensional classification criteria for the override library.** Tag each
   AutoFirm industry override pack with: application domain (NAICS prefix), the function it refines
   (PCF category), and its evidence/evaluation status. Mirrors Fettke/Loos's classification
   dimensions and makes the override library navigable and auditable.

## REJECT
1. **REJECT "best-practice once, frozen forever."** The recommendation property implies a CURRENT
   best practice; reference models age. AutoFirm override packs must be versioned and revisable as
   evidence changes (ties to the research iterate-to-perfection loop), not baked in.
2. **REJECT generality-by-assertion.** Because generality rests on a similarity assumption,
   AutoFirm may NOT mark a playbook "general" without panel evidence. (QA FAIL condition.)

## Build implication (concrete)
- Definition-of-general (for QA): `is_general(playbook)` requires (a) it derives a sensible variant
  for every fixed-panel row AND (b) each step is a cited best-practice, not an ad-hoc choice.
- Drives the **panel-coverage test** that is the heart of L2.B12: run `derive_playbook` across all 8
  panel industries; assert each variant is non-empty, lawful (source 05 requirements), and sensible;
  any failure = not-general = FAIL. This is the empirical discharge of the similarity assumption.
