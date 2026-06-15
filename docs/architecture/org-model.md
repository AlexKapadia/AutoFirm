# AutoFirm — Dynamic Modular Org Model (Gate-2 v1, ratified)

> The roles-as-data org engine. Synthesizes A1.5 (lifecycle), A1 (orchestrator-worker spine), B1
> (org-design theory), with the A7/A8 least-privilege fence and the A6 audit plane. Roles are
> **data**, the org **re-shapes itself on a heartbeat**, and `main`-equivalent org state stays clean
> (no graveyard — CLAUDE.md §3.8). Every state transition is **fail-closed and audited**.
> **A1.5 is CRO-verified** (Bauer et al. 2007 JAP DOI 10.1037/0021-9010.92.3.707 and Saks/Uggerslev/
> Fassina 2007 JVB DOI 10.1016/j.jvb.2006.12.004, confirmed against accessible primary sources). The
> dynamic-org engine's merge to main is therefore **no longer blocked on A1.5** — it remains gated only
> on experiment **E2** re-proving dynamic-beats-static on AutoFirm's own golden set (per T4).

---

## 1. Shape: hierarchical orchestrator-worker, roles-as-data (A1, A1.5)
- **3-tier spine (A1):** Tier-0 orchestrator (plan/dispatch/gate) → Tier-1 dynamic role-design →
  Tier-2 scoped execution. Centralized because error amplification is 4.4× vs 17.2× for peer mesh
  (Google Research *blog*, Low–Moderate tier, **directional only**; experiment **E1** is the acceptance bar).
- **Strict hierarchy:** every role has exactly one `reports_to` manager (`RoleSpec`, see
  `data-contracts.md` §2). No matrix ambiguity at the platform level.
- **Span control (B1):** roster width follows the **Graicunas curve** `C(n)=n(2^(n−1)+n−1)` and
  Galbraith OIPT — wider spans are allowed only when the information system supports them (Rajan &
  Wulf). The literal "5–6 reports" cap is **rejected**; the curve drives the decision (B1).
- **Roles-as-data:** a role is a `RoleSpec` record, not code. Hiring = writing a record;
  re-scoping = editing it; firing = transitioning it to RETIRED. This is what makes the org modular
  and the lifecycle auditable (A1.5).

---

## 2. The five-stage lifecycle (A1.5 — A1.5 ontology question)
Runs continuously on a heartbeat to maintain org-fit. Each stage is decision-gated and audited.

### 2.1 GAP-DETECT (continuous)
Four complementary gap kinds drive hiring/re-scoping (A1.5 src 01 SWP):
- `SHORTAGE` = required − available headcount
- `SKILL_GAP` = target − current proficiency
- `ROLE_COVERAGE_GAP` = a missing function archetype (e.g. no pricing role for a priced-product client)
- `COORDINATION_LOAD` = an agent's information-processing demand exceeds its capacity (Galbraith
  OIPT — A1/B1). This is the signal that a manager's span is saturating.

### 2.2 ROLE-SPEC (manager writes the charter)
The hiring manager authors a `RoleSpec` (§data-contracts 2) using **JCM five dimensions** (variety,
identity, significance, autonomy, feedback — A1.5 src 03). A **charter-completeness gate** (MPS
collapse test) rejects an under-specified role. The manager also defines the **report spec** the new
role must deliver (see §4). RACI edges assign **exactly one Accountable owner per artifact** —
the single-writer invariant.

### 2.3 SPAWN (dynamic, capped, decision-gated)
Dynamic instantiation under a **saturating spawn cap** (HALO — A1.5): roster size converges to an
equilibrium `P_eq` and never explodes. **SPAWN is gated by RACI decision-rights and fail-closed**
(A1.5) — and, critically, **no agent unilaterally creates a role** (A7). The spawn request goes to
the governance plane, which (a) checks decision-rights, (b) instructs the A8.3 broker to mint a
**fresh per-session SPIFFE identity + short-TTL least-privilege credentials** (this is the T3
spawn-time credential contract), and (c) materializes the role as a `.claude/agents/*.md` substrate
file (A5; see `substrate.md`).

