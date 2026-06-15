# AutoFirm Research Program (RESEARCH-PROGRAM.md)

> How the research program actually runs: the layers, the peer-review/QA protocol, the
> iteration/gap-closure loop, the synthesis-to-architecture method, and the on-disk persistence
> convention. Companion files: `RESEARCH-ORG.md` (who), `QUESTION-ONTOLOGY.md` (what),
> `DEPTH-RUBRIC.md` (how good). Implements CLAUDE.md §2, §3.3, §3.4, §3.6, §3.7, §4.

---

## 1. The layered process (Foundations → Applied → Synthesis)

The program runs as **waves**, each aligned to the ontology layers (QUESTION-ONTOLOGY.md):

1. **Layer 1 (Foundations):** pure literature. Answers "what is known/true". Gate: every
   Layer-1 question PASSes DEPTH-RUBRIC before any Layer-2 work that depends on it begins.
2. **Layer 2 (Applied):** design options + evidence-backed choices. Competing approaches run on
   `experiment/<approach>` branches against a pre-agreed golden set + metric (CLAUDE §3.4/§4.5);
   only the evidence-backed winner is recorded. Gate: Layer-2 dependencies PASS before Layer 3.
3. **Layer 3 (Synthesis):** integrate into the AutoFirm architecture spec + operating doctrine.

The CRO enforces the **dependency gate** between layers (no L2 on un-PASSED L1; no L3 on
un-PASSED L2). This follows the Kitchenham/PRISMA discipline of plan → conduct → report, made
auditable: each wave has a written plan, a conduct log, and a report.

---

## 2. Per-question lifecycle

```
ASSIGN ─► SCOUT (find full source set) ─► SUMMARIZE (one folder per source)
   ─► SENIOR REVIEW (first-line) ─► INDEPENDENT QA (DEPTH-RUBRIC) ─► CRO "answered"
                                          │ FAIL + defect list
                                          └──────────► back to SUMMARIZE/SCOUT (loop)
```

- **Scout** assembles the candidate source set so coverage is exhaustive (DEPTH-RUBRIC §4),
  not convenient.
- **Researcher** writes `SUMMARY.md` + `BEST-PARTS.md` per source under the rubric.
- **Senior** does first-line review (catches obvious gaps before QA).
- **Independent QA** (different principal than the author) applies the PASS checklist.
- **CRO** is the only role that flips a question to "answered".

---

## 3. Peer-Review / QA protocol

The QA function (RESEARCH-ORG.md §3.5) audits four axes, each PASS/FAIL with a written reason:

1. **Citation faithfulness** — formulae/numbers/quotes match the source exactly; QA **spot-fetches a
   defined sample — ≥ 20% of the question's sources (min 2) and 100% of safety/correctness-critical
   formulae/quantitative claims** (DEPTH-RUBRIC §3.5) — to confirm they resolve and say what is
   claimed (reproducibility check — directly answering the agent-eval finding that <20% of studies
   verify their numbers).
2. **Depth** — source counts + tiers meet DEPTH-RUBRIC §1–2; full alternative space surveyed §4.
3. **Coverage** — no missing sub-branch; all ontology dependencies PASSED.
4. **Real-world usefulness** — `BEST-PARTS.md` states a concrete, general, build-relevant
   implication (§5).

**Powers & independence:** QA returns **PASS** or **FAIL-AND-RETURN + defect list**; it reports
directly to the CRO (never through a Domain Lead); the reviewer is never the author
(generator/evaluator split). Any fabrication finding escalates immediately to the CRO.

**Metrics fed to `evidence/`:** FAIL rate per branch, rework loops per question, time-to-PASS,
source-tier distribution, sample re-fetch success rate.

---

## 4. Iteration / gap-closure loop (never one-shot)

Research is a **loop**, not a single pass (CLAUDE.md §3.7):

```
RESEARCH ─► QA ─► (FAIL?) ─► HARDEN (add sources / fix citation / survey missing options)
   ▲                                                   │
   └───────────────── RE-RESEARCH ◄────────────────────┘   repeat until CRO bar met
```

