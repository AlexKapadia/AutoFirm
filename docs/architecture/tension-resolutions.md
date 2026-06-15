# AutoFirm — Cross-Branch Tension Resolutions (Gate-2 v1, ratified)

> Resolves each of the seven cross-branch seams T1–T7 from `docs/research/_program/LAYER1-SIGNOFF.md`
> §2. These are the must-resolve-in-L2 obligations the sign-off carried forward. Each ruling cites
> the branches it reconciles, states the binding decision, and names where it is enforced. Rulings
> are **fail-closed and deterministic** wherever a security/correctness boundary is involved.

---

## T1 — Right-to-erasure vs immutable audit log  *(highest priority)*
**Conflict:** A4's **VF** primitive mandates exact external-store deletion / GDPR Art. 17
right-to-erasure; A6.2 mandates an **immutable, append-only audit log** whose data layer refuses
UPDATE/DELETE. Both branches independently flagged the seam.

**RULING (binding):** the two are reconciled by a **data-separation invariant** — *the audit log
stores hashes and lineage of sensitive records, never raw PII or client content.*
- VF erasure (A4) purges the **memory store + PV-derived records** and writes a **new tombstone
  AuditRecord** proving auditable non-recoverability (A4 src 15 SISA exact-delete + reindex).
- The **hash chain is never rewritten or broken** — erasing raw data the chain only *references* by
  hash leaves the tamper-evidence intact (A6).
- Therefore erasure and immutability coexist: you can prove *what happened* forever (hashes/lineage)
  while the *content* is exactly, verifiably gone.

**Enforced in:** `data-contracts.md` §3 (AuditRecord stores hash/lineage; tombstone on erase),
A4 VF lifecycle, A8.2 tenant-scoped purge. **Reconciles:** A4 ∩ A6.

---

## T2 — Hooks fail-open vs audit-via-hooks
**Conflict:** A5 proves Claude Code **hooks are fail-OPEN** and must not be the sole control
boundary; A6 builds part of its append-only audit ledger and green-gate on
SessionStart/PostToolUse/Stop hooks.

**RULING (binding):** **hooks are a logging/convenience + iterate-gate plane only — never the
security boundary and never the sole path an audit record can take.**
- The true enforcement boundary is: permission deny-rules + OS/container sandbox + the **A8 API
  gateway PEP** + SPIFFE-scoped credentials (`substrate.md` §3).
- Every consequential action's audit record is written **through the A8 gateway mediation path**,
  which *can* fail closed (refuse the action if the record cannot be written/sealed — A6 veto).
- A hook may *additionally* observe and log, but a **missed/failed hook can never silently drop an
  audit record**, because the record does not depend on the hook firing.

**Enforced in:** `substrate.md` §3, `overview.md` §2.6, A8.1 gateway mediation. **Reconciles:**
A5 ∩ A6 ∩ A8.

---

## T3 — Dynamic role-spawning vs least-privilege / no-self-granting
**Conflict:** A1.5 SPAWN dynamically creates roles on a heartbeat under a saturating spawn cap; A7
demands "no agent unilaterally creates roles" and "agent never holds the kill credential"; A8.3
demands per-session SPIFFE identity + short-TTL scoped creds + no god-keys.

**RULING (binding):** A1.5 is consistent **by design** but imposes a hard **spawn-time credential
contract**:
- **No agent self-spawns.** A SPAWN is a *request* to the governance plane, gated by RACI
  decision-rights and fail-closed (A1.5 + A7).
- On approval, the **A8.3 secrets broker mints a fresh per-session SPIFFE identity + short-TTL,
  least-privilege, sender-constrained credentials at spawn-cap rate** (no standing/god-keys — A8.3).
- The spawned role **never holds the kill-switch credential** (A7) — that stays out-of-band.
- Retire revokes the identity and credentials (org-model §2.5).

**Enforced in:** `org-model.md` §2.3, `data-contracts.md` §2 (`tool_grants`) + §5 (SpiffeId/
ScopedToolGrant). **Reconciles:** A1.5 ∩ A8 ∩ A7. **Scaling constraint noted:** the broker must mint
at spawn-cap rate — validated as a substrate test.

---

## T4 — "Dynamic beats static" benchmark vs eval rigor
**Conflict:** A1.5's "dynamic roles beat fixed roster → winner merges" leans on HALO's external
**+14.6%** number; A9 forbids any external benchmark as the acceptance bar and requires
Friedman+Nemenyi on AutoFirm's **own** golden set.

