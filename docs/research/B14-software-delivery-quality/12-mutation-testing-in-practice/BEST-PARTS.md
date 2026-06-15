# BEST-PARTS — Mutation testing in practice (tooling)

## ADOPT
1. **Production tool selection per language.** Adopt **PIT** (Java/JVM), **Stryker** (JS/TS/C#/Scala), **mutmut**/**cosmic-ray** (Python), **Infection** (PHP) — the tools empirically used in *active* (not just teaching) repos. AutoFirm's mutation gate (source 01) wires the language-appropriate tool automatically.
2. **Incremental mutation to control cost.** The dominant adoption blocker is runtime cost. AutoFirm runs **changed-files-only / incremental mutation per PR** (most tools support this) with a **full-suite mutation run at release gates**, plus parallelism — making the CLAUDE.md §3.6 mutation discipline affordable at company scale.
3. **Mutation as a TDD/quality driver.** Use surviving mutants as the concrete worklist for the iterate-to-perfection loop: each survivor on a critical module spawns a "write a harder test" task until killed.

## REJECT
- Reject literature-only / unmaintained mutation tools (appear mostly in teaching repos) for production client delivery.
- Reject full-suite mutation on every commit (cost-prohibitive) — use incremental + release-gate strategy instead.

## Concrete artifact this drives
- The mutation-gate implementation: per-language tool registry + incremental-mode config for PR gates + full-run config for release gates + survivor-to-task automation feeding the test generator and the `evidence/` mutation-score chart.
