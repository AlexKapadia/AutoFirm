# ARCH-QA-001 — Independent Architecture Review (Gate-2 v1)

> **Role:** Independent CTO peer-review / QA. I did **not** author the architecture under review.
> **Scope:** `overview.md`, `data-contracts.md`, `org-model.md`, `substrate.md`,
> `tension-resolutions.md`, `experiments.md`, audited against `LAYER1-SIGNOFF.md`, four spot-checked
> branch SYNTHESIS files (A1, A1.5, A6, B5), and CLAUDE.md §2/§3.2/§3.5/§5.6/§5.7.
> **Date:** 2026-06-15. **Posture:** demanding skeptic with veto power.

## VERDICT: **AMBER** (one-fix-from-GREEN)

The architecture is genuinely strong: research-grounded, internally consistent, security-by-default,
and ready to drive the E1–E8 experiments. It is **AMBER, not GREEN, for exactly one reason**: a
**stale blocking caveat** asserting A1.5 is "not yet CRO-PASSED" survives in three places, while the
A1.5 SYNTHESIS it cites now marks both DOIs **VERIFIED** and the branch **QA-verified**. This is a
documentation-coherence defect, not a substantive gap. Remove the stale caveat → GREEN.

---

## Per-criterion grades

### 1. GROUNDING — **GREEN**
Spot-checked four major decisions against their cited branch SYNTHESIS; all faithfully represented,
no misrepresentation found:
- **A1** → orchestrator-worker 3-tier spine, error amplification **4.4× (centralized) vs 17.2×
  (mesh)**, fan-out saturation **~3–4/cluster**, the multi-agent routing predicate (breadth-first ∧
  low-dependency ∧ >1 context ∧ gain >~15× cost). All verbatim-consistent with A1 SYNTHESIS L1.A1.1–.4.
- **A1.5** → 5-stage lifecycle (gap-detect→role-spec→spawn→onboard→retire), JCM five dimensions,
  RACI single-Accountable, HALO +14.6% as **directional-only** (correctly demoted). Faithful.
- **A6** → PROV-DM + FHIR two-record split, history-tree/RFC-6962 Merkle log + STH at gates,
  data-layer refuses UPDATE/DELETE, graduated containment (warn→throttle→isolate→kill). Faithful.
- **B5** → `EVC = Ref + Diff − Switching`, `Lerner (P−MC)/P = 1/|e|`. Exact.
- **One honest caveat (not a defect):** overview §2.1 / org-model §1 cite "4.4× vs 17.2× (Google
  Research)". The A1 SYNTHESIS sources this to a **Google Research *blog*** locator (Low–Moderate
  tier), which A1 itself flags and re-measures on AutoFirm's own golden set in E1. The architecture
  inherits a directional number correctly (E1 is the acceptance bar, not the blog) but the prose
  "Google Research" reads slightly more authoritative than "Google Research blog". Minor wording.

### 2. TENSIONS (T1–T7) — **GREEN**
All seven are genuinely resolved with a binding ruling, the reconciled branches named, and an
enforcement site cited — not hand-waved. Cross-doc consistency holds:
- **T1** (erasure vs immutable log): data-separation invariant (hashes/lineage only, tombstone on
  erase, chain never rewritten). Consistent across tension-resolutions §T1, data-contracts §3 + erasure
  rule, overview §2.4. Sound.
- **T2** (hooks fail-open): hooks = logging/iterate-gate plane only; true boundary = sandbox +
  permission-deny + A8 gateway PEP + SPIFFE; audit record routed through the gateway (can fail closed)
  so a dropped hook cannot lose a record. Consistent across substrate §3, overview §2.6, tension §T2.
  This is the single most important security ruling and it is correct.
- **T3** (spawn vs least-privilege): no self-spawn; SPAWN is a RACI-gated governance request; broker
  mints per-session SPIFFE + short-TTL sender-constrained creds; never holds kill-switch. Consistent
  across org-model §2.3, data-contracts §2/§5, tension §T3.
- **T4** (HALO benchmark vs eval rigor): external +14.6% is directional-only; **E2 re-proves on
  AutoFirm's own golden set under Friedman+Nemenyi** before merge. Consistent (org-model §7, E2, §T4).
