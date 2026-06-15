# AutoFirm Research Question Ontology (QUESTION-ONTOLOGY.md)

> A **structured tree** of every research question needed to build AutoFirm well, grouped into
> three LAYERS with an explicit dependency graph. IDs are stable (`L<layer>.<branch>.<n>`) so
> the dependency graph, waves, and `docs/research/<source>/` folders can reference them.
>
> **Two halves, both mandatory:** **(A) Platform engineering** — how to build the autonomous
> agent-company substrate; **(B) Business building & operations across industries** — how real
> companies are researched, built, funded, marketed, sold, and run, so AutoFirm generalizes to
> ANY company of ANY size in ANY industry.

---

## Layer model

```
LAYER 1 — FOUNDATIONS    What is known / true / proven. Pure literature.
                          (orchestration theory, agent safety, org-design theory,
                           SLR method, business-function taxonomies). NO build decisions.
        │  feeds
        ▼
LAYER 2 — APPLIED         Given the foundations, WHAT SHOULD AUTOFIRM DO. Design options +
                          evidence-backed choices (architectures, memory design, business
                          playbooks per function). Maps onto branch-per-experiment (CLAUDE §3.4).
        │  feeds
        ▼
LAYER 3 — SYNTHESIS       The integrated AutoFirm architecture & operating doctrine: how the
                          platform + the business-building playbooks combine into one system
                          that runs ANY company. Output is the architecture spec + evidence.
```

A question may not enter Layer 2 until its Layer-1 dependencies are PASSED; Layer 3 may not
start until its Layer-2 dependencies are PASSED. The CRO enforces this gate.

---

## TOP-LEVEL BRANCHES

**A — PLATFORM ENGINEERING**
- A1 Multi-agent orchestration & coordination
- A2 Agent communication & workflow
- A3 Long-horizon autonomy, handoff & resume
- A4 Memory & learning infrastructure
- A5 Claude Code CLI substrate
- A6 Governance, auditability & provenance
- A7 Safety & control of autonomous agents
- A8 Integration & data layer
- A9 Evaluation, evidence & QA of the platform

**B — BUSINESS BUILDING & OPERATIONS (ANY INDUSTRY)**
- B1 Organizational operating models by industry
- B2 Taxonomy of automatable business functions
- B3 Entrepreneurship & opportunity validation
- B4 Financial / customer / operational modeling on real data
- B5 Pricing & monetization
- B6 Fundraising & capital
- B7 Marketing
- B8 Sales
- B9 Customer support & success
- B10 Legal, compliance & risk
- B11 Operations & supply/delivery
- B12 Cross-industry generalization (the "any company" question)
- B13 Product & design capability for client builds (UI/UX, design systems, accessibility, live E2E)
- B14 Software delivery & engineering quality for client products (CI/CD, test strategy, code quality)
- B15 Professional artifact-generation capability (financial models, slide decks, documents)

---

# LAYER 1 — FOUNDATIONS (literature only)

## A1 Multi-agent orchestration & coordination
- **L1.A1.1** Taxonomy of MAS coordination (orchestrator-worker, hierarchical, blackboard,
  market/auction, debate, swarm) — strengths/failure modes per pattern.
- **L1.A1.2** When does multi-agent beat a single strong agent? (evidence, not assumption.)
- **L1.A1.3** Hierarchical/role-based orchestration patterns (HALO-style) & dynamic role assignment.
- **L1.A1.4** Coordination-cost / context-flooding theory (information-processing view).
- **L1.A1.5** **Hiring & new-role creation in real orgs** — how firms detect a capability gap,
  author a role spec, hire/onboard, and retire roles (workforce planning, role-charter design):
  the org-theory basis for AutoFirm's automated **gap-detect → manager-authored role-spec → spawn
  → onboard → retire** lifecycle (single-writer + must_study rules). Feeds L2.ORG.

## A2 Agent communication & workflow
- **L1.A2.1** Agent communication protocols & message schemas (typed contracts, ACL lineage).
- **L1.A2.2** Workflow/DAG vs. emergent coordination; reliability of each.
- **L1.A2.3** Standardization-of-outputs as coordination (org-theory ↔ MAS bridge).

