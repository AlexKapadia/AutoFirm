# Decision record — output-review model-advisory layer (P3): evidence-based **DEFER**

**Status:** DEFER (deferred, not rejected). Add-only re-open path preserved.
**Scope:** `autofirm.output_review` — Phase 3 "optional model reviewer" of the
human-output-review-gate plan (`human-output-review-gate-plan.md` §Phase 3, lines 250–253;
§Risks 3).
**Authority for this decision:** CLAUDE.md §3.4 (measure, never pick a method by taste)
and §3.5 (hybrids only where evidence shows they earn their place).
**Date:** 2026-06-19.

---

## 1. Decision

**Do not build the model-advisory reviewer now.** The deterministic floor is
acceptance-complete and **ships without it**. The contract surface for the layer
already exists (so it can be added later **add-only**, without disturbing the core),
and a concrete re-open path with acceptance metrics is fixed below (§5).

This is the standing-bar-compliant outcome for P3: the layer's only job is to reach a
defect class the floor provably cannot, and **building it now would be speculative ML**
— it depends on infrastructure and a labelled corpus that do not yet exist (§4).
Deferring on measured evidence *is* "doing what needs to be done" for P3, not skipping it.

---

## 2. What the deterministic floor already achieves (measured, not asserted)

Every number below is read from the committed evidence showcase
([`evidence/output_review/stats/RESULTS.md`](../../evidence/output_review/stats/RESULTS.md)
and [`evidence/output_review/_measured/efficacy_metrics.json`](../../evidence/output_review/_measured/efficacy_metrics.json)),
produced by running the **real** `autofirm.output_review` gate over the labelled
synthetic golden set (18 cases: 14 planted defects, 4 known-good controls; 7-check floor).

| Property | Measured result | Source |
| --- | --- | --- |
| Defect detection (all must-block classes) | **14 / 14 = 100%** | `RESULTS.md` §Headline; `efficacy_metrics.json` `detection_by_panko_class` |
| Detection on **MECHANICAL** (7 planted) | **100%** (Wilson 95% low 0.646) | `efficacy_metrics.json` |
| Detection on **PURE_LOGIC** (6 planted) | **100%** (Wilson 95% low 0.610) | `efficacy_metrics.json` |
| Detection on **OMISSION** (1 planted) | **100%** (Wilson 95% low 0.207) | `efficacy_metrics.json` |
| Escape / false-pass rate (planted) | **0 / 14 = 0.000** | `RESULTS.md`; `efficacy_metrics.json` `headline.escapes` |
| False-positive rate (controls) | **0 / 4 = 0.000** | `RESULTS.md`; `efficacy_metrics.json` `headline.false_positives` |
| Determinism (verdict stability) | **1 unique digest / 3,600 reviews** (18 cases × 200 runs) | `RESULTS.md` §Determinism; `efficacy_metrics.json` `determinism` |
| Line / branch coverage | **100.0% / 100.0%** (691 stmts, 130 branches) | `RESULTS.md` §Coverage |
| Mutation survivors (package) | **0** (25 modules, score 1.0, fail-closed grading) | `RESULTS.md` §Mutation score |

The Wilson lower bounds sit below 1.0 only because a finite golden set cannot *prove* a
population rate of exactly 1.0; the **point estimate is 100% on every must-block class
with zero misses** (`RESULTS.md` §Defect-detection rate). On the three Panko-Halverson
classes the floor is responsible for, it is **measurably effective**, not merely
fault-free.

---

## 3. The one class the floor provably cannot reach: EUREKA

