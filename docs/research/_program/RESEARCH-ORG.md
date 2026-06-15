# AutoFirm Research Organization (RESEARCH-ORG.md)

> The dynamic, scalable agent org that **conducts** AutoFirm's research. This is the
> org that produces `docs/research/`. It is itself a worked example of the dynamic,
> audited, scalable multi-team org AutoFirm must run for real companies — built by the
> same roles-as-data primitives (§"Dynamic role lifecycle" below).
>
> **Grounding.** Structure follows contingency theory (fit between task uncertainty and
> structure) and Galbraith's Star Model (Strategy/Structure/Process/Rewards/People must
> fit), with Mintzberg coordination mechanisms (direct supervision, standardization of
> work/outputs/skills, mutual adjustment). Sources cited in `RESEARCH-PROGRAM.md` §Sources.

---

## 1. Design principles (why this shape)

1. **Roles-as-data, dynamic.** Every role is a typed record (id, mandate, parent, tools,
   context-scope, success-criteria, status, **`must_study`**) — not hard-coded. Managers
   spawn/retire/re-scope reports at runtime. Mirrors the platform requirement: hire/fire/
   re-scope, strict audited hierarchy, every manager defines its reports' roles.
   **Mandatory onboarding contract — `must_study`:** every role record carries a
   `must_study: [CLAUDE.md, DEPTH-RUBRIC.md, <assigned ontology branch>]` field. It is
   **verified at SPAWN and is a fail-closed gate: no role activates (status → active) until
   its `must_study` set is present and acknowledged.** A spawn with a missing/empty
   `must_study` is **refused**, not silently fixed. This guarantees every agent has read and
   conforms to the behavioural contract (CLAUDE.md), the quality bar (DEPTH-RUBRIC.md), and
   the slice of the ontology it owns before it touches any artifact.
2. **Strict, audited hierarchy with bounded span of control.** Contingency theory: high task
   uncertainty (novel research) → narrower spans, more lateral coordination. **Hard cap: a
   manager directly supervises ≤ 7 reports** (Mintzberg/classic span limits); beyond that,
   insert a sub-lead layer. Every spawn/retire/re-scope is an append-only audit event.
3. **Separation of duties (fail-closed governance).** The team that *produces* research never
   *signs off* its own depth/faithfulness — an **independent Peer-Review/QA function** holds
   the gate and is empowered to FAIL and return work. (TRiSM/verifiability-first agents:
   oversight must be a different principal than the actor.)
4. **Protect orchestrator context.** Leads receive **compact structured results**, never
   transcripts. Information-processing view (Galbraith): reduce coordination load via
   self-contained domain teams + standardized interfaces (`SUMMARY.md` / `BEST-PARTS.md`
   schemas), not constant cross-talk.
5. **Standardization of outputs as the primary coordination mechanism.** Because researchers
   are expert and autonomous, we coordinate by **standardizing outputs** (the artifact
   schemas + DEPTH-RUBRIC) rather than micromanaging method — Mintzberg's "standardization of
   outputs/skills" fits high-expertise work.
6. **Single-writer artifact lock (hard, fail-closed).** Every writable artifact — each
   `docs/research/<branch>/<source>/` folder, each `SUMMARY.md`/`BEST-PARTS.md`, each branch
   `INDEX.md`, each `_program/` spec file — has **at most one owning role at any instant**.
   Ownership is an **exclusive assignment lock** acquired *before* work begins, not
   reconciled after the fact. **No two agents ever own or write the same artifact
   concurrently.** A SPAWN/RE-SCOPE/assignment whose mandate would write an already-locked
   artifact is **REFUSED** at the precondition check (§5) — never granted and merged later.
   This is the strongest of the fail-closed invariants and supersedes the older
   detect-and-merge behaviour for write conflicts (Org-Mgmt de-dup, §3.6, now operates
   *only* on read/scout overlap and never as the primary guard against double-writes).

---

## 2. Org chart (functions, not fixed headcount)

```
                         Head of Research (CRO)  ── owns the bar; only role that says "research done"
                                  │
        ┌──────────────────┬──────┴───────────┬───────────────────────┐
        │                  │                  │                       │
 Program Architect(s)   Domain Research    Peer-Review / QA        Org-Management /
 (designs the program,  Leads (N, one per   Function (INDEPENDENT  Efficiency Function
  ontology, waves)      live domain)        — audits & FAILS work)  (keeps org efficient)
        │                  │                                          
        │          ┌───────┼────────┐                                 
        │      Lead A    Lead B   Lead C ...    each Lead manages a TEAM:
        │          │                                 • Senior Researcher(s)
        │      ┌───┴───┬───────┐                     • Researcher(s)
        │   SrR     R      R   ...                    • Source-Hunter / Scout(s)
        │   (team size scales with depth×breadth — §4)
        │
   (North Star / CCO heartbeat — read-only, from CLAUDE.md §2 — audits the whole effort)
```

