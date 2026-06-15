# BEST-PARTS — SagaLLM (Chang & Geng)

## ADOPT (the LLM-specific realization of sources 08+09 — highest build relevance)
1. **Adopt the three-dimension checkpoint payload (Application / Operation / Dependency state) as AutoFirm's checkpoint schema.**
   - *Why:* it is the saga/recovery theory (sources 08, 09) instantiated for LLM agents, and it names exactly what a resumed AutoFirm session needs: app state, operation state (where we are in the saga), and dependency state (what depends on what).
   - *Build implication:* AutoFirm's checkpoint object = `{SA: workspace/git/files, SO: saga step + transaction log + decision reasoning, SD: operation dependency graph + compensation metadata}` plus the **verbatim stored goal** (from source 07). This is the concrete data contract for L2.A3.

2. **Adopt the separate GlobalValidationAgent (independent generator/evaluator split).**
   - *Why:* directly addresses self-validation failure (source 05's "False Assumption", source 06's reflection-module errors) — an agent cannot reliably catch its own errors. SagaLLM externalizes validation to a *different* agent.
   - *Build implication:* AutoFirm's resume + milestone checks run a **separate validation agent** (never the producing agent) that validates intra-agent outputs and inter-agent dependencies before a checkpoint is committed — mirrors CLAUDE.md §4.9 "the judge must be a different agent" and the §2 QA/North Star generator-evaluator split.

3. **Adopt context-loss mitigation = externalize, then re-inject on resume.**
   - *Build implication:* on resume, re-inject SA/SO/SD + the stored goal into the fresh context window, so the session is re-grounded on durable state rather than a drifted transcript (counters catastrophic forgetting + goal misgeneralization, sources 05/07).

## REJECT / DEFER
- **Reject** citing any SagaLLM efficacy *number* — there are none (qualitative case studies only). Adopt the *architecture*; prove efficacy on AutoFirm's own golden suite (branch A9) with real metrics.
- **Defer** the REALM-benchmark specifics; not AutoFirm's domain.
