# HALO: Hierarchical Autonomous Logic-Oriented Orchestration for Multi-Agent LLM Systems

**Question informed:** L1.A1.5 (the MAS bridge: dynamic role creation/spawn); feeds L2.ORG, L2.A1.

## Full citation
- **Title:** HALO: Hierarchical Autonomous Logic-Oriented Orchestration for Multi-Agent LLM Systems
- **Authors:** Zhipeng Hou; Junyi Tang; Yipeng Wang
- **Year:** 2025 (submitted 17 May 2025)
- **Venue:** arXiv preprint arXiv:2505.13516
- **URL:** https://arxiv.org/abs/2505.13516 ; HTML https://arxiv.org/html/2505.13516v1
- **GRADE tier:** **Moderate** (arXiv preprint with full method + benchmarked results; not yet
  peer-reviewed). Used for the **dynamic-role-instantiation pattern** and its benchmark evidence;
  the architectural pattern is corroborated by the orchestration surveys cited in RESEARCH-PROGRAM
  (arXiv:2412.17481, 2601.13671) and by the A1.3 HALO-style role-assignment line in the ontology.

## What it is
A multi-agent LLM orchestration framework whose central contribution is an **extensible agent-role
instantiation mechanism** that **dynamically creates task-specific roles** instead of relying on a
fixed, predefined role space - the platform-side analogue of AutoFirm's gap->role-spec->spawn.

## Key claims (exact)
**Three-layer hierarchical architecture:**
1. **High-level planning agent** - decomposes the overall task into sequential subtasks, adapting
   the decomposition iteratively from execution history.
2. **Mid-level role-design agents** - **dynamically instantiate specialized agents** matching each
   subtask, "guided by subtask semantics, refined prompts, and global task context." This is the
   "extensible agent-role instantiation mechanism replacing predefined static role spaces."
3. **Low-level inference agents** - execute the subtasks via collaborative reasoning.

**Three modules:** Adaptive Prompt Refinement; Hierarchical Reasoning Stack; Workflow Search
Engine (subtask execution reformulated as a **workflow search** problem explored by **Monte Carlo
Tree Search (MCTS)** over the agentic action space).

**Benchmark results (Table 2) - exact, HALO vs. strongest baseline ADAS:**
- Overall average: **78.6% vs. 64.0% (+14.6%)** [abstract states ~14.4% avg over baselines].
- HumanEval pass@1: **95.2% vs. 82.4% (+12.8%)**.
- MMLU accuracy: **81.6% vs. 72.8% (+8.8%)**.
- MATH accuracy: **58.9% vs. 36.9% (+22.0%)**.

## Up/down-rate reasoning
Moderate: arXiv preprint, but with reproducible architecture and clear benchmark deltas extracted
verbatim from the HTML source. The relied-upon claim for AutoFirm is the **dynamic-role-design
pattern** (the mid-level role-design agent), which is independently corroborated by the
orchestration surveys; the specific benchmark numbers are reported as the paper's own results, not
re-derived, and are tagged as the source's measurements.

## Reproducibility note
The three-layer architecture, the role-instantiation mechanism, and the Table 2 numbers are in the
arXiv HTML (v1). The paper notes HALO instantiates roles dynamically but does **not** detail a
role-*retirement* mechanism - a gap AutoFirm fills from the org-theory sources (04, 10).