All four top-level functions report to the **CRO**. The **North Star/CCO** review (CLAUDE.md
§2) is an external read-only overseer of the entire research org, not a report of the CRO.

---

## 3. Role definitions

### 3.1 Head of Research (CRO) — owner of the bar
- **Mandate:** Owns the research quality bar (DEPTH-RUBRIC.md). The **only** role that
  declares a research question "answered". Ratifies the question ontology, sequences the
  waves, allocates team budget, and adjudicates QA disputes.
- **Reports:** Program Architect(s), all Domain Research Leads, the Peer-Review/QA lead, the
  Org-Management lead.
- **Coordination:** Direct supervision of leads; standardization of outputs everywhere else.
- **Empowered to:** Send any work back as RED; freeze a wave; reallocate researchers; veto a
  premature "answered" claim. **Fail-closed:** if depth is ambiguous, the question is NOT done.

### 3.2 Program Architect(s) — designers of HOW
- **Mandate:** Maintain the QUESTION-ONTOLOGY (the tree + dependency graph), the layer model,
  the artifact schemas, and the wave plan. Detect coverage gaps (missing branches, dangling
  dependencies). Do **not** conduct primary research themselves — they design the machine.
- **Scaling:** 1 architect up to ~40 active questions; add a second when the live ontology
  exceeds ~40 open questions or spans >6 domains, to keep cross-domain dependency integrity.
- **Output:** updated ontology + dependency graph + a per-wave brief handed to the CRO.

### 3.3 Domain Research Leads (N — one per live domain)
- **Mandate:** Own one domain branch of the ontology (e.g. "multi-agent orchestration",
  "pricing & monetization across industries"). Decompose the branch into per-question briefs,
  assign them to their team, run the local iterate-to-perfection loop, and return a **compact
  domain digest** to the CRO. Each Lead **defines its own reports' roles** (roles-as-data).
- **Coordination:** Direct supervision within the team; lateral liaison with other Leads only
  through declared cross-domain dependencies (no ad-hoc chatter).
- **Span cap:** ≤ 7 direct reports. If a domain needs more, the Lead spawns **Sub-Leads** (one
  layer) each owning a sub-branch.

### 3.4 Researcher roles inside a Domain team
- **Senior Researcher:** owns the hardest questions in the branch, sets the adopt/reject
  rationale, mentors, first-line reviews juniors' artifacts before QA.
- **Researcher:** executes one `SUMMARY.md`+`BEST-PARTS.md` per source under the rubric.
- **Source-Hunter / Scout:** finds the full primary/peer-reviewed source set for a question
  (so coverage is exhaustive, not convenient); does not write summaries.