## A3 Long-horizon autonomy, handoff & resume
- **L1.A3.1** Levels-of-autonomy frameworks (what "autonomous" means, by level).
- **L1.A3.2** Long-horizon failure modes (drift, goal misgeneralization, context loss).
- **L1.A3.3** Checkpoint / handoff / resume mechanisms & state externalization.

## A4 Memory & learning infrastructure
- **L1.A4.1** Agent-memory taxonomy (short/long, episodic/semantic, storage→reflection→experience).
- **L1.A4.2** RAG & retrieval foundations; limits of context windows.
- **L1.A4.3** Learning-over-time mechanisms (reflection, experience abstraction, RL-on-memory).
- **L1.A4.4** Memory security & governance over the memory lifecycle (poisoning, deletion-verify).

## A5 Claude Code CLI substrate
- **L1.A5.1** CLI capabilities/limits (sessions, subagents, hooks, MCP, headless, settings).
- **L1.A5.2** Determinism, resumability & idempotency of CLI sessions.
- **L1.A5.3** Tool/permission model & sandboxing of the substrate.

## A6 Governance, auditability & provenance
- **L1.A6.1** Provenance models (what/when/who; FHIR-Provenance/AuditEvent-style, W3C PROV).
- **L1.A6.2** Immutable append-only audit logs & tamper-evidence.
- **L1.A6.3** Governance-aware telemetry & closed-loop enforcement.
- **L1.A6.4** **Workspace organization & the public/private data boundary** — clean folder
  structure + naming for the repo and per-company workspaces, and the **hard separation of the
  public version-controlled codebase from finance/company-sensitive data that must NEVER be
  committed or deployed** (gitignored private workspace, enforced in the data layer not by
  convention), plus the **organizer/librarian role** that keeps both intact. Ties to A8.2/A8.3,
  L1.B4.4 (PII boundary), A7.3 (fail-closed). (CLAUDE.md §3.12, §5.6, §5.7.)

## A7 Safety & control of autonomous agents
- **L1.A7.1** Threat models for agentic AI (TRiSM; prompt injection; tool misuse).
- **L1.A7.2** Oversight architectures (verifiability-first, audit agents, kill-switch, HITL).
- **L1.A7.3** Fail-closed design patterns & least-privilege for agents.

## A8 Integration & data layer
- **L1.A8.1** External-tool/API integration patterns & untrusted-input handling.
- **L1.A8.2** Multi-tenant data isolation (data-layer enforcement, not convention).
- **L1.A8.3** Secrets & credential scoping for autonomous agents.

## A9 Evaluation, evidence & QA of the platform
- **L1.A9.1** Agent-evaluation taxonomy (what vs. how) & reliability/reproducibility pitfalls.
- **L1.A9.2** Statistical rigor for stochastic systems (repeat-trial, CIs, hypothesis tests).
- **L1.A9.3** Mutation testing & test-adequacy theory (tests-with-teeth foundations).

## B1 Organizational operating models by industry
- **L1.B1.1** Org-design theory (contingency, Galbraith Star, Mintzberg configurations).
- **L1.B1.2** Operating-model archetypes by industry (SaaS, services, manufacturing, retail,
  marketplace, fintech, healthcare, etc.) — structure, roles, KPIs.
- **L1.B1.3** Span-of-control, coordination & hierarchy scaling.

## B2 Taxonomy of automatable business functions
- **L1.B2.1** Canonical value-chain taxonomy (Porter primary + support activities).
- **L1.B2.2** Business Model Canvas building blocks (Osterwalder) as a function map.
- **L1.B2.3** Which functions are automatable to what degree (evidence-based map).

## B3 Entrepreneurship & opportunity validation
- **L1.B3.1** Opportunity-discovery & validation theory (lean startup, customer development,
  jobs-to-be-done) — empirical support and critiques.
