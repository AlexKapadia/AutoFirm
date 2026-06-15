# BEST-PARTS — Anthropic Multi-Agent Engineering

## What AutoFirm should ADOPT and why (substrate-specific: this is the Claude runtime)

1. **The four-part delegation contract on EVERY task message.** ADOPT: every orchestrator->agent
   message carries {objective, output format, tools/sources guidance, clear task boundaries}.
   Build implication: these become *required fields* in AutoFirm's task envelope (source 01/04).
   Missing any -> refuse to dispatch (fail-closed). This is the empirically-validated fix for
   "subagents misinterpreted the task / did duplicate work" — i.e. MAST FC1+FC2 (source 02).

2. **Store-and-reference, not copy-through (anti-telephone).** ADOPT: subagents persist large
   outputs to external storage and pass lightweight references back; the orchestrator never
   re-expands full transcripts into its own context. Build implication: directly implements
   CLAUDE S3.1/S4.1 (protect the orchestrator's context; compact results) and mitigates
   context-loss-during-handoff (FC2). Drives the A4/A8 artifact-store contract.

3. **A dedicated verification/citation pass as a separate agent.** ADOPT a separate
   verifier/citation agent after synthesis. Build implication: maps to MAST FC3 (verification) —
   make verification a distinct flow step + role, not an afterthought (links source 02, S3.7).

4. **Durable resume, not restart-from-zero.** ADOPT externalized state so long runs resume from
   the last checkpoint; persist the plan to memory before the 200k-token truncation boundary.
   Build implication: the A2 flow must emit durable, resumable state at each step boundary ->
   feeds A3 (handoff/resume) and the §4.8 watchdog auto-resume.

## What AutoFirm should REJECT / weigh

- **WEIGH the 15x token cost.** Multi-agent uses ~15x tokens vs chat; token usage explains ~80%
  of performance variance. Build implication: AutoFirm must budget/meter tokens per flow and only
  fan out when the task justifies it (CLAUDE S4.3 "parallelise only genuinely independent work").
  This is a quantified guardrail, not a free lunch.
- **REJECT spawning subagents without the delegation contract** — the post shows this directly
  causes duplicate/misinterpreted work.

## Concrete build implication / quantified targets
- A2 task envelope REQUIRES the 4 delegation fields; A2 results use store-and-reference.
- Golden-metric inputs for L2: target measurable multi-agent uplift vs single-agent baseline
  (Anthropic saw +90.2% on their eval) while keeping the ~15x token cost inside a budget.
- Resume target: a killed flow resumes from last checkpoint, not from start (A3 acceptance test).
