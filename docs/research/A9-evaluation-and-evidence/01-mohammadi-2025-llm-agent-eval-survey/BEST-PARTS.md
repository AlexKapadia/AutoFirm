# BEST-PARTS — Mohammadi et al. 2025 (LLM Agent Eval Survey)

## ADOPT

1. **The two-axis eval taxonomy as the spine of AutoFirm's eval harness (L2.A9).**
   Structure the platform's self-evaluation along (WHAT) Behavior / Capabilities / Reliability /
   Safety & Alignment and (HOW) Interaction-mode / Data / Metrics-computation / Tooling / Context.
   *Build implication:* the eval-harness module gets one test-suite namespace per WHAT-axis cell;
   the CCO/North-Star alignment review (CLAUDE.md §2) grades Reliability and Safety as first-class,
   not as an afterthought.

2. **`pass^k` (all-of-k succeed) as AutoFirm's reliability gate, not `pass@k`.**
   AutoFirm runs *mission-critical, unattended* company-building. The survey explicitly recommends
   `pass^k` for "mission-critical deployments." *Build implication:* every deterministic/critical
   workflow step must hit a high `pass^k` over repeated runs (ties directly to CLAUDE.md §3.6
   determinism tests and §3.13 "verified increment"). `pass@k` is acceptable only for exploratory
   generation steps where one good candidate suffices.

3. **Separate code-based from LLM-as-Judge metrics; never let a judge grade a deterministic path.**
   *Build implication:* deterministic outputs (financial-model arithmetic, audit-log invariants)
   are graded code-based/exact (CLAUDE.md §3.11 zero numerical errors); only open-ended artifacts
   (deck narrative, marketing copy) may use an LLM/Agent-as-Judge -- and the judge must be a
   *different* agent (generator/evaluator split, CLAUDE.md §4.9.5).

4. **Adopt the "enterprise blind spots" list as mandatory eval dimensions.**
   Predictable reliability, regulatory compliance, data security, maintainability -- exactly the
   institution-grade bar (CLAUDE.md §3.2). *Build implication:* these become explicit gate checks,
   not optional.

## REJECT / DEFER

- **REJECT** treating any single agent-benchmark (SWE-bench, WebArena, etc.) as AutoFirm's
  acceptance criterion. They evaluate narrow tasks; AutoFirm builds *whole companies*. Use them as
  *capability spot-checks* feeding evidence/, not as the bar. Rationale: CLAUDE.md §3.9 (generality
  over scenario-fit) -- a public benchmark is one scenario.
- **REJECT** LLM-as-a-Judge as a sole oracle for correctness-critical outputs (survey notes
  AST-based checks "may miss semantic errors"; judges add their own variance). Use only as a
  *secondary* signal corroborated by code-based checks.
- **DEFER** TheAgentCompany / tau-benchmark integration to L2 -- useful as an external comparator
  once the internal harness exists.

## Why this matters to AutoFirm
This survey is the canonical map of *what an agent-eval harness must cover*. It directly shapes
L2.A9 (eval-harness design) and the CCO heartbeat, and it supplies the `pass^k` reliability
concept that hardens CLAUDE.md's "verified increment" and determinism requirements.