### 2.4 ONBOARD (institutionalized 4-Cs pipeline)
4-Cs pipeline (A1.5 src 08 Saks; institutionalized > individualized tactics):
**Compliance → Clarification → Culture → Connection.** Hard Definition-of-Done gates before the role
goes ACTIVE: `role_clarity_ok ∧ self_efficacy_ok ∧ social_acceptance_ok` (A1.5 src 06 Bauer — the
three empirically-central adjustment indicators).
- **`must_study` gate:** onboarding **blocks until the role acknowledges its required research refs**
  (`RoleSpec.must_study`). A role cannot act on a function it has not studied (A1.5). This is the
  mechanism that ties the org to the `docs/research/` corpus.

### 2.5 RETIRE (graceful, knowledge-preserving — no graveyard)
detect-surplus → **redeploy/re-scope before eliminate** → checkpoint + **harvest memory** into A4
Experience tier → hand off open artifacts → deregister identity (A8.3 revokes creds) → teardown
substrate session. Roles persist **as data records** (status=RETIRED), so history is queryable but
no dead agent lingers (CLAUDE.md §3.8; A6/A6.4 escalate-not-delete). **Retire property test:** zero
orphaned artifacts + a memory-harvest record exists (A1.5).

---

## 3. Single-writer artifact locks (A1.5 RACI + A3)
Every artifact has **exactly one Accountable role** at any time (RACI). Concurrent writes are
impossible by construction:
- Org-level: the RACI `accountable` set across all live `RoleSpec`s must be **disjoint per artifact**
  (audited invariant; build-failing test).
- Substrate-level: enforced by the A5 `--resume` **single-writer lease** on the worktree
  (`substrate.md` §4). Parallel exploration uses `--fork-session` on isolated branches, reconciled by
  the orchestrator (A1 fan-in).

---

## 4. Manager-defined report specs (A1.5)
When a manager hires a report, it defines the **`ReportSpec`** — the typed output contract that role
owes upward (cadence, format, KPIs). This is the org-level analogue of the A2 delegation contract:
the manager specifies WHAT the report must contain (standardized output — Mintzberg/B1), the role
decides HOW. Reports flow up the strict hierarchy; the orchestrator reads aggregated reports, not
transcripts (CLAUDE.md §3.1 context protection).

---

## 5. Org *shape* per client (B1) — distinct from platform org
The **platform** org (above) runs AutoFirm itself. The **client** org is a *designed artifact*: for
each client AutoFirm picks a configuration from Galbraith Star Model + Mintzberg's five
configurations (as a menu) + Burton-Obel multi-contingency fit + Donaldson SARFIT adaptive cycle
(B1), parameterized by the `IndustryProfile` (B12) and industry KPI contracts (SaaS Rule-of-40/NRR,
PSF leverage pyramid, SCOR, marketplace, fintech/healthcare — B1). The client org is **data the
platform produces**, evaluated like any other deliverable.

---

## 6. What's deterministic vs LLM here
- **Deterministic:** gap arithmetic, span curve, spawn cap → P_eq, RACI disjointness check, DoD
  gates, credential minting, retire invariants. These must be exact and are unit/property-tested.
- **LLM:** writing a role's prose charter, judging social-acceptance/clarity, proposing org shape.
  Always validated by the deterministic gates above before any state changes (A7 propose-then-dispose).

---

## 7. Gate to merge this engine to main
1. A1.5 is **CRO-verified** (Bauer 2007 / Saks 2007 DOIs confirmed against accessible primary
   sources) — **satisfied**; this is no longer a blocking prerequisite for merge.
2. Experiment **E2** (dynamic-vs-static org engine, `experiments.md`) re-proves "dynamic roles beat
   fixed roster" **on AutoFirm's own org golden set under A9's Friedman+Nemenyi** — the external
   HALO +14.6% number is **not** an acceptance bar (resolves T4).
3. Single-writer, spawn-saturation, charter-completeness, onboarding-DoD, and retire-property tests
   green with mutation teeth (A9, B14).
