# SYNTHESIS — B16 Output Review & Verification (the independent human-facing review gate)

> Feeds the lane `feature/human-output-review-gate` and its plan
> `docs/architecture/human-output-review-gate-plan.md`. Complements **B15** (artifact *generation*):
> B16 is the **independent EVALUATOR / RELEASE GATE** that must catch every error before any artifact
> reaches an owner, CEO, or investor. Binds CLAUDE.md §2 (CRO / generator-evaluator), §3.4
> (evidence-gated method choice), §3.6 (tests with teeth + mutation), §3.11 (zero numerical error +
> explain-every-decision), §4.9 step 5, §5.6 (fail-closed).

## 1. The question
What is the full method space for **verifying** a generated artifact, and which methods earn their
place in a fail-closed, institution-grade review gate — and where (if anywhere) does a **model-based
reviewer** justify itself by *evidence* rather than taste?

## 2. Surveyed method space (ADOPT / REJECT)

### 2.1 Why an independent gate at all (not self-review)
- Self/producer review catches only **~50% of errors** (Panko 01) — ICAEW puts self-review at
  **34%-69%** (10); average inspection detection **~60%** (01); producers are **overconfident** (01).
- **ADOPT (now triple-sourced, was single-Panko in B15):** acceptance NEVER comes from the builder.
  Independence is the source of value (Boehm/IV&V 09; ICAEW third-party review 10; Panko 01/02).

### 2.2 Deterministic / mechanical verification (the FLOOR)
- Inspection software reliably clears the **mechanical/structural/omission** classes humans miss —
  orphan constants, inconsistent row formulas, blank-reference, recomputation, identities
  (Aurigemma & Panko 02; ICAEW five-stage 10; Panko-Halverson taxonomy 03).
- **ADOPT as MANDATORY, fail-closed:** ACCOUNTING_IDENTITY (A=L+E exact to the unit, Decimal),
  NUMERIC_RECOMPUTE (recomputed == cached, exact), SPEC_ROUND_TRIP, FILE_OPENS_CLEAN,
  FAST_LINT (orphan-constant + row-consistency + statement/period completeness = omission defence),
  IBCS_SUCCESS + VISUAL_INTEGRITY (IBCS CHECK: no misleading axes — 11).

### 2.3 Model-based review (LLM-as-judge) — ADVISORY ONLY, evidence-gated
- A single strong judge matches humans **>80% agreement** on subjective preference (Zheng 04) BUT
  carries **position, verbosity, and self-enhancement biases** (04), with self-preference quantified
  at **~0.520 for GPT-4** (TPR 0.945 vs TNR 0.425 on its own outputs — 06), driven by a
  **low-perplexity/familiarity** effect (06).
- Decisively, on items the judge **cannot itself solve**, agreement **collapses** — Cohen's kappa
  **0.78 -> 0.14** (07) — i.e. toward chance exactly where it matters. Reference-grounding partially
  rescues it (**0.21 -> 0.67**, 07).
- A **diverse jury (PoLL)** beats a single big judge, correlates better with humans, **~7x cheaper**,
  and dilutes bias (Verga 05) — *if* members are genuinely different families (correlated-error
  caveat, 05).
- **ADOPT only as an add-only ADVISORY layer (CLAUDE §3.4):** it may *raise* a blocking finding on the
  **semantic/Eureka-logic residue** the deterministic floor provably cannot reach (02, 03), but can
  **NEVER clear a deterministic FAIL** (06/07 show it would wave through fluent-but-wrong work). If
  enabled, it must be (a) a **small cross-family jury**, (b) **reference-grounded** with the
  deterministic facts (recomputed values + spec) as its reference, (c) **position-swapped**, and
  (d) **kill-switchable**. **REJECT** any LLM-judge-as-acceptance-authority.

### 2.4 Release-gate design + metrics
- **ADOPT fail-closed quality gate** (SonarQube model; Boehm cost curve 09; escape-rate practice 12):
  PASS is the only path to delivery; absent/ambiguous -> refuse. The plan's ReleaseDecision matches.
- **ADOPT kappa as the headline evidence metric** (Landis-Koch bands 08): gate-verdict vs verified
  gold-reviewer.
- **REJECT pass-rate / coverage as proof** — a 95%-green gate can still leak (12; CLAUDE §3.6).

