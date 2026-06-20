# Human-Facing Output Review Gate — Implementation Plan & Typed-Contract Design

> **Lane:** B15 `output_review`. **Branch:** `feature/human-output-review-gate`.
> **Status:** CTO/COO plan for orchestrator ratification. **No feature code is implemented by this document.**
> **Research basis:** `docs/research/B15-artifact-generation/SYNTHESIS.md` (Panko generator/evaluator
> split; spreadsheet_audit_gate; FAST/ICAEW error classes; accounting identity A=L+E; IBCS success_rubric;
> visual_integrity_lint; file_opens_clean). Binds CLAUDE.md §2 (CRO / North Star / generator-evaluator),
> §3.2 (institution-grade), §3.6 (tests-with-teeth + mutation), §3.11 (zero numerical errors + explain-every-decision),
> §4.9 step 5 (generator/evaluator split), §5.6 (security), §5.7 (naming + ≤300-line hard limit).

---

## A. Problem statement & the promise it fulfils

### A.1 The promise
AutoFirm's standing promise (CLAUDE.md §2 CRO/North Star, §3.11, §4.9 step 5; MEMORY "human-facing
artifacts & document store") is that **nothing reaches a human — owner, CEO, or investor — until an
INDEPENDENT, multi-pass review has verified it is error-free.** The research mandate is unambiguous
(SYNTHESIS §3, the "Panko confidence gap", src 02): *acceptance NEVER comes from the builder's
self-assessment* — humans estimate ~18% error rates against an actual ~86%, so a generator grading its
own work is structurally untrustworthy. An **independent evaluator** must grade every artifact against a
deterministic rubric/audit gate before delivery.

### A.2 What is missing today
The builders exist (`src/autofirm/artifacts/`) and the human delivery path exists
(`src/autofirm/document_store/librarian_filing_service.py` → the gitignored sensitive store;
`src/autofirm/frontdoor/front_door_response_contract.py` → the human front door). **What is missing is the
gate between them.** Today a builder's output could in principle flow straight to the librarian or the
front door with no independent verification. That is the exact gap this lane closes.

### A.3 The capability (generalizable, never overfit — CLAUDE.md §3.9)
A new package `src/autofirm/output_review/` that provides:

1. An **independent review gate** — never the builder — that runs **N deterministic checks** over a
   built artifact (the file on disk + its originating spec) and emits a typed `ReviewVerdict`.
2. A **send-back-for-correction loop**: when the verdict is FAIL, the gate emits a **structured,
   machine-actionable send-back** (which check failed, where, severity, expected vs actual) that a
   builder/correction agent consumes to regenerate; the corrected artifact is **re-reviewed**; the loop
   repeats until PASS or a bounded attempt budget is exhausted (fail-closed → block delivery).
3. A **release gate**: only a PASS verdict authorises hand-off to `document_store` (librarian) or the
   front door. A FAIL or exhausted-budget verdict **blocks delivery** and is audited.
4. An **optional model-based reviewer layer ON TOP** of the deterministic core — gated on evidence
   (§3.4): it may *raise* findings (e.g. prose coherence, "does this make sense to a domain expert")
   but can **never downgrade or override** a deterministic FAIL. Cheap-model generator output is
   reviewed and corrected; the deterministic checks are the floor that cheap-model mistakes cannot pass.

**Generality:** every check is standard-based and parameterized (FAST/ICAEW/IBCS/accounting identities),
not fitted to one company. The gate must return a sensible verdict for **every** artifact AutoFirm
produces for **any** company on the industry panel — proven by tests over diverse inputs (§D).

---

## B. Architecture — generator/evaluator split as a deterministic core + typed contracts