- **T5** (dynamic-routing boundary): deterministic DAG default for structured flows; Contract-Net for
  unknown-at-design-time allocation; LLM-mediated routing confined to exploratory work, sized by E1.
  Consistent (overview §2.2, E1, data-contracts §1, §T5).
- **T6** (margin edge B5→B-fin) and **T7** (B6→{B10,B-fin,B1}) enumerated as **typed boundary-validated
  edges** in data-contracts §6.1; closes LAYER1-SIGNOFF §5.5 / QA-REVIEW C1.3. Consistent.

### 3. COMPLETENESS — **GREEN**
Every required plane is covered: org (A1/A1.5/B1), communication/flow (A2/A3), memory/learning (A4),
governance/audit (A6/A6.4), safety/control (A7), integration/data (A8/A6.4), substrate (A5), **and**
the business layer — finance (B-fin formulae), the function set (B1–B11 driven by the B12
PlaybookSpine), and product/design (B13/B15). The 26-branch coverage map in LAYER1-SIGNOFF §1 maps
cleanly onto the seven planes + business layer. Eval/evidence spine (A9/B14) present.
- **Minor gaps (deferrable, already self-flagged):** (a) **B4.2 customer/CLV cohort-retention** and
  **B4.3 ops modeling** consolidation is carried as an L2.B4 obligation (tension §carried-forward) but
  has **no E-experiment** of its own — acceptable, since it's a synthesis-consolidation task, not a
  method bake-off. (b) **B6 fundraising instrument-economics** (venture-debt/RBF) remains under-sourced;
  B6 self-gates quantitative claims until a peer-reviewed source lands. Correctly fail-closed; flag it
  forward as an L2.B6 prerequisite so it is not forgotten.

### 4. SECURITY / DETERMINISM — **GREEN**
- **Fail-closed** is the stated default everywhere: missing required envelope field → refuse
  (data-contracts §1); unlawful playbook variant → refuse (overview §2.7); RLS schema-audit **fails the
  build** if any tenant table lacks ENABLE+FORCE+USING+WITH CHECK (data-contracts §5).
- **Least-privilege:** per-session SPIFFE + short-TTL sender-constrained creds, no standing god-keys
  (A8.3, data-contracts §5, T3).
- **Deterministic-core / optional-ML split** is explicit and the invariant is stated correctly: "an
  LLM never makes a hard decision" (overview §1) — honors §3.5. All business formulae sit in the
  deterministic core, exact-to-the-unit, mutation-tested (data-contracts §6).
- **Tenant isolation in the data layer, not by convention** (§5.6 tenancy note) — satisfied via RLS
  with a non-owner, non-BYPASSRLS role.
- **Typed contracts are sound:** envelope, RoleSpec, AuditRecord, Checkpoint, identity/credential, and
  business formulae are all typed, with REQUIRED/OPTIONAL marked and fail-closed on missing required.
- *Nit:* contracts are pseudo-typed (language-neutral shapes), which is correct at architecture-time;
  the build must pick an encoding (data-contracts header acknowledges this). Not a defect.

### 5. STRUCTURE — **GREEN**
- **Self-documenting names** throughout (`tension-resolutions.md`, `data-contracts.md`,
  `org-model.md`, `substrate.md`) — a newcomer can navigate without opening files. No junk-drawer names.
- **§5.7 300-line limit honored** on every file: overview 168, data-contracts 185, org-model 115,
  substrate 108, tension-resolutions 140, experiments 112, README 16. None close to the cap.
- One responsibility per file; companion-file cross-references are explicit and bidirectional.

### 6. EXPERIMENTS (E1–E8) — **GREEN**
All eight are well-formed: each has a clear **hypothesis**, **named competing approaches**, a
**pre-agreed golden set + metric** stated up front, and an `experiment/<branch>` name. The A9
statistical procedure (pass@k / pass^k, McNemar→Wilcoxon→bootstrap for pairs, Friedman+Nemenyi for ≥3,
effect size + CI, no cross-industry averaging) and **mutation-score-as-acceptance** are applied
uniformly. Winner-merges / losers-deleted (no graveyard) is binding in the run discipline.
- E1 (topology), E2 (dynamic-vs-static org, gates T4), E3 (memory), E4 (injection-defense, AgentDojo),
  E5 (tamper-log), E6 (B12 panel generalization — overfit-to-any-row = FAIL), E7 (artifact engine vs
  Panko 86%), E8 (live-E2E design DoD). Each maps to its L2 branch and the LAYER1-SIGNOFF §5 list.