- **L1.B3.2** Market sizing & TAM/SAM/SOM methodology.

## B4 Financial / customer / operational modeling on real data
- **L1.B4.1** Financial modeling foundations (3-statement, DCF, unit economics, cohort).
- **L1.B4.2** Customer modeling (CAC/LTV, retention/cohort, segmentation).
- **L1.B4.3** Operational modeling (capacity, throughput, queueing/forecasting).
- **L1.B4.4** Public-data sourcing + PII boundary — where/how AutoFirm legally obtains REAL public
  data (annual reports, public registries, regulatory filings, public APIs), source ToS/scraping
  legality, and the **hard synthetic-only-for-sensitive boundary**: real public corporate data is
  allowed; **real PII, client data, or confidential/deal documents are NEVER used** in tests or
  validation (CLAUDE.md §3.12 public-data-only final gate + §5.6 fail-closed data handling).
  Operationalizes the §3.12 validation gate and feeds L2.B4.

## B5–B11 (function foundations — each = theory + cross-industry evidence)
- **L1.B5.1** Pricing & monetization theory (value-based, cost-plus, dynamic; willingness-to-pay).
- **L1.B6.1** Fundraising & capital structure foundations (equity/debt/grants; stage norms).
- **L1.B7.1** Marketing foundations (STP, 4Ps, channels, attribution; brand vs. performance).
- **L1.B8.1** Sales foundations (funnels, methodologies, B2B vs. B2C motions).
- **L1.B9.1** Customer support & success foundations (support tiers, SLAs, CSAT/NPS, deflection).
- **L1.B10.1** Legal/compliance/risk foundations (entity formation, contracts, IP, regulatory map).
- **L1.B11.1** Operations & supply/delivery foundations (lean/TPS, SCOR, service ops).

## B12 Cross-industry generalization
- **L1.B12.1** What makes a business playbook **general** vs. industry-specific (the invariants).
- **L1.B12.2** Industry-classification schemes (NAICS/GICS) as a parameterization for playbooks.

> **FIXED industry panel (the B12 generalization golden set).** The Program Architect declares this
> diverse, fixed panel up front (CLAUDE.md §4.5); every generalization claim (L1.B12, L2.B12) is
> proven against ALL of it, not asserted. The panel deliberately spans B2B/B2C, regulated/
> unregulated, and physical/digital so "any company" is tested, not claimed:
>
> | # | Industry | B2B/B2C | Regulated? | Physical/Digital |
> |---|---|---|---|---|
> | 1 | B2B SaaS | B2B | Light | Digital |
> | 2 | Professional services / consulting | B2B | Light | Services |
> | 3 | Discrete manufacturing | B2B | Moderate | Physical |
> | 4 | E-commerce / DTC retail | B2C | Light | Physical+Digital |
> | 5 | Two-sided marketplace | B2B+B2C | Moderate | Digital |
> | 6 | Fintech / payments | B2C+B2B | Heavy | Digital |
> | 7 | Healthcare / digital health | B2B+B2C | Heavy | Physical+Digital |
> | 8 | Restaurant / food service | B2C | Moderate | Physical |
>
> A playbook is "general" only when it produces a sensible, evidence-backed result for **every**
> row above. Overfitting to any single row is an instant FAIL (DEPTH-RUBRIC §5/§6).

## B13 Product & design capability for client builds
> AutoFirm itself is headless, but it must build **institution-grade, non-vibe-coded** products/UIs
> for client companies (CLAUDE.md §2 CDO/Head of Design, §3.14, §4.9).
- **L1.B13.1** Design-research / competitive-teardown method (how to study category-leading,
  unicorn-or-bigger products and distil patterns — inspiration, never plagiarism).
- **L1.B13.2** Design-systems & design-token theory (color/type/spacing/motion scales, component
  inventories) and the anti-AI-slop bar (real hierarchy, restraint, custom decisions).
- **L1.B13.3** UX heuristics & interaction design (Nielsen heuristics, state coverage:
  loading/empty/error/edge; nothing-static — every control wired to real behaviour).
