# BEST-PARTS — Long-Horizon Task Mirage

## ADOPT (this is the threat model for AutoFirm's resume protocol)
1. **Adopt the 7-category failure taxonomy as the explicit checklist the handoff/resume protocol must defend against.**
   - *Build implication:* each category maps to a concrete control in the L2.A3 resume protocol:
     - *Catastrophic Forgetting [L]* + *Memory Limitation [L]* => **externalize constraints/goals into a durable, re-injected state object** (not left only in the volatile context window) — ties to sources 08–10 (checkpoint state) and branch A4 (memory).
     - *History Error Accumulation [L]* => **checkpoint + validate at milestones** so early errors are caught before they compound (source 06 AgentDebug; source 10 SagaLLM independent validation).
     - *False Assumption [S]* => the resume payload re-states *verified* task state, forcing re-grounding on resume (counters confirmation-bias drift).
     - *Planning Error [S]* => keep the plan/roadmap as a durable artifact re-loaded on resume (CLAUDE.md §4.8 "resume state comes from git, the task list, and the roadmap doc").

2. **Adopt the "process-level dominates (72.5%)" finding to prioritize engineering effort.**
   - *Why:* most long-horizon failures are *process* (orchestration/state-management) not *design* (model capability). This validates AutoFirm's core bet: better orchestration + state externalization beats waiting for bigger models.
   - *Build implication:* invest the resume protocol budget in checkpointing/validation/state-re-injection, not in prompt-tuning the base model.

3. **Adopt the "scaling won't fix it -> architectural solution" conclusion** as the mandate for an explicit checkpoint/resume architecture (L2.A3), rather than hoping longer context windows solve drift.

## REJECT / DEFER
- **Defer** the per-domain breaking-point numbers (web vs. embodied) — AutoFirm's domains differ; re-measure on AutoFirm's own task suite (branch A9) rather than importing these thresholds.
- **Reject** treating any single category as sufficient: the taxonomy is used as a *complete* checklist; partial coverage is an overfit risk (DEPTH-RUBRIC §6).