## 3. What the DETERMINISTIC FLOOR must check (mapped to the defect taxonomy, 03)
| Panko-Halverson class | Deterministic check (must KILL it) | Severity |
|---|---|---|
| Mechanical (typo / wrong reference / hard-coded where formula belongs) | NUMERIC_RECOMPUTE + FAST_LINT orphan-constant + SPEC_ROUND_TRIP | BLOCKING |
| Pure logic (wrong formula) | ACCOUNTING_IDENTITY (A=L+E exact) + SPEC_ROUND_TRIP | BLOCKING |
| Omission (missing line/statement/period) | FAST_LINT completeness | BLOCKING |
| Visual-integrity (misleading/truncated axis, chartjunk, message<->chart mismatch) | IBCS_SUCCESS + VISUAL_INTEGRITY (IBCS CHECK/EXPRESS) | BLOCKING |
| File invalidity | FILE_OPENS_CLEAN | BLOCKING |
| Eureka / domain-logic residue | NOT deterministically catchable -> MODEL_ADVISORY (advisory) | ADVISORY |
| Qualitative practice (docs/version/notation) | FAST_LINT / ICAEW P7/P17/P19 lint | ADVISORY/BLOCKING per config |

## 4. Whether / when a MODEL-REVIEWER layer is justified by evidence
Justified **only** for the **semantic/Eureka residue** the floor cannot reach (02, 03), and admitted
**only if** a golden-set bake-off shows it **raises gate-vs-gold-reviewer kappa on that residual class
without lowering kappa elsewhere** (CLAUDE §3.4; admission criterion grounded in 04/05/06/07/08). It
ships **OFF by default**; the deterministic core is the product. When on: small cross-family jury,
reference-grounded, position-swapped, add-only, kill-switchable.

## 5. Metrics that prove the gate works (-> evidence/, CLAUDE §3.10)
1. **Defect-detection rate** by taxonomy class on a labelled golden set of planted real-world errors
   (off-by-one balance, sign-flip cash line, hard-coded-where-formula, dropped statement, truncated
   axis) — **target ~100% on must-block classes**, benchmarked against human ~60% / solo ~50% (01).
2. **False-pass / escape rate** — fraction of planted defects that would reach a human — **target ~0%**
   on the controlled set; <10% "excellent" band on held-out real artifacts (09, 12).
3. **False-positive rate** on known-good artifacts — **target 0%** (a gate that cries wolf gets bypassed).
4. **Cohen's / Fleiss' kappa vs a verified gold reviewer** (08) — **target >= 0.80 "almost perfect"**
   (deterministic + verified labels), reported with the Landis-Koch band.
5. **Determinism** — identical artifact -> byte-identical verdict over N runs (CLAUDE §3.11).
6. **(If model layer on)** kappa uplift on the residual class vs deterministic-only — the evidence
   that it earned its place; plus jury cost vs single-judge (05).
> Gold-reviewer labels must themselves be **independently verified before use** (07: 35% of MT-Bench
> references were wrong) or the kappa is meaningless.

## 6. Generality (not overfit — CLAUDE §3.9)
Every check is standard-grounded and parameterised: Panko-Halverson classes, FAST/ICAEW structure,
IBCS SUCCESS notation (per-company config, not a hard-coded palette), accounting identities. The gate
must return a sensible verdict for **every** artifact for **any** panel company — proven by property
tests over diverse synthetic specs, never tuned to one fixture.

## 7. Verdict on the existing draft plan
The plan at docs/architecture/human-output-review-gate-plan.md **HOLDS** — its generator/evaluator
split, deterministic-core-with-add-only-model-layer, fail-closed ReleaseDecision, bounded correction
loop, and false-pass guard are all now independently corroborated. Required **strengthenings**: cite
B16 (not only B15's single Panko line); add the Eureka-residue rationale as the *only* justification
for the model layer; if the model layer is enabled make it a reference-grounded cross-family **jury**
with position-swap (04/05/06/07), never a single judge; and report **kappa, defect-detection rate, and
escape/false-pass rate** (not pass-rate/coverage) as the proof.

## 8. Source quality summary
High (peer-reviewed / primary): Panko 01, Aurigemma&Panko 02, Panko-Halverson 03, Zheng 04, Verga 05,
Landis&Koch/Cohen 08, Boehm&Basili 09, ICAEW 10, IBCS 11. Moderate-High: self-preference 06, no-free-
labels 07. Moderate (professional practice): quality-gate/escape-rate 12. The generator/evaluator
mandate, the deterministic floor, and the model-layer-as-advisory decision each rest on >=3 independent
sources. Where arXiv PDFs returned binary to the fetch tool (01/02/03), figures were taken from the
authors' abstracts/HTML/SSR corpus and flagged in each source note rather than fabricated (CLAUDE §3.3).