- **L1.B13.4** Accessibility foundations — **WCAG 2.2 AA** (automated + manual keyboard/focus/
  screen-reader) and Core Web Vitals performance budgets (LCP/CLS/INP via Lighthouse).
- **L1.B13.5** Live, browser-driven E2E testing theory (Playwright-style) — exercising every
  button/input/link/flow in the running app (happy path + failure/edge), generator/evaluator split.

## B14 Software delivery & engineering quality for client products
> How AutoFirm **engineers the actual software it ships for clients** — distinct from A9 (platform
> eval) and B11 (ops). Applies CLAUDE.md §3.6/§5.5 (tests-with-teeth) and §5.7 (code-org) to
> *client* code.
- **L1.B14.1** CI/CD pipeline design for delivered software (build/test/scan gates, deploy/rollback,
  preview environments).
- **L1.B14.2** Testing strategy for client products (test pyramid, property/fuzz/mutation testing,
  coverage + mutation-score gates) applied to shipped code.
- **L1.B14.3** Code-organisation & maintainability (self-documenting naming, file-size limits,
  module boundaries — CLAUDE.md §5.7) and secure-SDLC for delivered software (SAST/DAST/dep-scan).

## B15 Professional artifact-generation capability
> How best-in-class business artifacts are *actually* produced, so agents generate genuinely
> excellent (not templated) deliverables. Distinct from B13 (UIs) / B14 (software); runs under the
> A6.4 workspace/data boundary; financial-model logic ties to L1.B4.1.
- **L1.B15.1** **Financial models / spreadsheets (Excel)** — institutional model-build standards
  (FAST/SMART, 3-statement/DCF structure, formatting & audit conventions) + programmatic generation
  (openpyxl/xlsxwriter-class libs; live formulas, not dead values).
- **L1.B15.2** **Slide decks (PowerPoint)** — consulting/IB-grade deck craft (pyramid principle,
  message-titled slides, data-ink, chart design) + programmatic generation (python-pptx-class libs)
  that avoids the templated/AI-slop look.
- **L1.B15.3** **Documents** — professional long-form deliverables (memos, reports, contracts:
  structure, tone, typography) + programmatic generation (DOCX/PDF/Markdown→PDF pipelines).

---

# LAYER 2 — APPLIED (design options + evidence-backed choices)

> Each L2 question = "given the L1 evidence, what should AutoFirm DO?" → produces options on
> `experiment/*` branches, a golden metric, and a chosen winner (CLAUDE §3.4/§4.5).

**Platform design choices**
- **L2.A1** Choose AutoFirm's orchestration topology (hierarchical orchestrator-worker + dynamic
  roles) ← L1.A1.*, L1.A2.*, L1.B1.1.
- **L2.A3** Design the long-horizon autonomy + handoff/resume protocol ← L1.A3.*, L1.A5.2.
- **L2.A4** Design the memory & learning infrastructure (tiered, provenance-aware, governed)
  ← L1.A4.*, L1.A6.1.
- **L2.A5** Define the CLI-substrate execution model (sessions, subagents, MCP, watchdog)
  ← L1.A5.*, L1.A3.3.
- **L2.A6** Design provenance + append-only audit + roles-as-data audit trail, **plus the workspace
  layout + public/private data-boundary scheme and the organizer/librarian role** ← L1.A6.*
  (incl. **L1.A6.4**), L1.A1.3, L1.A8.2-3, L1.B4.4.
- **L2.A7** Design the safety/control stack (kill-switch, HITL gates, fail-closed, least-priv)
  ← L1.A7.*, L1.A8.2-3.
- **L2.A8** Design the integration & multi-tenant data layer ← L1.A8.*, L1.A6.2.
- **L2.A9** Design the platform's own evaluation harness + tests-with-teeth ← L1.A9.*.
- **L2.ORG** Design the **dynamic, audited, scalable agent-org engine** (gap-detection →
  manager-authored role-spec → spawn → onboard → retire, span caps, mgmt+QA functions) ← L1.B1.*,
  L1.A1.3, **L1.A1.5**, L1.A6.*, L1.A7.*. *(directly informs RESEARCH-ORG.md and the live platform.)*

