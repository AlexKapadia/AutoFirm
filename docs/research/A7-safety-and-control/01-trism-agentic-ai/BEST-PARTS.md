# BEST-PARTS — TRiSM for Agentic AI

## ADOPT
1. **The AMAS risk taxonomy as AutoFirm's canonical threat catalogue (A7 threat model).** Adopt the five threat classes verbatim as the spine of AutoFirm's threat model doc (CLAUDE.md §5.6 STRIDE-style model): **prompt injection, memory poisoning, collusive failure, emergent misbehavior, tool-use abuse.** *Why:* AutoFirm is itself an LLM-based MAS (orchestrated Claude Code sessions) — this is the exact system class the survey covers, so the taxonomy is directly indicative (no indirectness down-rate). *Build implication:* each class becomes a row in `docs/threat-model.md` with a fail-closed control and a red-team test (DEPTH-RUBRIC §5 — must be testable).
2. **Lifecycle-governance-as-cross-cutting-pillar.** Treat governance/audit not as one module but as a property spanning every agent's lifecycle (spawn → act → retire) — aligns with branch A6 and CLAUDE.md §5.6 append-only audit. *Build implication:* the audit log must cover the *whole* agent lifecycle, not just tool calls.
3. **CSS / TUE as candidate platform-eval metrics.** Component Synergy Score and Tool Utilization Efficacy feed AutoFirm's `evidence/` showcase and branch A9 (platform eval). *Build implication:* expose per-orchestration CSS/TUE telemetry as evidence charts.

## REJECT / DEFER
- **Reject sole reliance on its numeric/efficacy claims.** As a review it aggregates others' numbers; any AutoFirm decision needing a quantitative threshold must cite the *primary* study (e.g. AgentDojo for prompt-injection defense rates — see source 06). Use TRiSM for *structure*, not for sole numbers.
- **Defer the CSS/TUE formulae** until the exact definitions are read from the published version (the abstract names them but the precise formula needs the journal PDF) — do not implement a guessed formula (zero-fabrication rule).
- **Reject "encryption + compliance" as sufficient controls.** The survey lists these at a high level; AutoFirm needs the concrete fail-closed/least-privilege mechanisms from sources 05, 09, 10 — TRiSM motivates *what* to defend, those sources give *how*.

## Concrete build implications
- Drives the **A7 threat-model contract**: a typed enum of threat classes each agent-action is screened against.
- The **memory-poisoning** row links A7 ↔ A4.4 (memory security) — cross-branch dependency to flag in synthesis.
- The **collusive-failure / emergent-misbehavior** rows are *MAS-specific* and justify the oversight architecture (audit agents, source 07) over single-agent safety alone.
