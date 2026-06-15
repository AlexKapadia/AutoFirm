# BEST-PARTS — Deterministic vs Dynamic Orchestration

## What AutoFirm should ADOPT and why

1. **Declared, deterministic DAG topology as the DEFAULT flow substrate.** ADOPT: workflow
   topology is "declared, not discovered at runtime"; routing is deterministic and "consumes
   zero tokens"; the LLM "operates only within individual agent nodes." Build implication: the
   A2 flow engine = an inspectable, version-controlled DAG of typed stages; routing between
   stages is code, not an LLM decision. This is cheaper, auditable, and reliable — and it is the
   org-theory "standardization of work processes/outputs" (source 06) realized in software.

2. **Reserve LLM-driven / emergent routing for genuinely exploratory work.** ADOPT the explicit
   tradeoff: deterministic for "known structure" (most of AutoFirm's gated phases, CLAUDE S4.2);
   dynamic (CNP-style negotiation, source 05) only when the path is unknown at design time. Build
   implication: hybrid flow engine — deterministic DAG core + bounded dynamic delegation, chosen
   by task type (matches Mintzberg contingency, source 06; CLAUDE S3.5 prefer hybrids).

3. **Inspectability/auditability as a first-class property.** ADOPT: routing must be
   human-readable and auditable. Build implication: every flow is a serializable, diffable graph
   feeding the A6 audit trail — serves A2's "audited inter-team comms" priority directly.

## What AutoFirm should REJECT

- **REJECT LLM-as-orchestrator for structured, repeatable flows.** Justified by the quoted
  cost/latency/unpredictability triad AND by MAST: specification/design failures are the single
  largest category (41.77%, source 02) and non-deterministic routing is "harder to audit and
  control." Don't pay tokens + unpredictability for routing that can be declared.
- **REJECT pure-emergent (all mutual-adjustment) coordination at scale** — corroborated failure
  mode (FC2 36.94%, source 02; Mintzberg adhocracy-doesn't-scale, source 06).

## Concrete build implication / golden-metric framing
A2's coordination model = **deterministic DAG by default, dynamic (Contract-Net) only where the
path is unknown**. This is the contested L2 choice to settle on `experiment/*` branches
(CLAUDE S3.4/S4.5): candidates = {deterministic-DAG, LLM-orchestrated, hybrid}, measured on a
golden flow set for (a) task success, (b) tokens, (c) auditability, (d) MAST-FC2 failure rate.
Hypothesis (to test, not assume): hybrid wins; deterministic-DAG beats LLM-routed on cost +
auditability for structured flows.
