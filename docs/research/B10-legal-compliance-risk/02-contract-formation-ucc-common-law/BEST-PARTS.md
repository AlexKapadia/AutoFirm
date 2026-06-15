# BEST-PARTS — Contract formation (common law vs. UCC)

## ADOPT
- **A1. Typed contract-formation contract.** AutoFirm represents every agreement it forms/executes as a
  structured object with the **formation invariants as required fields**: `offer`, `acceptance`,
  `consideration`, `capacity`, `legal_purpose`, plus `governing_regime ∈ {common_law, UCC_goods}`.
  A deal object missing any element is **refused** (fail-closed, CLAUDE.md §5.6) — no "implied" assent.
- **A2. Regime router.** Because the UCC (goods) and common law (services) diverge on the mirror-image
  rule, definiteness, and revocability, the playbook **routes by subject-matter** first: a `goods` deal
  applies §2-204/205/207 defaults; a `services` deal applies strict mirror-image + all-material-terms
  definiteness. Build implication: a deterministic `classify_subject_matter()` gate before term checks.
- **A3. Firm-offer / definiteness checks as guardrails.** For goods deals the engine may rely on
  UCC **gap-fillers** (quantity is the only hard-required term); for services it must **block** a deal
  with any undefined material term. This is a deterministic, auditable rule set — exactly the kind of
  "hard guardrail" core CLAUDE.md §3.5 wants, with ML only refining wording, never assent.

## REJECT / DEFER
- **R1. REJECT auto-binding on ambiguous assent.** AutoFirm must not treat silence or a non-matching
  reply as acceptance; mirror-image/§2-207 nuance means assent is a *decision*, not a default. Any
  borderline case escalates to a human gate (ties to source 06 electronic-agent attribution).
- **R2. DEFER CISG / non-US contract regimes** to the jurisdiction module (Jenkins covers CISG too but
  it is out of L1 core scope) — keeps the engine general, per-jurisdiction data pluggable.

## Build implication (concrete)
- **Component:** `legal/contracting/formation_guard.py` (and a `regime_router`).
- **Contract:** `DealAssent{ offer, acceptance, consideration, capacity, legal_purpose,
  governing_regime, material_terms_defined: bool, fired_rules[] }`.
- **Test (adversarial + boundary):** counter-offer-treated-as-acceptance must FAIL the guard; a goods
  deal missing price but having quantity must PASS (gap-filler) while a services deal missing price must
  FAIL (definiteness). Boundary on the §2-205 "up to 3 months" firm-offer window (89 vs 90 vs 91 days).