- A FAIL is not a setback — it is the mechanism. If a question PASSes on the first try with
  thin sourcing, QA treats that as a smell and probes harder (mirrors §3.6 "if everything
  passes first try, make it harder").
- **Circuit-breaker (loop cannot spin forever):** if a single question FAILs **≥ 3 times**
  (oscillation), the loop is halted and **CRO arbitration is mandatory** — the CRO re-scopes,
  splits, or re-teams the question (RESEARCH-ORG.md §5.1). The iterate-to-perfection loop is
  bounded, not infinite.
- **Gap detection** runs continuously: the Program Architect re-scans the ontology each wave for
  missing branches and dangling dependencies; new gaps spawn new questions (and, if needed, new
  roles — RESEARCH-ORG.md §5).
- The loop also re-runs **after** synthesis and after any real-world validation finding
  (CLAUDE.md §3.12): new evidence re-opens affected questions.

---

## 5. Synthesis-to-architecture method (Layer 3)

Turning PASSED research into the AutoFirm design:

1. **Aggregate `BEST-PARTS.md`** across a branch into a per-branch **design-decision record**:
   the adopted option, the rejected alternatives + why, and the cited evidence for each.
2. **Resolve cross-branch conflicts** (e.g. an orchestration choice vs. a safety constraint) by
   re-reading the governing evidence; the safety/governance branch (A6/A7) has **veto** under
   the fail-closed principle (CLAUDE.md §5.6).
3. **Branch-per-experiment for contested choices:** where evidence is close, implement the
   candidates on `experiment/*`, measure on the golden set, keep the winner, delete the rest
   (no graveyard, CLAUDE.md §3.8/§4.4).
4. **Emit the architecture spec** (`docs/architecture/`) and **operating doctrine**, each line
   tracing back to a PASSED question + its evidence. Generality is mandatory: a decision tied to
   one example/industry is rejected (CLAUDE.md §3.9). The Program Architect declares the **fixed
   diverse industry panel** (QUESTION-ONTOLOGY.md B12) as the generalization golden set up front,
   and every business playbook must produce a sensible result for **all** panel rows (CLAUDE.md §4.5).
5. **Evidence showcase:** quantitative findings flow into `evidence/` (stats + PNG/HTML charts +
   B&W flow diagrams), analysis-only deps isolated from runtime (CLAUDE.md §3.10).

---

## 6. Persistence convention (on disk)

Root: `docs/research/`. **One folder per SOURCE**, named `docs/research/<branch>/<source-slug>/`,
each containing exactly:

- **`SUMMARY.md`** — a faithful, exactly-cited structured summary of the source: full citation
  (Title · Authors/Org · Year · Venue · URL/DOI), the question(s) it informs (ontology IDs),
  the key claims with exact formulae/numbers + locators, and the source's GRADE tier with
  up/down-rate reasoning (DEPTH-RUBRIC §2–3).
- **`BEST-PARTS.md`** — the adopt/reject note: what AutoFirm should take from this source and
  why, what it rejects and why, and the concrete build implication (component/contract/test).

Per-question index files live at the branch root (e.g. `docs/research/agent-communication-and-flow/
INDEX.md`) listing the question IDs, their sources, and current status (assigned / in-review /
PASSED). The `_program/` folder (this file + the other three) is the durable program spec.

Seed branches scaffolded with source folders on disk (verified 2026-06-15): `agent-communication-
and-flow/` (8 sources, A2), `claude-code-substrate/` (2 sources, A5), `evaluation-and-evidence/`
(4 sources, A9), `integration-and-data-layer/` (9 sources, A8). All four contain source folders;
none has yet been QA-PASSED, so they are **seeded, not answered**. Remaining branches — including
the new **B13** (product/design) and **B14** (software delivery) — are created on first assignment.

---

## 7. Sources grounding this program (exact citations)

*Research methodology & evidence quality*
- Kitchenham, B. & Charters, S. (2007). *Guidelines for Performing Systematic Literature Reviews
  in Software Engineering.* Technical Report EBSE 2007-001, Keele Univ. & Durham Univ.
  https://www.scirp.org/reference/ReferencesPapers?ReferenceID=1555797
- Guyatt, G. et al. (2011). *GRADE guidelines: 3. Rating the quality of evidence.* J. Clinical
  Epidemiology. https://www.sciencedirect.com/science/article/abs/pii/S089543561000332X
- Cochrane Handbook §12.2.1, *The GRADE approach.*
  https://handbook-5-1.cochrane.org/chapter_12/12_2_1_the_grade_approach.htm
- PRISMA (Preferred Reporting Items for Systematic Reviews and Meta-Analyses) — reporting
  discipline integrated with Kitchenham (per SE-SLR practice).

*Multi-agent orchestration & coordination*
- *A Survey on LLM-based Multi-Agent System: Recent Advances and New Frontiers in Application*
  (2024–25). arXiv:2412.17481. https://arxiv.org/html/2412.17481v2
- *Multi-agent collaboration mechanisms: a survey of LLMs.* Univ. College Cork repository.
  https://cora.ucc.ie/server/api/core/bitstreams/e0305ac0-e1df-45b1-98c5-09510a44b4bd/content
- *The Orchestration of Multi-Agent Systems: Architectures, Protocols, and Enterprise Adoption.*
  arXiv:2601.13671. https://arxiv.org/pdf/2601.13671
- *Beyond the Strongest LLM: Multi-Turn Multi-Agent Orchestration vs. Single LLMs on Benchmarks.*
  arXiv:2509.23537. https://arxiv.org/pdf/2509.23537

*Memory & learning infrastructure*
- *From Storage to Experience: A Survey on the Evolution of LLM Agent Memory Mechanisms.*
  Preprints.org 202601.0618. https://www.preprints.org/manuscript/202601.0618
- *A Survey on Long-Term Memory Security in LLM Agents.* arXiv:2604.16548.
  https://arxiv.org/html/2604.16548v2
- *A-Mem: Agentic Memory for LLM Agents.* arXiv:2502.12110. https://arxiv.org/html/2502.12110v1

*Safety, governance, provenance, evaluation of the platform*
- *TRiSM for Agentic AI: Trust, Risk, and Security Management in LLM-based Agentic Multi-Agent
  Systems.* https://www.sciencedirect.com/science/article/pii/S2666651026000069
- *Verifiability-First Agents: Provable Observability and Lightweight Audit Agents.*
  arXiv:2512.17259. https://arxiv.org/pdf/2512.17259
- *Governance-Aware Agent Telemetry for Closed-Loop Enforcement in Multi-Agent AI Systems.*
  arXiv:2604.05119. https://arxiv.org/pdf/2604.05119
- Mohammadi, M., Li, et al. (2025). *Evaluation and Benchmarking of LLM Agents: A Survey.*
  KDD 2025 / arXiv:2507.21504. https://arxiv.org/abs/2507.21504

*Organizational design & business-function taxonomy (the "any company" half)*
- Galbraith, J. *The Star Model™.* https://jaygalbraith.com/wp-content/uploads/2024/03/StarModel.pdf
- Burton & Obel (2018). *The science of organizational design: fit between structure and
  coordination.* J. Organization Design.
  https://link.springer.com/article/10.1186/s41469-018-0029-2
- Donaldson. *The Contingency Theory of Organizational Design.* Springer.
  https://link.springer.com/chapter/10.1007/0-387-34173-0_2
- Mintzberg's configurations (organizational components & coordination mechanisms). ACCA tech
  article. (Primary: Mintzberg, *The Structuring of Organizations*, 1979.)
- Porter, M. (1985). *Competitive Advantage* — the Value Chain (primary + support activities).
  https://en.wikipedia.org/wiki/Value_chain (summary; primary = Porter 1985).
- Osterwalder, A. & Pigneur, Y. (2010). *Business Model Generation* — Business Model Canvas.
  https://en.wikipedia.org/wiki/Business_model_canvas (summary; primary = Osterwalder/Pigneur).

> Note: arXiv/preprint items are tiered **Moderate** under DEPTH-RUBRIC §2 unless peer-reviewed;
> book/standard items (Porter, Osterwalder, Kitchenham, GRADE) are the **primary** anchors.
> Wikipedia/practitioner links above are pointers to the primary works, not the citation of
> record — researchers must cite the primary work itself in `SUMMARY.md`.
