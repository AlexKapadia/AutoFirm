# BEST-PARTS — Rollback-Recovery Survey (Elnozahy et al.)

## ADOPT (the checkpoint-design decision menu for L2.A3)
1. **Adopt COORDINATED checkpointing as AutoFirm's default resume mechanism — explicitly to avoid the domino effect.**
   - *Why:* uncoordinated checkpointing risks cascading rollbacks (the domino effect) and useless checkpoints. AutoFirm's gates (§4.2) are natural coordination points: checkpoint the whole workflow state at each green gate => a single, consistent recovery line, no cascade.
   - *Build implication:* the resume protocol checkpoints a **consistent global state at every gate** (git commit + task-list + roadmap doc + memory snapshot — matches CLAUDE.md §4.8). Recovery = roll forward from the last gate, never a cascading multi-agent rollback. Determinism test: resuming from a checkpoint reproduces the same downstream state (§5.5).

2. **Adopt the piecewise-deterministic (PWD) + event-logging idea for sub-gate resumability.**
   - *Why:* between gates, an agent does many nondeterministic steps (LLM calls, tool results). Logging those events lets a crashed session replay to its exact pre-failure point without re-running completed side-effecting work — exactly the durable-execution model.
   - *Build implication:* the audit log (branch A6.2) doubles as the **replay log**: each tool call + result is recorded with an **idempotency key** so replay does not duplicate side effects (the durable-execution rule). Ties PWD theory directly to A6 append-only logging.

3. **Adopt "consistent global state = no orphan messages" as the checkpoint-validity invariant.**
   - *Build implication:* a checkpoint is only valid if no agent has "received" a delegated result whose producing step is not itself checkpointed — a testable invariant on the saved state graph.

## REJECT / DEFER
- **Reject** pure **uncoordinated** checkpointing as the default (domino-effect risk) — allowed only for fully-independent, side-effect-free leaf subagents.
- **Defer** message-logging optimizations (causal vs. pessimistic vs. optimistic logging) to L2.A3 implementation; the *family choice* (coordinated + logged) is the L1 decision.