### 3.5 Peer-Review / QA Function (INDEPENDENT — the gate)
- **Mandate:** Audit every completed question against DEPTH-RUBRIC.md on four axes:
  **(1) citation faithfulness** (does the SUMMARY match the source exactly — no fabricated
  formulae/quotes/numbers), **(2) depth** (enough independent primary sources, full alternative
  space surveyed), **(3) coverage** (no missing sub-branch, dependencies satisfied),
  **(4) real-world usefulness** (does the BEST-PARTS actually inform AutoFirm's build).
- **Powers:** PASS / **FAIL-AND-RETURN** with a written defect list. A FAIL re-opens the
  question; it cannot be marked answered until QA passes. **Reproducibility check:** spot-re-runs
  a sample of source fetches to confirm citations resolve (addresses the agent-eval
  reproducibility gap: <20% of studies do statistical/verification checks — we will).
- **Independence:** never reports through a Domain Lead; reports directly to CRO. Reviewer of a
  question must not be its author (generator/evaluator split — CLAUDE.md §4.9). **No-self-dependency
  review:** a QA reviewer also may not review a question that **depends on a question they
  authored** — reviewing your own upstream work is a disguised self-review and is refused
  (fail-closed); the CRO assigns a different reviewer.
- **Staffing:** ≥ 1 QA reviewer per ~6 questions in flight; +1 dedicated **faithfulness
  auditor** whenever a wave touches formulae/quantitative claims.

### 3.6 Org-Management / Efficiency Function
- **Mandate:** Keep the org efficient, non-duplicative, and unstalled — the org's own
  "testing/QA of operations". Runs **operational unit checks** on the org itself:
  - **De-duplication:** detect two teams researching the same source/question; merge.
  - **Stall detection:** flag any question with no artifact progress in a wave; escalate.
  - **Load balancing:** detect over/under-allocated teams; recommend re-scope to CRO.
  - **Hierarchy invariants:** assert span ≤ 7, no orphan roles, no cycle in reporting,
    every role has a parent and an audit trail (fail-closed if violated).
  - **Throughput metrics:** questions/wave, FAIL rate, rework loops, time-to-PASS — fed to
    `evidence/`.
- **Powers:** advisory to CRO + can halt a duplicate spawn (fail-closed on the invariant set).

---

## 4. Dynamic team-sizing rule (data-driven, roles-as-data)

Team size for a domain branch is **computed, not guessed**, from a scored estimate the
Program Architect assigns each question, then aggregated per branch.

**Per-question complexity score** `C = Depth × Breadth × Criticality`, each scored 1–3:

| Factor | 1 (low) | 2 (med) | 3 (high) |
|---|---|---|---|
| **Depth** (how deep the literature goes) | settled, few canonical sources | active area | research-frontier, contested |
| **Breadth** (size of alternative space) | 1–2 approaches | 3–5 approaches | many competing paradigms |
| **Criticality** (impact on AutoFirm correctness/safety) | nice-to-have | important | safety/correctness-critical |

**Researchers assigned to a question:**
- `C ≤ 4` → 1 Researcher (+ shared Scout, + QA at branch level).
- `5 ≤ C ≤ 12` → 1 Senior + 1–2 Researchers + 1 Scout.
- `C ≥ 13` (e.g. 3×3×≥2) → spin a **sub-team**: 1 Senior + 2–3 Researchers + 1 Scout, and
  the Lead may add a Sub-Lead if the branch holds ≥ 3 such questions.

**Branch → team headcount** = sum of per-question assignments, then collapse shared Scouts/QA.
**Span guard:** if a Lead's direct reports would exceed 7, insert Sub-Leads (one layer) so no
node exceeds the cap. **Criticality multiplier:** any safety/correctness-critical question
gets a mandatory **second independent researcher** for cross-check (redundancy for fail-closed
correctness), regardless of C.

---

## 5. Dynamic role lifecycle (spawn / retire / re-scope)

Roles are typed records governed by audited transitions. Every transition is an append-only
audit event `{event, role_id, parent_id, actor, timestamp, reason}`.

- **SPAWN** (a manager creates a report): allowed iff `parent.span < 7`, the mandate is
  non-duplicative (Org-Mgmt check), and the parent has authority over the scope. The manager
  **writes the new role's mandate, tools, and success-criteria** (managers define reports).
- **RE-SCOPE** (change mandate/tools/parent): allowed by the role's manager or CRO; must keep
  the dependency graph acyclic and span ≤ 7.
- **RETIRE** (close a role): when its questions are PASSED and no open dependents need it.
  Closing is mandatory — **no graveyard** of idle roles (mirrors CLAUDE.md §3.8). Retired
  roles' artifacts persist; the role record is closed, not deleted.
- **Fail-closed:** any transition that would break an invariant (orphan, cycle, span>7,
  duplicate mandate, missing audit field) is **refused**, not silently fixed.

### 5.1 Triggers (data-driven, not vibes)
| Signal (from Org-Mgmt metrics) | Action |
|---|---|
| Branch backlog grows / wave deadline at risk | SPAWN more Researchers (within span; else Sub-Lead) |
| Question complexity re-estimated upward | upgrade Researcher→Senior, add cross-check |
| New domain appears in ontology | SPAWN a Domain Lead + seed team |
| Two teams overlap on same source/question | Org-Mgmt halts dup; CRO merges/re-scopes |
| QA FAIL rate on a branch > threshold | CRO adds a Senior + a faithfulness auditor |
| **Single question FAILs ≥ 3 times (oscillation)** | **Rework-loop circuit-breaker: mandatory CRO arbitration** — the iterate-to-perfection loop is halted and the CRO rules (re-scope the question, swap the team, or split it) so the loop cannot spin forever (mirrors RESEARCH-PROGRAM §4). |
| Branch fully PASSED, no dependents | RETIRE the team (no graveyard) |

---

## 6. Communication & flow (compact, audited)

- **Downward:** CRO → Leads (briefs) → Researchers (per-question scoped briefs + tool grants).
- **Upward:** Researcher → Lead (artifact links + 5-line digest) → CRO (domain digest). Never
  raw transcripts; standardized digests only.
- **Lateral:** only along declared cross-domain dependency edges; a "dependency-satisfied"
  signal flows from the upstream branch to the downstream Lead.
- **Gate:** Lead marks a question "ready" → **independent QA** PASS/FAIL → CRO marks "answered".
- **Heartbeats:** North Star/CCO (~30 min, read-only, whole-org) and the auto-resume watchdog
  (CLAUDE.md §4.8) run orthogonally; QA throughput + invariants feed `evidence/`.

This org is intentionally a microcosm of the AutoFirm platform: dynamic roles-as-data, strict
audited hierarchy with bounded spans, separated oversight, and an operations/efficiency
function running checks on itself — provable, scalable, and fail-closed.
