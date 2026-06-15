# BEST-PARTS — Donaldson Contingency / SARFIT

## What AutoFirm ADOPTS

1. **SARFIT is the formal model for AutoFirm's dynamic-org engine and the North Star loop.** The
   agent company is not designed once — it must continuously detect misfit and re-adapt. SARFIT
   gives the exact loop: *in fit -> contingency changes (goal/scope/scale shifts) -> misfit ->
   performance drops -> structural adaptation (re-scope/spawn/retire agents) -> back in fit.*
   - **Build implication:** L2.ORG runs a SARFIT cycle; the **North Star alignment review**
     (CLAUDE.md §2, ~30 min) is literally the misfit-detection step; a RED grade = detected misfit
     = mandatory structural adaptation before new work.

2. **Contingency variables are the engine's inputs.** size, strategy/diversification, task
   uncertainty (technology), environment. AutoFirm measures proxies for each (agent count = size;
   goal complexity = task uncertainty; client industry = environment) and adapts structure when any
   crosses a threshold.
   - **Build implication:** the dynamic-org engine watches these proxies and triggers re-design
     (spawn sub-orchestrators when size grows, etc.) — turning span-caps (source 06) into rules.

3. **"No one best way" — the anti-overfitting theorem.** Donaldson's central claim is the
   theoretical guarantee that AutoFirm CANNOT ship one fixed org/business template; the design must
   be contingent. This is the deepest justification for CLAUDE.md §3.9 (generality) and the B12
   fixed-industry-panel test.

4. **Fit -> performance is empirically grounded.** AutoFirm can treat "improve fit -> improve
   measured task success" as a falsifiable, testable hypothesis in evidence/ (not a vibe).

## What AutoFirm REJECTS / caution
- **Reject permanent structures.** Any "set it and forget it" org spec violates SARFIT; the engine
  must keep the adaptation loop live.
- Caution: SARFIT predicts adaptation **lags** (orgs tolerate misfit before reacting). AutoFirm
  should make the lag short and *automatic* (heartbeat-driven), beating the human-org lag — a
  concrete advantage to demonstrate in evidence/.
- Caution: don't over-react to transient noise as "misfit" — require a sustained signal (debounce)
  before triggering costly re-design.

## Quantification for evidence/
- **Misfit-detection latency:** time from contingency-change to structural adaptation. Target:
  bounded by the heartbeat interval. Chart vs. (slow) human-org baselines from the literature.
- **Fit-performance curve:** measured task success vs. a computed fit score across panel scenarios —
  expected positive slope validates the whole adaptive-org thesis.