### B.1 Flow
```
builder output (file on disk + originating spec)
        │
        ▼
┌──────────────────────────────────────────────────────────────┐
│  OutputReviewGate.review(artifact)                             │
│   runs N INDEPENDENT deterministic ReviewCheck implementations │
│   (accounting-identity, spec-round-trip, numeric-recompute,    │
│    file-opens-clean, fast-lint, ibcs-success, visual-integrity)│
│        → collects ReviewFinding[] (severity-tagged)            │
│        → composes a ReviewVerdict (PASS iff zero blocking)     │
└──────────────────────────────────────────────────────────────┘
        │                                   │
   verdict.passed?                          │
        │ no                                │ yes
        ▼                                   ▼
  CorrectionSendBack  ──► builder/correction   ReleaseDecision(authorised=True)
  (structured defects)    agent regenerates         │
        │                       │                    ▼
        └──────── re-review ◄────┘            document_store (librarian)
        (CorrectionLoopState: attempt budget)       / front door
        │ budget exhausted
        ▼
  ReleaseDecision(authorised=False)  ──► delivery BLOCKED + AuditRecord(DENY)
```

The **gate is the only authority** that produces a `ReleaseDecision`. The librarian/front door accept a
delivery **only** with an authorised `ReleaseDecision` (integration in Phase 4) — fail-closed (§5.6):
absent or unauthorised → refuse.

### B.2 Deterministic core vs optional model layer
- **Deterministic core (mandatory, the floor).** Hard checks are pure functions of (file bytes + spec):
  accounting identity **A = L + E exact to the unit** (`Decimal`, zero numerical error — §3.11),
  spec↔artifact round-trip (every spec value/row present and correct in the file), numeric
  recomputation (recomputed formula results match cached values exactly), `file_opens_clean` (valid
  OOXML/PDF, no repair), FAST/ICAEW lint (orphan constants, row-formula consistency, statement
  completeness), IBCS SUCCESS rubric + visual-integrity (no truncated/misleading axes, no chartjunk).
  These are **deterministic and reproducible** — identical inputs → identical verdict (tested, §D).
- **Optional model reviewer (on top, evidence-gated — §3.4).** A `ModelReviewer` adapter behind the
  same `ReviewCheck` Protocol may add advisory findings (prose sense, domain plausibility). It is **add-only
  with respect to FAIL**: it may escalate a PASS to FAIL by raising a blocking finding, but a deterministic
  blocking finding can **never** be cleared by the model layer. It is disabled by default and only enabled
  where a golden-set bake-off shows it earns its place; the kill-switch (§5.6) can disable all external
  model calls without breaking the deterministic gate.

### B.3 Typed contracts (Pydantic, frozen, fail-closed)
Mirrors existing house style (`audit_record_contract.py`, `filed_document_record.py`): `model_config =
ConfigDict(frozen=True, extra="forbid")`, validate-at-boundary, injected clock (never `now()`), enums not
free strings.