The Panko-Halverson taxonomy has four classes (`DefectClass` in
[`review_finding_and_severity_contracts.py`](../../src/autofirm/output_review/review_finding_and_severity_contracts.py)):
`MECHANICAL`, `PURE_LOGIC`, `OMISSION`, and `EUREKA` ("wrong domain model/approach —
not deterministically catchable").

The canonical, runtime check→class map `CHECK_DEFECT_CLASSES` in the same file is **total
over `ReviewCheckId`** and assigns:

```
MODEL_ADVISORY -> frozenset({DefectClass.EUREKA})
```

while every one of the seven deterministic checks maps only to
`MECHANICAL` / `PURE_LOGIC` / `OMISSION`. **`EUREKA` is the sole defect class no
deterministic check covers** — a "wrong domain model" passes recomputation, the
accounting identity, the spec round-trip, and file-integrity checks because it is
internally consistent and merely *wrong about the world*. This is corroborated by
[B16 SYNTHESIS](../research/B16-output-review-and-verification/SYNTHESIS.md) (the
semantic/Eureka residue the floor "provably cannot reach", §2.3/§4; sources 02, 03) and
[B15 SYNTHESIS](../research/B15-artifact-generation/SYNTHESIS.md), and is recorded in the
plan's RATIFIED-per-B16 constraints (`human-output-review-gate-plan.md` §RATIFIED, item 2).

**The model-advisory layer is the *only* justification for `EUREKA`** — and the *only*
defect class that justifies it.

---

## 4. Why it is already safe to defer — the layer is contract-constrained, not load-bearing

The layer can be added later **add-only** because its entire contract surface already
exists and is already constrained:

- **The contract slots exist.** `ReviewCheckId.MODEL_ADVISORY` and
  `CheckSeverity.ADVISORY` are defined in
  [`review_finding_and_severity_contracts.py`](../../src/autofirm/output_review/review_finding_and_severity_contracts.py).
  A future reviewer plugs into these without touching the deterministic core.

- **Advisory-only, by construction.** `CheckSeverity.ADVISORY` is "recorded and
  surfaced, but does not block"; the fail-closed default is `BLOCKING`. An advisory
  finding can never fail a verdict.

- **It can NEVER clear a deterministic BLOCKING finding — structurally, not by
  convention.** `ReviewVerdict.passed` is **derived**, never a trusted input
  ([`review_verdict_contract.py`](../../src/autofirm/output_review/review_verdict_contract.py)):
  the model validator computes `derived = not any(f.severity is BLOCKING …)` and **refuses
  construction** of any verdict whose supplied `passed` disagrees. A `passed=True` over a
  BLOCKING finding is therefore **unconstructible** — no ordering, duplicate, or field
  trick can manufacture a false pass. A purely-advisory layer literally cannot downgrade a
  deterministic FAIL.

Because the core does not depend on the layer and the layer cannot weaken the core,
shipping the gate now forecloses nothing: the layer remains a clean, additive future step.

---

## 5. Decision rationale + re-open conditions

### Rationale (CLAUDE.md §3.4 / §3.5)
Building the layer now would be **speculative ML chosen by taste, not evidence** — exactly
what §3.4 forbids. It **requires** two things that do not yet exist:

1. **An integrated W1 model gateway as a constrained jury.** Per
   [B16 SYNTHESIS §4](../research/B16-output-review-and-verification/SYNTHESIS.md), if the
   layer is ever enabled it must be a **small cross-family jury (PoLL)**,
   **reference-grounded** with the deterministic facts (recomputed values + spec) as its
   reference, **position-swapped**, and **kill-switchable** — never a single
   LLM-judge-as-acceptance-authority. The `autofirm.modelgateway` primitives exist, but
   the advisory **jury reviewer wired against the gateway** (the `model_advisory_reviewer`
   adapter, plan file #16) is not built.

2. **A labelled EUREKA-class golden corpus + a bake-off.** There is no labelled
   semantic/domain-logic ("wrong domain model") corpus and no measured bake-off against a
   verified gold reviewer. Without both, there is nothing to measure, so there is no
   evidence that the layer earns its place.

The deterministic core is **acceptance-complete** on its three classes (§2) and is the
product (plan §Risks 3). Deferring is the evidence-driven call.

### Re-open conditions (build it only when ALL hold)
Re-open P3 and run the bake-off when:

1. the **W1 model gateway is available** to host a cross-family, reference-grounded,
   position-swapped, kill-switchable jury (per §4 above and B16 §4); **and**
2. a **labelled EUREKA-class (semantic/domain-logic) golden corpus** exists, large enough
   to estimate a per-class rate with meaningful confidence.

### Acceptance metrics — enable the layer ONLY if the bake-off shows ALL of:
1. a **real EUREKA-detection lift** on the residual class versus the deterministic-only
   floor, **without lowering** detection elsewhere
   (B16 §4: "raises gate-vs-gold-reviewer kappa on that residual class without lowering
   kappa elsewhere"); **and**
2. **inter-rater agreement κ** (Cohen's / Fleiss') against a **verified gold reviewer** in
   an acceptable **Landis-Koch band** — B16's headline target is **κ ≥ 0.80
   ("almost perfect")**, reported with its band (B16 SYNTHESIS §evidence metrics, src 08);
   **and**
3. **zero ability to clear a deterministic FAIL** — re-verified against the §4 false-pass
   guard.

If any condition fails, the layer **stays disabled by default behind the kill-switch**;
the deterministic core remains the shipped product. This keeps the gate fail-closed and
the decision auditable and replayable.

---

## 6. References

- `evidence/output_review/stats/RESULTS.md`, `…/_measured/efficacy_metrics.json` — measured floor efficacy.
- `src/autofirm/output_review/review_finding_and_severity_contracts.py` — `DefectClass`, `CheckSeverity`, `CHECK_DEFECT_CLASSES` (MODEL_ADVISORY → {EUREKA}).
- `src/autofirm/output_review/review_verdict_contract.py` — the derived-`passed` false-pass guard.
- `docs/research/B16-output-review-and-verification/SYNTHESIS.md` (§2.3, §4) and `docs/research/B15-artifact-generation/SYNTHESIS.md` — Eureka residue as the sole model-layer justification; jury / reference-grounding / position-swap / kill-switch constraints; κ acceptance metric.
- `docs/architecture/human-output-review-gate-plan.md` (§Phase 3; §Risks 3; §RATIFIED per B16) — the P3 scope this record resolves.
- CLAUDE.md §3.4 (evidence-driven method choice), §3.5 (hybrids only on evidence).
