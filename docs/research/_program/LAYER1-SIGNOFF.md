# LAYER1-SIGNOFF.md — CRO / Head of Research Cross-Branch Depth Sign-Off

> The Layer-1 (Foundations) depth gate before Layer 2 (applied architecture + branch-per-experiment).
> Implements CLAUDE.md §2 (CRO gate), §3.3 (deep research), §3.4 (evidence-driven choice), and the
> RESEARCH-PROGRAM.md §1 layer-dependency gate. Audited against QUESTION-ONTOLOGY.md (the L1
> questions), DEPTH-RUBRIC.md (the per-question bar), and the 26 branch SYNTHESIS.md files.
>
> **VERDICT: AMBER — Layer 1 is substantively complete; open Layer 2 with the must-resolve-in-L2
> items below carried in as explicit L2 obligations.** No RED gap forces re-research before L2 can
> begin; the open items are reconciliation/proof obligations that Layer 2 is the correct place to
> discharge. One branch (A1.5) is not yet CRO-PASSED and is the single conditional item.

Audited: 2026-06-15. All 26 branch SYNTHESIS.md files read in full (via 4 scoped review agents).

---

## 1. COMPLETENESS — is every L1 ontology question answered?

**Verdict: COMPLETE, with two scope-placement notes and one not-yet-PASSED branch.**

Every Layer-1 ontology branch has a SYNTHESIS.md that claims and substantively answers its
questions. Coverage map:

| Ontology question | Branch | Covered? |
|---|---|---|
| L1.A1.1–.4 (orchestration) | A1 | YES |
| L1.A1.5 (auto-hiring/role lifecycle) | A1.5 | YES — **but seeded for QA, NOT yet CRO-PASSED** |
| L1.A2.1–.3 (comms/flow) | A2 | YES |
| L1.A3.1–.3 (autonomy/handoff) | A3 | YES |
| L1.A4.1–.4 (memory) | A4 | YES (deepest branch) |
| L1.A5.1–.3 (CLI substrate) | A5 | YES (narrow source diversity — first-party Anthropic spec, appropriate) |
| L1.A6.1–.3 (governance/audit) | A6 | YES |
| L1.A6.4 (workspace/data boundary) | A6.4 | YES |
| L1.A7.1–.3 (safety/control) | A7 | YES |
| L1.A8.1–.3 (integration/data layer) | A8 | YES |
| L1.A9.1–.3 (eval/mutation) | A9 | YES (68 lines, dense not thin) |
| L1.B1.1–.3 (org models) | B1 | YES (rows 6/7/8 org-KPIs by principle only) |
| L1.B2.1–.3 (function automation) | B2 | YES |
| L1.B3.1–.2 (entrepreneurship) | B3 | YES |
| L1.B4.1, .4 (+B4.2 spillover) | B-finance-accounting | **PARTIAL — see note A** |
| L1.B5.1 (pricing) | B5 | YES (deepest business branch, 15 sources) |
| L1.B6.1 (fundraising) | B6 | YES (theory deep; instrument-economics under-sourced, self-gated) |
| L1.B7.1 (marketing) | B7 | YES |
| L1.B8.1 (sales) | B8 | YES |
| L1.B9.1 (support/success) | B9 | YES |
| L1.B10.1 (legal/compliance) | B10 | YES |
| L1.B11.1 (operations) | B11 | YES |
| L1.B12.1–.2 (generalization) | B12 | YES (panel proof DEFERRED to L2 — see note B) |
| L1.B13.1–.5 (product/design) | B13 | YES (all 5 sub-questions) |
| L1.B14.1–.3 (software delivery) | B14 | YES (58 lines, dense not thin) |
| L1.B15.1–.3 (artifacts) | B15 | YES |