**RULING (binding):** the external HALO number is **directional motivation only, never an acceptance
bar.** Before the dynamic-org engine merges to main, **experiment E2** must **re-prove
dynamic-beats-static on AutoFirm's own org golden set under A9's procedure** (pass@k + Friedman
omnibus + Nemenyi post-hoc, effect size + CI, repeated trials, no cross-industry averaging).

**Enforced in:** `experiments.md` E2, `org-model.md` §7 (merge gate). **Reconciles:** A1.5 ∩ A9.

---

## T5 — Blackboard / dynamic-routing scope
**Conflict:** A1 keeps debate/Contract-Net/dynamic roles live and borrows the blackboard's
opportunistic-scheduling idea; A2 **DEFERs blackboard** and **REJECTs LLM-as-orchestrator for
structured flows.** Not a logical contradiction (both land on an orchestrator-worker spine), but the
boundary must be drawn.

**RULING (binding):** draw the **explicit routing boundary**:
- **Deterministic, declared, inspectable DAG is the default** for all *structured* flows — zero-token
  routing, auditable, fail-closed (A2). **LLM-mediated / dynamic routing is forbidden here.**
- **Contract-Net** (announce→bid→award) is permitted for **dynamic allocation where the path is
  unknown at design time** (A2).
- **LLM-mediated routing + bounded debate + dynamic role instantiation** are permitted **only for
  exploratory work** (A1) — and how much of it earns its place is decided by **experiment E1**.
- The **blackboard is not a backbone**; only its single-writer stigmergy (audit log / task list /
  roadmap with stale-state decay) and explainable control-plan ideas are adopted (A1).

**Enforced in:** `overview.md` §2.2, `experiments.md` E1, `data-contracts.md` §1. **Reconciles:**
A1 ∩ A2.

---

## T6 — Pricing margin handoff (B5 → B-fin)
**Conflict:** B-fin's `CLV = m·r/(1+i−r)` needs margin `m`, which should be fed by B5's
price-level/EVC engine output; neither synthesis named the joining contract.

**RULING (binding):** define the **typed margin edge**: B5's EVC/price engine emits gross margin `m`
as a typed value; B-fin's CLV consumes it. No magic constant; `m` is always sourced from the live
pricing engine for that client (CLAUDE.md §3.9 anti-overfit).

**Enforced in:** `data-contracts.md` §6.1 (margin edge: B5 → B-fin). **Reconciles:** B5 ∩ B-fin.

---

## T7 — Fundraising eligibility/dilution dependencies (B6 → B10, B-fin, B1)
**Conflict:** B6's grant/RBF/venture-debt eligibility predicates depend on B10 legal rules it does
not source; its dilution engine needs a valuation input from B-fin; its stage classifier overlaps
B1's growth-cycle logic. Handoffs implied but no contracts named (also QA-REVIEW C1.3).

**RULING (binding):** enumerate the four edges as **typed contracts** before any B6 experiment runs:
1. **B10 → B6:** legal eligibility predicates (grant/RBF/venture-debt lawfulness) — B10 owns
   compliance authority (LAYER1-SIGNOFF convergence; B5/B7/B8 also defer to B10).
2. **B-fin → B6:** valuation (for dilution) **and** leverage ceiling (from the trade-off debt-capacity
   model).
3. **B1 → B6:** round-stage classification from the growth-cycle logic (B6 does not re-implement it).
4. **B6 dilution:** `ownership = investment / post_money_cap` consumes (1)–(3); all inputs typed and
   boundary-validated, none hard-coded (round benchmarks are date-stamped, re-pulled — B6).

**Enforced in:** `data-contracts.md` §6.1 (four edges). **Reconciles:** B6 ∩ B10 ∩ B-fin ∩ B1.

---

## Carried-forward prerequisites (LAYER1-SIGNOFF §5)
Not tensions, but binding gates recorded here for traceability:
- **A1.5 must flip to CRO-PASSED** (Bauer 2007 / Saks 2007 DOIs verified or open-access substituted)
  **before L2.ORG / the dynamic-org engine merges to main** (org-model §7).
- **Confirm A9.3 (mutation/test-adequacy) and A7.* are CRO-PASSED**, since B14 and several L2 items
  depend on them at the gate.
- **L1.B4.2 (customer/CLV cohort-retention) consolidation + B4.3 (ops modeling) cross-reference** to
  be discharged in the L2.B4 toolkit (LAYER1-SIGNOFF Note A).