**Business playbook design (per function — must be industry-parameterized)**
- **L2.B2** A function-decomposition engine that maps any company → automatable functions
  ← L1.B2.*, L1.B1.2.
- **L2.B3** An opportunity-validation playbook ← L1.B3.*, L1.B4.2.
- **L2.B4** A real-data modeling toolkit (financial/customer/ops) ← L1.B4.1-3, **L1.B4.4**, L1.A8.1.
- **L2.B5** Automated **pricing & monetization** playbook ← L1.B5.1, L1.B4.2 (LTV/CAC), L1.B12.*.
- **L2.B6** Automated **fundraising & capital** playbook ← L1.B6.1, L1.B4.1, L1.B12.*.
- **L2.B7** Automated **marketing** playbook ← L1.B7.1, L1.B4.2, L1.B12.*.
- **L2.B8** Automated **sales** playbook ← L1.B8.1, **L1.B7.1** (marketing→sales handoff), L1.B12.*.
- **L2.B9** Automated **customer support & success** playbook ← L1.B9.1, L1.B8.1, L1.B12.*.
- **L2.B10** Automated **legal/compliance/risk** playbook ← L1.B10.1, L1.A7.* (fail-closed), L1.B12.*.
- **L2.B11** Automated **operations & supply/delivery** playbook ← L1.B11.1, L1.B4.3, L1.B12.*.
- **L2.B12** The generalization layer: parameterize every playbook by industry/size, proven against
  the **fixed industry panel** golden set ← L1.B12.*, all L2.B*.
- **L2.B13** The AutoFirm **design-build + live-E2E playbook** (back-end-first, real-data/all-states,
  design-token adherence, WCAG 2.2 AA, Core Web Vitals, green live Playwright DoD)
  ← L1.B13.*, L1.A9.* (eval rigor).
- **L2.B14** The AutoFirm **client software-delivery engine** (CI/CD + tests-with-teeth + code-org +
  secure-SDLC applied to shipped client code) ← L1.B14.*, L1.A9.3, L1.A7.*.
- **L2.B15** The AutoFirm **artifact-generation engine** (auto-produce institutional-grade
  spreadsheets/models, decks, and documents — live formulas, message-titled storylines, no
  templated/AI-slop output) ← L1.B15.*, L1.B4.1 (model logic), L1.A6.4 (writes into the private
  workspace, never the public repo).

---

# LAYER 3 — SYNTHESIS (integrated architecture & doctrine)

- **L3.PLATFORM** The integrated AutoFirm platform architecture (orchestration + memory +
  governance + safety + data + eval as one fail-closed system) ← all L2.A* + L2.ORG.
- **L3.BUSINESS** The integrated company-building operating doctrine (validate→build→fund→
  market→sell→operate→support, **plus design-build (L2.B13) and software-delivery (L2.B14)** of the
  client products themselves, generalized by industry, **plus artifact generation (L2.B15)**)
  ← all L2.B* (incl. L2.B13, L2.B14, L2.B15).
- **L3.WHOLE** How platform + doctrine compose: the dynamic agent-company that runs ANY company,
  end-to-end, with evidence it generalizes ← L3.PLATFORM + L3.BUSINESS.

---

## Dependency graph (critical edges)

The full critical-edge graph (incl. the new L1.A1.5→L2.ORG, L1.A6.4→L2.A6, and L1.B15.*→L2.B15
edges) lives in the sibling file **`DEPENDENCY-GRAPH.md`** to keep this file navigable. Every edge
is also stated inline in each L2 entry's `←` clause above; the ontology remains the source of truth.

**Cross-half edges (do not miss):** L1.B1.1 (org theory) feeds L2.A1 and L2.ORG — the platform's
orchestration IS organizational design. L1.A6/A7 (governance/safety) feed both halves: every
business playbook must run under the same audited, fail-closed governance as the platform.