**Note A — L1.B4 (financial/customer/operational modeling).** The `B-finance-accounting` folder
covers **B4.1** (financial modeling) and **B4.4** (public-data/PII boundary) fully, and **B4.2**
(customer/CLV) as spillover. **L1.B4.3 (operational modeling — capacity/throughput/queueing)** is
NOT in this folder; it is distributed to B1-R4 (per-archetype operational KPI contracts), B11
(Lean/SCOR/Little's-Law ops foundations), and B12 (NAICS ops key). So B4.3 IS answered cross-branch,
but the BFIN synthesis does not state this hand-off. **Under-answered, not unanswered** — fix is a
one-line scope cross-reference in BFIN, deferrable to L2.B4. **(L1.B4.2 customer modeling — CAC/LTV,
retention/cohort, segmentation — is the thinnest sub-area: present as BFIN spillover + referenced
by B5/B9, but lacks a dedicated cohort/retention synthesis. Flag for L2.B4 to consolidate.)**

**Note B — the only conditional COMPLETENESS item: A1.5 is not yet CRO-PASSED.** Its synthesis line
1 reads "seeded for QA (not yet CRO-PASSED)" and §4 honestly flags two paywalled DOIs (Bauer 2007,
Saks 2007) whose exact correlation values were deliberately NOT fabricated and are queued for QA
spot-fetch. This is the correct, honest behaviour per DEPTH-RUBRIC §3, but it means L2.ORG (which
depends on L1.A1.5) cannot be marked dependency-satisfied until QA verifies those two sources. **This
is the single item that keeps the verdict AMBER rather than GREEN.**

No L1 question is wholly unanswered. No RED completeness gap.

---

## 2. CONSISTENCY — cross-branch contradictions/tensions for L2 to resolve

No hard contradiction was found that invalidates a branch. The following are **unreconciled seams**
that multiple branches independently flag and that Layer 2 must explicitly resolve (most are
integration constraints, not logical conflicts):

**T1 (HIGHEST PRIORITY) — Right-to-erasure vs immutable audit log.** A4's VF primitive mandates
**exact external-store deletion / GDPR right-to-erasure**; A6.2 mandates an **immutable, append-only
audit log whose data layer refuses UPDATE/DELETE**. Both branches independently flag the seam.
L2 ruling needed: *the audit log stores hashes/lineage of sensitive records, never raw PII; erasure
purges the memory store + PV-derived records but never breaks the tamper-evident chain.*

**T2 — Hooks fail-open vs audit-via-hooks.** A5 proves Claude Code **hooks are fail-OPEN and must
NOT be the sole control boundary**; A6 builds part of its append-only audit ledger and green-gate on
SessionStart/PostToolUse/Stop hooks. L2 ruling: *hooks are a logging/convenience plane only;
permission-deny-rules + OS sandbox are the true enforcement boundary; a missed hook must not be able
to silently drop an audit record (reconcile with A8 gateway-level mediation).*

**T3 — Dynamic role-spawning (A1.5) vs least-privilege / no-self-granting (A7, A8.3).** A1.5 SPAWN
dynamically creates roles on a heartbeat under a saturating spawn cap. A7 demands "no agent
unilaterally creates roles" and "agent never holds the kill credential"; A8.3 demands per-session
SPIFFE identity + short-TTL scoped creds + no god-keys. A1.5 *designs for* this (SPAWN gated by
RACI/RAPID decision-rights; ONBOARD issues scoped least-privilege creds) — so it is consistent **by
design**, but imposes a hard scaling constraint: the A8.3 credential broker must mint fresh scoped
credentials per spawned role at spawn-cap rate. L2.ORG + L2.A8 must wire this contract.

**T4 — "Dynamic beats static" benchmark (A1.5) vs eval rigor (A9).** A1.5's "dynamic roles beat
fixed roster → winner merges" leans on HALO's external **+14.6%** number; A9 forbids any external
benchmark as the acceptance bar and requires Friedman+Nemenyi on AutoFirm's own golden set. L2:
*re-prove dynamic-beats-static on AutoFirm's own org golden set under A9's statistical procedure
before it merges to main* (a branch-per-experiment item — see §Experiments).

**T5 — Blackboard / dynamic-routing scope (A1 vs A2).** A1 adopts the blackboard's
opportunistic-scheduling/explainable-control-plan idea and keeps debate/Contract-Net/dynamic roles
live; A2 **DEFERs blackboard** and **REJECTs LLM-as-orchestrator for structured flows**. Not a
contradiction (both land on an orchestrator-worker spine independently), but L2.A1 must draw the
**explicit boundary: where dynamic/LLM-mediated routing is permitted (exploratory) vs forbidden
(structured/deterministic-DAG flows).**

**T6 — Pricing margin handoff (B5 → BFIN).** BFIN's `CLV = m·r/(1+i−r)` needs margin `m`, which
should be fed by B5's price-level/EVC engine output; neither synthesis names the contract joining
price → CLV margin. L2.B4/L2.B5 must define the shared typed contract.

**T7 — Fundraising eligibility/dilution dependencies (B6 → B10, BFIN, B1).** B6's grant/RBF/
venture-debt eligibility predicates depend on B10 legal rules it does not itself source; its
dilution engine needs a valuation input from BFIN; its stage classifier overlaps B1's growth-cycle
logic. Handoffs are implied but no shared contract is named. L2 must enumerate these edges (this is
exactly QA-REVIEW-001 fix C1.3 — per-function L2 dependency edges).

**Strong convergences (no action, but they de-risk L2):** orchestrator-worker spine (A1 + A2
independently); data-layer tenant isolation via RLS/per-tenant container (A4 PS + A5 + A6.4 + A8.2
all agree); fail-closed governance VETO of A6/A7 over A3 resume + A4 writes; no-graveyard /
escalate-not-delete (A6 + A6.4 + A1.5 retire); mutation-score-as-acceptance-signal shared by A9
(platform) and B14 (client code); compliance authority centralized in B10 with B7/B8 deferring.

---

## 3. DEPTH — does the corpus meet the graduate-level bar?

**Verdict: YES overall — graduate/institution-grade, with self-disclosed open verification items.**

- **Source quality is genuinely primary/peer-reviewed**, not blog folklore. Representative High-tier
  anchors found across branches: Hayes-Roth 1985, Smith 1980, Du et al. ICML 2024 (A1); FIPA-ACL
  IEEE std, MAST NeurIPS 2025 (A2); Garcia-Molina/Salem 1987, Elnozahy 2002, Langosco ICML 2022
  (A3); CoALA TMLR, DPR EMNLP, SISA/Cao-Yang IEEE S&P, GDPR primary law (A4); Saltzer-Schroeder 1975,
  NIST AI 600-1, AgentDojo (A7); NIST SP 800-204/800-207, IETF RFCs, SPIFFE (A8); Dror ACL18,
  Demšar JMLR06, DeMillo IEEE78, Jia-Harman TSE11 (A9); Galbraith/Mintzberg/Burton-Obel/Graicunas
  (B1); Frey-Osborne, Eloundou, Autor-Levy-Murnane (B2); Camuffo 759-firm RCT (B3); Damodaran,
  IAS 7/ASC 230, SEC EDGAR, Van Buren/hiQ caselaw (BFIN); Calvano AER 2020, Miller JMR 2011 (B5);
  Anderl IJRM, Gordon Marketing Science, Ehrenberg-Bass (B7); Weitz/Sujan JM (B8); Keiningham 2007
  + Anderson-Sullivan N=22,300 (B9); EU AI Act 2024/1689, UCC, Thaler, LegalBench NeurIPS (B10);
  Little 1961 theorem, Heskett, Shostack (B11); W3C WCAG / Google CWV normative (B13); mutation-
  coupling on 357 real faults (B14); FAST/ICAEW/ISO-29500, Tufte, Minto, Panko (B15).
- **Alternative space surveyed in every branch** with explicit ADOPT/REJECT/DEFER + rationale
  (DEPTH-RUBRIC §4) — no single-approach tunnel vision found.
- **Anti-overfit discipline is consistent**: every business branch parameterizes by the B12 panel
  and explicitly rejects hard-coded constants (60:40, 80/20, Delaware default, vendor benchmarks,
  charm-pricing) — strong generality posture (CLAUDE.md §3.9).
- **Honest evidence ledgers** appear throughout (deferred/paywalled numbers flagged, not fabricated).

**THIN-branch scrutiny (line count is NOT depth):**
- A9 (68 ln), B2 (79 ln), B9 (77 ln), B14 (58 ln) were all scrutinized — **all PASS on substance**;
  brevity is tight tabular compression. B14 actually carries the most sources of any business branch
  (12); A9 is 6/9 High-tier with exact formulae.
- **The one genuinely under-sourced layer: B6 fundraising instrument-economics** (venture-debt/RBF
  rests on a Low/vendor source; Carta medians are single-dataset/Moderate). B6 *itself gates* this —
  it forbids quantitative RBF/venture-debt claims until a peer-reviewed source + second dataset land.
  This is correct fail-closed behaviour; it is an L2.B6 prerequisite, not an L1 RED.
- **L1.B4.2 customer modeling** is the thinnest sub-topic by coverage (spillover only) — consolidate
  in L2.B4.

No branch falls below the graduate bar. No RED depth gap.

---

## 4. ARCHITECTURE-READINESS — concrete enough to drive L2?

**Verdict: YES — strongly architecture-ready.** Syntheses are not literature dumps; they emit
cited, build-relevant ADOPT/REJECT decisions and, in many cases, named components, typed contracts,
exact formulae, and golden-metric hooks ready for branch-per-experiment:

- A1: routing predicate (multi-agent IFF breadth-first ∧ low-dependency ∧ >1 context ∧ gain >~15×),
  fan-out cap ~3–4/cluster, 14-MASFT adversarial test matrix → directly seeds L2.A1 + L2.A9.
- A2/A5: typed stage contracts, FIPA-ACL envelope, `claude -p --bare --output-format json` prod
  invocation, `--resume` single-writer lease → seeds L2.A2/L2.A5 execution model.
- A4: 5 governance primitives (WA/PV/PS/RB/VF) + tiered CoALA store → seeds L2.A4.
- A6/A6.4/A8: PROV-DM+FHIR audit split, history-tree/RFC-6962 Merkle log, RLS (ENABLE+FORCE) +
  per-tenant isolation, SPIFFE + short-TTL creds → seeds L2.A6/L2.A8.
- A7: fail-closed default-deny + CaMeL/Dual-LLM + out-of-band kill-switch → seeds L2.A7.
- A9: pass@k/pass^k estimators, McNemar/Wilcoxon/bootstrap decision tree, mutation-score gate →
  seeds L2.A9 harness directly.
- Business: exact formulae ready as code (ODI `I+max(I−S,0)`; EVC `Ref+Diff−Switching`;
  Lerner `1/|e|`; CLV `m·r/(1+i−r)`; Graicunas span; Little's Law; ownership `inv/post_money`) +
  `IndustryProfile`/`PlaybookSpine`/variation-point contracts (B12) → seed L2.B*.

Readiness is high. The only thing standing between these and L2 design work is discharging the §2
seams as explicit L2 decisions (which is what L2 is for).

---

## 5. Recommended Layer-2 design questions / experiments

**Must-resolve-in-L2 decisions (carry the §2 seams in as obligations):**
1. **Erasure-vs-audit ruling (T1)** — audit log stores hashes/lineage only; erasure purges memory +
   derived records, never the tamper chain. (L2.A4 ∩ L2.A6.)
2. **Hook trust boundary (T2)** — hooks = logging plane; permission-rules+sandbox+gateway = the
   boundary. (L2.A5 ∩ L2.A6 ∩ L2.A8.)
3. **Spawn-time credential contract (T3)** — A8.3 broker mints per-spawn SPIFFE+short-TTL creds at
   spawn-cap rate; RACI gates SPAWN. (L2.ORG ∩ L2.A8 ∩ L2.A7.)
4. **Dynamic-routing boundary (T5)** — declare where LLM-mediated routing is permitted vs
   deterministic-DAG-only. (L2.A1 ∩ L2.A2.)
5. **Per-function dependency edges (T6, T7 + QA-REVIEW C1.3)** — enumerate B5→B4(margin),
   B6→{B10,BFIN,B1}, B8←B7 as typed contracts before any L2.B* experiment runs.
6. **Consolidate L1.B4.2 + cross-reference B4.3** in the L2.B4 toolkit (cohort/retention + ops
   modeling hand-off explicit).

**Top recommended branch-per-experiment (`experiment/*`) studies — each with a pre-agreed golden
set + metric, winner-merges-loser-deleted (CLAUDE.md §3.4/§4.4):**
- **E1 — Orchestration topology bake-off (L2.A1):** orchestrator-worker spine vs +debate-subroutine
  vs +dynamic-role-instantiation, on a task golden set; metric = task success × cost, error-
  amplification, MASFT-failure incidence. Resolves how much dynamism earns its place.
- **E2 — Dynamic-vs-static org engine (L2.ORG) — gates T4:** re-prove "dynamic roles beat fixed
  roster" on AutoFirm's OWN org golden set under A9's Friedman+Nemenyi; do not import HALO's +14.6%.
- **E3 — Memory architecture (L2.A4):** A-Mem linked-notes vs MemGPT OS-tiering vs hybrid, on a
  long-horizon recall+poisoning-resistance golden set; metric = recall@k, AgentPoison ASR, exact-
  deletion verification.
- **E4 — Injection-defense pattern (L2.A7/A8):** Plan-Then-Execute vs Dual-LLM vs CaMeL interpreter
  on AgentDojo-style adversarial suite; metric = utility retained vs attack-blocked (quantify the
  CaMeL utility cost, ~77% vs 84% undefended).
- **E5 — Tamper-evident log mechanism (L2.A6):** plain hash-chain vs history-tree vs RFC-6962
  Merkle/STH; metric = append latency, proof size, tamper-detection completeness at fail-closed.
- **E6 — B12 panel generalization proof (L2.B12) — discharges Note B:** run `derive_playbook()`
  across all 8 fixed panel rows; metric = every row yields a non-empty, lawful, domain-expert-
  sensible variant (overfit to any row = FAIL).
- **E7 — Artifact-generation engine (L2.B15):** XlsxWriter+LibreOffice-recalc vs alternatives for
  live-formula models; deck/document router; metric = generator/evaluator error rate vs Panko 86%.
- **E8 — Live-E2E design DoD (L2.B13):** Playwright vs Cypress golden-set bake-off + a11y scanner
  choice; metric = every interactive element exercised, WCAG 2.2 AA pass, Core Web Vitals budget.

**Prerequisite before the dependent L2 work starts:**
- **CRO action:** QA must spot-fetch A1.5's two paywalled DOIs (Bauer 2007, Saks 2007) and flip
  L1.A1.5 to PASSED, OR A1.5 substitutes open-access corroboration — **L2.ORG is blocked until then.**
- **CRO action:** confirm L1.A9.3 (mutation/test-adequacy) and L1.A7.* are CRO-PASSED, since B14 and
  several L2 items explicitly depend on them at the gate.

---

## Sign-off

**AMBER — Layer 1 is complete enough to OPEN Layer 2**, with the §5 must-resolve items carried in as
explicit L2 obligations and the two CRO prerequisite actions (A1.5 DOI verification; confirm A9.3/A7
PASSED) discharged before the branches that depend on them begin. No RED gap requires re-research
first. The corpus is graduate-grade, the alternative space is surveyed everywhere, generality
discipline is consistent, and the syntheses are concrete enough to drive L2 design and
branch-per-experiment selection.
