# BEST-PARTS — LegalBench

## ADOPT
- **A1. IRAC as the decomposition contract for the legal playbook.** AutoFirm's L2.B10 legal tasks are
  structured as **Issue → Rule → Application → Conclusion** stages, mirroring LegalBench's six categories.
  This lets each legal output **explain itself** (CLAUDE.md §3.11): the "Rule" stage cites the controlling
  statute, "Application" shows the facts, "Conclusion" states the verdict — auditable and gradeable.
- **A2. Capability-aware escalation policy.** Because LLM legal performance is **uneven by reasoning
  type**, the playbook must **not** treat all legal tasks as equally automatable. Adopt a tiered rule:
  rule-recall / issue-spotting → high-confidence automatable; **multi-step rule-application and
  interpretation → require human-in-the-loop sign-off** (CLAUDE.md §2 HITL gate). This is a direct,
  evidence-backed build decision, not a guess.
- **A3. LegalBench-style internal eval harness.** Build a held-out, expert-validated legal-reasoning
  eval set for AutoFirm's own legal agent, scored per IRAC stage, feeding `evidence/` with accuracy +
  CIs per category (CLAUDE.md §3.6 efficacy tests, §3.10 showcase).

## REJECT / DEFER
- **R1. REJECT relying on LLM legal reasoning for any fail-closed control.** The benchmark shows
  competence is partial; therefore deterministic rules (entity, contract-formation, secrecy gates from
  sources 01-04/06) own the must-never-fail decisions, with the LLM as a *soft layer* that drafts and
  explains within those guardrails (CLAUDE.md §3.5 hybrid). Never let a model's interpretation override
  a hard legal guardrail.
- **R2. DEFER citing specific 2023 per-model accuracy figures** into the live system — they are dated;
  re-benchmark against current models before quoting any number.

## Build implication (concrete)
- **Component:** `legal/reasoning/irac_pipeline.py`; `legal/reasoning/escalation_policy.py`.
- **Contract:** `LegalAnalysis{ issue, rule_cited, application, conclusion, reasoning_type, confidence,
  requires_human_signoff: bool }`.
- **Test (efficacy):** score the legal agent on a held-out IRAC eval set; assert escalation fires for
  interpretation/rule-application tasks; assert the "rule_cited" field is non-empty and resolves (no
  hallucinated statute — ties to DEPTH-RUBRIC §3 anti-fabrication, applied at runtime).