| Contract | Shape (essential fields) | Notes |
|---|---|---|
| `CheckSeverity` (StrEnum) | `BLOCKING`, `ADVISORY` | A BLOCKING finding fails the verdict; ADVISORY is recorded but does not block. Fail-closed default = BLOCKING. |
| `ReviewCheckId` (StrEnum) | `ACCOUNTING_IDENTITY`, `SPEC_ROUND_TRIP`, `NUMERIC_RECOMPUTE`, `FILE_OPENS_CLEAN`, `FAST_LINT`, `IBCS_SUCCESS`, `VISUAL_INTEGRITY`, `MODEL_ADVISORY` | Closed set; an unknown check id is refused (audited, fixed set of buckets). |
| `ReviewFinding` | `check_id: ReviewCheckId`, `severity: CheckSeverity`, `locator: str` (sheet!cell / slide#/page#), `message: str`, `expected: str \| None`, `actual: str \| None` | Frozen. `expected`/`actual` carry the exact mismatch (e.g. `A=100`, `L+E=99`) so a send-back is machine-actionable and the verdict explains itself (§3.11). Blank message/locator refused. |
| `ReviewVerdict` | `artifact_ref: str`, `passed: bool`, `findings: tuple[ReviewFinding, ...]`, `checks_run: tuple[ReviewCheckId, ...]`, `reviewed_at: datetime` | `passed` is **derived and validated**: `passed == (no finding has severity BLOCKING)`. A verdict claiming `passed=True` while holding a BLOCKING finding is rejected at construction (fail-closed; cannot manufacture a false pass). `checks_run` proves *which* checks actually executed (an omitted mandatory check is itself a defect — omission defence). |
| `ReviewCheck` (Protocol) | `id: ReviewCheckId`; `run(artifact: ReviewableArtifact) -> tuple[ReviewFinding, ...]` | Each check is independent, single-responsibility, returns findings (empty = clean). The gate composes them; checks never see each other's results (independence). |
| `ReviewableArtifact` | `path: Path`, `kind: DeliverableKind`, `spec: object` (the originating builder spec), `recomputed_values: Mapping \| None` | Frozen handle the checks read from; carries the spec so spec↔artifact round-trip is possible. |
| `CorrectionSendBack` | `artifact_ref: str`, `blocking_findings: tuple[ReviewFinding, ...]`, `attempt: int` | The structured packet handed back to the builder/correction agent: only blocking findings, with locators + expected/actual, so regeneration is targeted not blind. |
| `CorrectionLoopState` | `attempt: int`, `max_attempts: int`, `history: tuple[ReviewVerdict, ...]` | Frozen; advanced functionally (`next_attempt()` returns a new state). Enforces a **bounded** budget so the loop cannot spin forever; budget exhaustion → blocked release (fail-closed). |
| `ReleaseDecision` | `artifact_ref: str`, `authorised: bool`, `final_verdict: ReviewVerdict`, `reason: str`, `decided_at: datetime` | The single authority the librarian/front door require. `authorised == final_verdict.passed`; an authorised decision with a failing verdict is refused at construction. `reason` = explain-every-decision. |

Every gate decision (PASS-release, FAIL-blocked, budget-exhausted) emits an `AuditRecord`
(`audit_record_contract.py`) via the existing append-only log — what was reviewed (content hash, not the
artifact bytes — T1 hashes-not-PII), the verdict, the outcome (`SUCCESS` / `DENY`).

---

## C. File breakdown — `src/autofirm/output_review/` (all ≤300 lines, one responsibility)

Confirmed **no name collision**: `output_review` does not exist under `src/autofirm/`, and none of the
filenames below collide with existing modules (checked `artifacts/`, `document_store/`, `frontdoor/`,
`audit/`).

| # | File | One-line purpose | Deterministic check it owns |
|---|---|---|---|
| 1 | `review_finding_and_severity_contracts.py` | `CheckSeverity`, `ReviewCheckId`, `ReviewFinding` frozen contracts. | — (shared contract) |
| 2 | `review_verdict_contract.py` | `ReviewVerdict` — derives/validates `passed` from findings; rejects a false pass. | — (shared contract) |
| 3 | `reviewable_artifact_contract.py` | `ReviewableArtifact` handle (path + kind + originating spec + recomputed values). | — (shared contract) |
| 4 | `review_check_protocol.py` | The `ReviewCheck` Protocol every check implements + the check registry type. | — (shared contract) |
| 5 | `accounting_identity_check.py` | Verifies **A = L + E exact to the unit** (`Decimal`) on every period of a financial model. | ACCOUNTING_IDENTITY |
| 6 | `spec_artifact_round_trip_check.py` | Re-reads the file (openpyxl/python-pptx/PDF) and asserts every spec value/row/title is present & correct. | SPEC_ROUND_TRIP |
| 7 | `numeric_recomputation_check.py` | Recomputes formula results and asserts they equal the file's cached values exactly (zero numerical error). | NUMERIC_RECOMPUTE |
| 8 | `file_opens_clean_check.py` | Confirms the artifact is valid OOXML/PDF that opens with no repair prompt (LibreOffice-headless probe, mockable). | FILE_OPENS_CLEAN |
| 9 | `fast_lint_check.py` | FAST/ICAEW lint: orphan-constant detector, row-formula consistency, statement completeness (omission defence). | FAST_LINT |
| 10 | `ibcs_success_rubric_check.py` | IBCS SUCCESS 7-rule + Zelazny message-type→chart-family match on decks. | IBCS_SUCCESS |
| 11 | `visual_integrity_lint_check.py` | Visual-integrity lint: no truncated/misleading axes, no 3D/chartjunk/default-Accent palette. | VISUAL_INTEGRITY |
| 12 | `output_review_gate.py` | `OutputReviewGate` — composes the independent checks, runs each, builds the `ReviewVerdict`. | — (orchestrates 5–11) |
| 13 | `correction_loop_state.py` | `CorrectionSendBack` + `CorrectionLoopState` — bounded send-back/re-review state machine. | — (loop) |
| 14 | `correction_send_back_builder.py` | Turns a failing `ReviewVerdict` into a targeted, machine-actionable `CorrectionSendBack`. | — (loop) |
| 15 | `release_decision_gate.py` | `ReleaseDecision` contract + the authority that authorises/blocks delivery and emits the `AuditRecord`. | — (release gate) |
| 16 | `model_advisory_reviewer.py` | Optional, evidence-gated `ModelReviewer` adapter (add-only findings; kill-switch honoured). | MODEL_ADVISORY (advisory only) |
| 17 | `output_review_errors.py` | `OutputReviewError` fail-closed exception type (mirrors `ArtifactSpecError`). | — (shared) |
| 18 | `__init__.py` | Package marker + curated public re-exports. | — |

If any single file approaches 300 lines during build (likely candidates: #6 round-trip, #12 gate), it is
split by responsibility (e.g. round-trip → one reader-per-kind file) before merge — the limit is hard (§5.7).

---

## D. Test + mutation strategy (CLAUDE.md §3.6 — tests with teeth)

Test files mirror the module and name the behaviour (`test_<module>__<behaviour>.py`); property/fuzz/
security tests carry their marker. Synthetic fixtures only; no real PII (§3.12). One command runs the suite.

### D.1 Adversarial / boundary-exact / property / metamorphic / fuzz cases per check
- **Accounting identity (the §3.11 zero-numerical-error core):** boundary-exact — `A = L + E` with the
  smallest representable mismatch (off by 0.01) **must FAIL**; exact balance **must PASS**; property test
  over random `Decimal` balance sheets where `A := L + E` always passes and any injected delta always
  fails; metamorphic — scaling every figure by a constant preserves the verdict; degenerate (all-zero,
  single-period, negative-equity) handled correctly.
- **Spec round-trip:** a file with one altered/missing/extra value vs its spec **must FAIL** with a finding
  whose locator points at the exact cell/slide; identical spec→build→review **must PASS**; fuzz the spec
  (random valid specs) and assert build→review always round-trips PASS (efficacy).
- **Numeric recompute:** inject a wrong cached value (e.g. a builder that wrote a dead constant instead of a
  formula result) **must FAIL**; correct recompute **must PASS**; determinism — same artifact reviewed N
  times yields byte-identical verdicts.
- **File-opens-clean:** a deliberately corrupted/truncated OOXML zip **must FAIL**; a valid artifact **must
  PASS**; malformed/empty/non-OOXML bytes fuzzed at the boundary.
- **FAST lint:** an embedded orphan constant, an inconsistent row formula, and a missing statement each
  **must raise a finding**; a clean FAST model **must PASS**.
- **IBCS + visual integrity:** a truncated/misleading axis, a 3D chart, a many-slice pie, a message↔chart
  mismatch each **must FAIL**; a compliant deck **must PASS**.
- **Send-back loop:** a defect **must trigger** a `CorrectionSendBack` carrying exactly the blocking
  findings; a corrected re-submission **must PASS**; **re-review is idempotent** (re-reviewing an unchanged
  PASS artifact yields the same PASS, no state drift); the attempt budget is bounded — N consecutive FAILs
  **must** produce an unauthorised `ReleaseDecision`, never an infinite loop.
- **Release gate:** a failing verdict **must** block delivery and emit `AuditRecord(DENY)`; constructing a
  `ReleaseDecision(authorised=True)` over a failing verdict **must raise** (cannot manufacture release);
  the librarian/front door **must refuse** a delivery lacking an authorised decision (fail-closed).
- **Verdict false-pass guard:** constructing a `ReviewVerdict(passed=True)` while holding a BLOCKING
  finding **must raise** — the single most important teeth-test (a green-but-wrong verdict is the failure
  mode the whole lane exists to prevent).

### D.2 Mutation testing (the acceptance signal — §3.6)
`mutmut` over `src/autofirm/output_review/` (Windows-local once loops are bounded, per MEMORY "mutation
gate: iterate LOCALLY"). Targeted mutants and the test that must KILL each: flip the `A = L + E` comparison
operator (`==`→`!=`, `+`→`-`); relax the exact-equality to a tolerance; invert the `passed` derivation;
short-circuit a check so it returns empty findings; drop a check from `checks_run`; flip the release
`authorised` guard; raise the attempt budget to unbounded. **Every survivor gets a harder adversarial test,
then re-run, until ~100% kill on these correctness-/security-critical modules.**

### D.3 Efficacy tests (prove the gate is GOOD at its job — §3.6)
A labelled golden set of **planted real-world errors a cheap model would make** (off-by-one balance,
sign flip on a cash-flow line, a hard-coded value where a formula belongs, a misleading truncated axis, a
dropped statement). Quantify the gate's **error-class kill rate** (target ~100%) and its **false-positive
rate on known-good artifacts** (target 0%), feeding the numbers straight into the `evidence/` showcase
(§3.10) alongside recalc-determinism and per-check pass-rates. This proves the gate *catches real errors*,
not merely that it has no bugs.

---

## E. Non-overlap statement

This lane (**B15 `output_review`**) creates a single new package `src/autofirm/output_review/` and its
test mirror. It **does not touch** any other agent's lane:
- **B7** system-activation / bootstrap — not touched.
- **W1** model gateway (`src/autofirm/modelgateway/`) — not touched (the optional model reviewer *depends
  on* the gateway's public interface but does not modify it; that dependency is read-only and behind the
  `ModelReviewer` adapter).
- **W2** knowledge (`src/autofirm/knowledge/`) — not touched.
- **W3** bootstrap / activation (`src/autofirm/substrate/`, the current `feature/w3-activation-bootstrap`
  HEAD) — not touched.
- **W4** capability registry (`src/autofirm/capabilities/`) — not touched.
- **W5** cost ledger (`src/autofirm/costledger/`) — not touched.

It **reads** (does not modify) existing contracts as integration points: `artifacts/*_spec.py` and the
builders (to obtain specs + outputs), `document_store/` and `frontdoor/` (the delivery targets it gates),
`audit/audit_record_contract.py` (to emit gate-decision audit records). The only *write-side* integration
(Phase 4) inserts the release-gate check at the librarian / front-door delivery seam — coordinated with the
orchestrator so no two agents edit the same artifact; if those files are owned by another lane this turn,
the gate exposes the `ReleaseDecision` contract and the wiring is deferred to an orchestrator-sequenced step.

---

## F. Gated phase plan (fan-out-ready — one file per agent)

Each phase ends in a hard verification gate; commit + push at each gate (§3.13). Within a phase, each
scoped build agent owns **exactly one file** so no two agents edit the same artifact (MEMORY "coordination").

**Phase 0 — Contracts (fan out; files #1–4, #17).**
Build the frozen Pydantic contracts and the `ReviewCheck` Protocol + the error type. Gate: contracts
import clean, false-pass guard on `ReviewVerdict` is tested and rejects a BLOCKING-with-`passed=True`
construction, `ReleaseDecision` rejects authorised-over-failing.

**Phase 1 — Deterministic checks (fan out; files #5–11, one agent each).**
Implement the seven independent deterministic checks. Gate: per-check adversarial + boundary-exact +
property tests green; the accounting-identity check is exact-to-the-unit with zero numerical error.

**Phase 2 — Gate + correction loop + release gate (fan out; files #12–15).**
Compose the gate, the bounded send-back/re-review loop, and the release authority (emitting audit records).
Gate: defect→send-back→re-review→PASS happy path green; budget-exhaustion blocks; idempotent re-review;
release blocks on FAIL and emits `AuditRecord(DENY)`.

**Phase 3 — Optional model reviewer (file #16, evidence-gated).**
Add the add-only model-advisory reviewer behind the gateway interface, kill-switch honoured. Gate:
golden-set bake-off shows it earns its place AND it can never clear a deterministic FAIL; otherwise it
stays disabled by default. (May be deferred — the deterministic core ships without it.)

**Phase 4 — Integrate with delivery path (orchestrator-sequenced).**
Wire the `ReleaseDecision` requirement into the librarian / front-door seam so delivery is refused without
an authorised decision. Gate: end-to-end build→review→(correct)→release→file test green; unauthorised
delivery refused fail-closed. Coordinated to avoid editing another lane's file concurrently.

**Phase 5 — Harden / mutation / evidence.**
Run `mutmut` to ~100% kill on §D.2 targets; fix every survivor with a harder test; produce the §D.3
efficacy numbers and the `evidence/` graphs (error-class kill rate, false-positive rate, recalc determinism)
— built last, visually QA'd before any README embed (MEMORY "evidence diagrams"). Gate: mutation score on
target modules at the bar, coverage ≥90/85, evidence rendered clean.

---

## Risks / decisions for orchestrator ratification
1. **`file_opens_clean` dependency (LibreOffice-headless).** The probe needs LibreOffice (already implied by
   the builders' recalc step). Proposal: a thin, mockable adapter so unit tests never shell out; real probe
   only in an integration-tagged test. Ratify the adapter boundary.
2. **Phase 4 ownership.** The librarian / front-door files may be owned by another lane this turn. Proposal:
   ship the `ReleaseDecision` contract now; defer the write-side wiring to an orchestrator-sequenced step so
   two agents never edit one file. Ratify the sequencing.
3. **Model reviewer scope (Phase 3).** Proposal: deterministic core is the product; the model layer is
   add-only and evidence-gated, defaulting OFF. Ratify that the lane ships PASS/FAIL purely on the
   deterministic core if the bake-off doesn't justify the model layer.

---

## RATIFIED per B16 — constraints applied

The B16 research (`docs/research/B16-output-review-and-verification/SYNTHESIS.md` + `INDEX.md`, which
independently corroborate and *strengthen* B15's single-Panko basis) ratifies this plan and mandates the
following four constraints, now bound into the P0 contract layer (`src/autofirm/output_review/`):

1. **Cite B16, not only B15's single Panko line.** The independent-evaluator mandate, the deterministic
   floor, and the model-layer-as-advisory decision each now rest on ≥3 independent peer-reviewed/primary
   sources (B16 SYNTHESIS §8; Panko 01, Aurigemma&Panko 02, ICAEW 10, Boehm 09, Zheng 04, Verga 05,
   Wu 06, no-free-labels 07, Landis&Koch 08). The contract docstrings cite B16 SYNTHESIS throughout.

2. **Panko-Halverson defect classes (src 03) are a first-class contract field.** Every `ReviewFinding`
   carries a `DefectClass` StrEnum — `MECHANICAL` / `PURE_LOGIC` / `EUREKA` / `OMISSION` — so detection
   can be reported *per taxonomy class* in `evidence/` (SYNTHESIS §3, §5). `EUREKA` is the sole class the
   deterministic floor provably cannot reach and is therefore the *only* justification for the model layer.

3. **Model layer is add-only / cross-family jury / never clears a FAIL.** A blocking finding (the
   false-pass guard) can never be downgraded by any layer; `ReviewVerdict.passed` is *derived* from
   findings and a `passed=True`-over-BLOCKING construction is structurally refused (SYNTHESIS §2.3, §4;
   finding #6). When enabled, the model layer must be a reference-grounded, position-swapped, kill-switchable
   **cross-family jury** (Verga 05; never a single self-preferring judge — Wu 06, no-free-labels 07).

4. **Metrics are κ + defect-detection rate + escape/false-pass rate — NOT pass-rate/coverage.** The
   evidence headline is Cohen's/Fleiss' κ vs a verified gold reviewer (Landis-Koch bands, src 08), per-class
   defect-detection rate (target ~100% on must-block classes), and false-pass/escape rate (target ~0%);
   pass-rate and coverage are explicitly rejected as proof (SYNTHESIS §2.4, §5; CLAUDE.md §3.6).
