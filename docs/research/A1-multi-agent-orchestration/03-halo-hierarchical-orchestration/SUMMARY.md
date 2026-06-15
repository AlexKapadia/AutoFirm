# SUMMARY — HALO: Hierarchical Autonomous Logic-Oriented Orchestration for Multi-Agent LLM Systems

## Full citation
- **Title:** HALO: Hierarchical Autonomous Logic-Oriented Orchestration for Multi-Agent LLM Systems
- **Authors:** Zhipeng Hou (Nanjing Univ. of Posts and Telecommunications), Junyi Tang (NJUPT),
  Yipeng Wang (Chongqing University)
- **Year:** 2025 (submitted 17 May 2025)
- **Venue:** arXiv preprint (arXiv:2505.13516v1) [cs.MA]. "Preprint. Under review."
- **URL:** https://arxiv.org/abs/2505.13516 ; PDF: https://arxiv.org/pdf/2505.13516 ;
  code: https://github.com/23japhone/HALO

## Questions informed
- **L1.A1.3** (hierarchical/role-based orchestration + dynamic role assignment) — PRIMARY (the
  named "HALO-style" reference in the ontology).
- **L1.A1.1** (hierarchical pattern) — PRIMARY.
- L1.A1.2 (multi beats single) — supporting (HALO vs single-agent ReAct numbers).

## GRADE tier
**Moderate.** arXiv preprint with full method, equations, ablations, and a code repo (reproducible).
Down-rate: under review, single-team, GPT-4o-only evaluation, 13% MMLU sub-sample. Up-rate: explicit
formulae + open code. Quantitative gains are tier-Moderate and corroborated directionally by
independent multi-beats-single sources (02, 04, 09).

## Architecture — three-stage paradigm
1. **Adaptive Prompt Refinement** — four agents P1–P4 (Task Parser, Prompt Template, Prompt
   Optimization, Prompt Generator) turn raw query Q into refined prompt Q̄.
2. **Hierarchical Reasoning Stack** — three tiers:
   - **High-level planning agent A_plan** — step-wise task decomposition into subtasks {T1…TK}.
   - **Mid-level role-design agents A_role** — dynamically instantiate role-specialized agents.
   - **Low-level inference agents A_k = {a_k^(1), a_k^(2), …}** — execute each subtask.
3. **Workflow Search Engine** — MCTS over the agentic action space to find optimal workflows.

## Formulae (reproduced verbatim with the paper's numbering)
- **Eq. (1) objective:** `W* = arg max Value(Q, W)` — find the workflow maximizing effectiveness.
- **Eq. (2):** `F = P1(Q) = (T, I, D)` — structured task triplet.
- **Eq. (3):** `Q0 = P2(Q, F)`  · **Eq. (4):** `Qopt = P3(Q0, F)`  · **Eq. (5):** `Q̄ = P4(Qopt, F)`.
- **Eq. (6):** `Tk = A_plan(Q̄, F, H_{k-1})` — step-wise decomposition using execution history H.
- **Eq. (7):** `a_k^(i) = A_role(Tk, Q̄, F) ⊕ φ_k^(i)` — role instantiation + role-specific prompt φ.
- **Eq. (8):** `Yk = {y_k^(1), …} = A_k(Tk, Q̄, F)` — subtask outputs.
- **Eq. (9) Selection (UCT):**
  `UCT(a_k^(i)) = v_k^(i)/n_k^(i) + η · sqrt( log N / n_k^(i) )`
  where v_k^(i) = score value of agent a_k^(i); n_k^(i) = visits to a_k^(i); N = visits to the parent
  a_k^(i-1); η = exploration coefficient. (Standard four-stage MCTS: Selection, Expansion,
  Simulation, Backpropagation.)
- **Early-stop:** inspired by Byzantine consensus ("at least 3p+1 agents are required to tolerate p
  faulty agents in a single round of communication"); HALO terminates if **≥66%** of completed
  subtasks yield a consistent answer, or at a max depth limit.

## Results (Table 2, GPT-4o, mean over 3 runs)
- **vs single-agent ReAct:** HumanEval pass@1 **95.2% vs 69.1%** (+26.1); MMLU **81.6% vs 57.6%**
  (+24.0); MATH **58.9% vs 29.2%** (+29.7); Avg **78.6% vs 52.0%** (+26.6).
- **vs strongest baseline (ADAS):** Avg **78.6% vs 64.0%** (+14.6). HumanEval +12.8 (95.2 vs 82.4);
  MMLU +8.8 (81.6 vs 72.8); MATH +22.0 (58.9 vs 36.9).
- **Abstract MMLU subjects vs ADAS:** **70.8% vs 56.4%** (+14.4). MATH hard subareas: 43.9% avg.
- Headline abstract figure: "**14.4% average improvement over state-of-the-art baselines**"; up to
  13.3% on MMLU Moral Scenarios; up to 19.6% on MATH Algebra.
- Baselines: single-agent ReAct; static MAS (CAMEL, LLM-Debate); dynamic MAS (DyLAN, AgentVerse, ADAS).

## Stated rationale / limitations
- Mechanism claim: hierarchy "reduces cognitive overload" vs a monolithic single agent that must
  "simultaneously manage planning, reasoning, and reflection."
- Limitations not enumerated explicitly; future work = memory mechanisms + knowledge integration.
  (Note for QA: GPT-4o-only, sub-sampled MMLU/MATH — generality caveat.)

## Reproducibility note
Equations and Table-2 numbers extracted from the PDF via pdftotext (pages 1–8). UCT (Eq. 9) and the
66% early-stop are the load-bearing/critical items; reproduced in the source's own notation.
