# BEST-PARTS — Entity structures

## ADOPT
- **A1. Entity choice = a parameterized decision over 4 axes** (liability, taxation, capital-raising,
  admin burden). AutoFirm's legal playbook (**L2.B10**) implements an **entity-selection decision
  function** keyed on these axes + the company's industry/size/funding intent — NOT a hard-coded
  "always LLC". Build implication: a **deterministic rule table** mapping (jurisdiction, funding plan,
  owner count, liability appetite) → recommended entity, with the **rule that fired** surfaced in the
  output (CLAUDE.md §3.11 explainability).
- **A2. Liability shield is a first-class invariant.** The recommendation engine must **never** propose
  an unincorporated structure (sole prop / general partnership) for a venture exposing the founder to
  uncapped liability without an explicit, logged warning — fail-closed default to a limited-liability
  form (CLAUDE.md §5.6). Drives a test: *given high-liability industry → engine must surface the shield
  trade-off.*
- **A3. Separate "legal entity type" from "tax election"** in the data model. The contract carries two
  fields (`entity_type` ∈ {LLC, C-corp, S-corp, LP, LLP, sole-prop, partnership}; `tax_classification`
  ∈ {disregarded, partnership, C, S}) because the IRS treats them orthogonally. Prevents the common
  category error of "S-corp is an entity".

## REJECT / DEFER
- **R1. REJECT hard-coding a single jurisdiction's rules into the general engine.** US (IRS/SBA) is one
  parameter set; the engine must accept a **jurisdiction module** (DEFER per-jurisdiction content to a
  pluggable data file, not core logic) so it generalizes beyond the US (CLAUDE.md §3.9 generality).
- **R2. DEFER concrete numeric tax rates** (e.g. QBI 20% deduction, corporate rate) out of L1 — they
  change annually and are **time-sensitive**; they belong in a versioned, dated config consulted at
  runtime, never baked into code (avoids stale magic constants).

## Build implication (concrete)
- **Component:** `legal/entity_selection/` decision engine in the L2.B10 playbook.
- **Contract:** `EntityRecommendation{ entity_type, tax_classification, jurisdiction, fired_rules[],
  liability_shield: bool, warnings[] }`.
- **Test (efficacy + boundary):** run the engine across all 8 fixed-industry-panel rows
  (QUESTION-ONTOLOGY B12) and assert a sensible, liability-aware result for **each** — overfitting to
  "SaaS → Delaware C-corp" alone is a FAIL.
