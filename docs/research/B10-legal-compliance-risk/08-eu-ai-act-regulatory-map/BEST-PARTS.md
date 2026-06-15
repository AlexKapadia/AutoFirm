# BEST-PARTS — Regulatory map (EU AI Act + sector regimes)

## ADOPT
- **A1. Compliance as a PARAMETERIZED regulatory-profile engine (not hard-coded rules).** Given a
  client company's (industry, jurisdiction, data-types-handled), the engine emits the **applicable
  regulatory bundle** — e.g. {healthcare, US} → HIPAA/HITECH; {fintech, US} → GLBA+BSA/AML+KYC+PCI DSS;
  {any, EU, personal-data} → GDPR; {any, EU, AI-system} → EU AI Act tier. This is the concrete mechanism
  that makes B10 generalize across the **fixed industry panel** (B12) — each panel row gets a different,
  evidence-backed compliance profile. Overfitting to one industry's regime = FAIL.
- **A2. Risk-tier classification of AutoFirm's OWN agents under the EU AI Act.** AutoFirm must classify
  each agent capability against the AI Act tiers and **refuse to build/deploy a prohibited-practice
  capability** (Art. 5) — a fail-closed legal gate. High-risk capabilities trigger the **conformity-
  assessment + Arts. 8-15** checklist (risk mgmt, data governance, logging, transparency, human
  oversight, accuracy/robustness) — which overlaps heavily with controls already in CLAUDE.md §5.6.
- **A3. Map AI Act high-risk requirements onto existing platform controls** (they are nearly identical):
  Art. 12 logging → A6.2 audit log; Art. 14 human oversight → HITL gate; Art. 15 accuracy/robustness →
  CLAUDE.md §3.6 tests-with-teeth. B10 supplies the **legal citation** for each control's necessity.

## REJECT / DEFER
- **R1. REJECT a single static compliance checklist.** Regulations differ by industry AND jurisdiction
  AND change over time — the regulatory content must live in a **versioned, dated data file**, never
  baked into code (no stale magic constants; CLAUDE.md §3.9).
- **R2. DEFER full per-jurisdiction statutory detail** (every US state privacy law, every national DPA)
  to the pluggable jurisdiction module; L1 fixes the **map structure**, not exhaustive content.

## Build implication (concrete)
- **Component:** `legal/compliance/regulatory_profile_engine.py` + versioned `regulatory_profiles/`
  data; `legal/compliance/ai_act_tier_classifier.py`.
- **Contract:** `RegulatoryProfile{ industry, jurisdiction, data_types[], applicable_regimes[],
  ai_act_tier, required_controls[], conformity_assessment_required: bool }`.
- **Test (generality + fail-closed):** run the engine across all 8 fixed-panel industries × {US, EU} and
  assert each yields the correct regime bundle (HIPAA for healthcare, GLBA/AML for fintech, etc.);
  assert a prohibited-practice capability is REFUSED; boundary on AI Act tier classification.
