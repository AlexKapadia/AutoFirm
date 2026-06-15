# BEST-PARTS — Arntz/OECD → AutoFirm

## ADOPT
- **The core design principle for ALL of B2: AUTOMATE TASKS, NOT JOBS.** This source is the
  evidence that justifies AutoFirm's entire decomposition strategy — the same role automates very
  differently depending on its *task mix*. **Build implication:** AutoFirm never assigns "automate
  the accountant"; it decomposes to APQC Tasks and scores each. The 9%-vs-47% gap is the
  quantified cost of getting the unit-of-analysis wrong, and is the single most important
  guardrail against AutoFirm over-claiming automation.
- **Intra-occupation task heterogeneity** → AutoFirm's per-client decomposition must be
  *data-driven per company*, not template-driven per job title. Two clients with the same nominal
  role can have completely different automatable surfaces. This forces the decomposition engine to
  read *actual* client process data (ties to L1.B4.4 public-data sourcing).
- **The explicit "technical ≠ actual" caveat** is the citable basis for AutoFirm's mandatory
  business-case + compliance gate before automating (reinforces the McKinsey REJECT note).

## REJECT / use-with-care
- **Reject neither figure as "the truth" — report the RANGE with the method.** AutoFirm's evidence
  showcase should present 9% (task-based) and 47% (occupation-based) as a *methodology-dependent
  band*, not pick one. The honest, citable claim is: "automation potential depends critically on
  the unit of analysis; AutoFirm operates at the task level (the lower-bound, more-defensible end)."
- **Use-with-care: PIAAC is pre-LLM (2012 survey).** Like MGI/Frey-Osborne, the absolute numbers
  predate generative AI and understate current cognitive-task automatability; the *method lesson*
  (task-level) is durable, the *level* is not — update with source 09.

## Concrete build implication
- Component: enforced in `function_decomposition/` — the engine's lowest assignable unit is an APQC Task; a lint/contract test forbids assigning automation at the occupation/role level.
- Test it drives: a regression test that two clients sharing a job title but differing in task mix receive *different* automation plans (proving task-level, not title-level, decomposition — kills any template-overfit mutant).