- *Minor:* E1 lists three candidates and E2/E3/E4 list 2–3; all use the correct statistical test for
  their arity. E6 is a generalization proof rather than a bake-off (single engine × 8 rows) — correctly
  framed as a property/fuzz proof, not an A/B. Well-formed.

---

## Prioritized concrete fixes

**P0 — BLOCKING for GREEN (stale caveat; A1.5 is in fact VERIFIED):**
1. **`org-model.md` lines 7–8** — delete the blockquote "Blocking prerequisite … A1.5 is not yet
   CRO-PASSED … two paywalled DOIs (Bauer 2007, Saks 2007) must be spot-fetched/substituted before
   this engine merges to main." The A1.5 SYNTHESIS (lines 6–7, 117–133) now reads **"QA-verified
   (paywalled-source blocker closed; Bauer 2007 + Saks 2007 structure confirmed)"** and marks both DOIs
   **VERIFIED**.
2. **`org-model.md` line 110** — strike or rewrite gate item 1 ("A1.5 flipped to CRO-PASSED … —
   **blocking**"); A1.5 is already CRO-PASSED, so this is satisfied, not pending.
3. **`tension-resolutions.md` lines 135–136** — strike the carried-forward "A1.5 must flip to
   CRO-PASSED (Bauer 2007 / Saks 2007 DOIs verified …) before L2.ORG merges" — discharged.
   *(Keep line 137's A9.3/A7 confirmation item unless those are independently confirmed PASSED.)*

**P1 — coherence / accuracy nits (do before merge, non-blocking):**
4. **overview.md §2.1 / org-model §1** — change "(Google Research)" → "(Google Research blog,
   directional; E1 is the acceptance bar)" to match the A1 SYNTHESIS source-tier honesty and avoid
   over-stating the locator.
5. **B6 instrument-economics** — add a one-line forward-flag in experiments.md or tension-resolutions
   §carried-forward that B6 quantitative venture-debt/RBF claims remain fail-closed-gated on a
   peer-reviewed source landing in L2.B6 (so the self-gate is not lost between layers).

**P2 — optional polish:**
6. Consider a one-line note in experiments.md that **B4.2/B4.3 consolidation** is an L2.B4 synthesis
   task with **no E-experiment** (explicitly, so its absence from E1–E8 is not read as an omission).

---

## Bottom line
The Gate-2 v1 architecture is institution-grade, faithfully research-grounded, internally consistent
across all six docs, fail-closed and deterministic-by-default, and structurally clean. The only thing
standing between it and a GREEN sign-off is removing the **stale A1.5 "not-yet-CRO-PASSED" caveat**
(three locations) that the A1.5 SYNTHESIS already contradicts. Apply P0; optionally P1/P2.

**Ready to run the E1–E8 experiments: YES.** (E1–E8 are well-formed and may run now; only the **merge
of the dynamic-org engine to main** was ever gated on the A1.5 item, which is itself now discharged
once the stale caveat is removed.)

---

## Fixes applied (2026-06-15)
- **P0 (1–3) — stale A1.5 caveat removed → architecture now GREEN.** `org-model.md` blockquote (was
  L7–8) and §7 gate item 1, and `tension-resolutions.md` carried-forward (was L135–136) now state
  **A1.5 is CRO-verified** (Bauer et al. 2007 JAP DOI 10.1037/0021-9010.92.3.707; Saks/Uggerslev/
  Fassina 2007 JVB DOI 10.1016/j.jvb.2006.12.004). The dynamic-org merge is no longer blocked on
  A1.5 — it is gated only on **E2** (per T4).
- **P1 (4) — "Google Research" wording.** `overview.md` §2.1 and `org-model.md` §1 now read "Google
  Research *blog*, Low–Moderate tier, directional only; E1 is the acceptance bar".
- **P1 (5) — B6 forward-flag.** `tension-resolutions.md` carried-forward now flags venture-debt/RBF
  instrument-economics as under-sourced and self-gated, carried into Layer-2 B6 as a fail-closed
  prerequisite.
- **P2 (6) — B4.2/B4.3 note.** `experiments.md` Run-discipline note records that B4.2/B4.3 (and B6)
  consolidation is an L2.B4 synthesis task with no E-experiment by design — absence from E1–E8 is
  intentional, not an omission.
