# BEST-PARTS — AI Kill Switch (AutoGuard)

## ADOPT
1. **The quantified before/after as AutoFirm's kill-switch efficacy target.** ASR 78% -> 9.1% and DSR ~81% are concrete, citable numbers for the `evidence/` showcase when AutoFirm demonstrates its own halting mechanism (CLAUDE.md §3.10). *Build:* report AutoFirm's ASR-with-kill-switch vs undefended.
2. **The kill-switch *requirements* (from corroborating Galileo/CodeX analysis), not AutoGuard's specific HTML trick:** an internal kill-switch must provide **immediate stop + state capture + immutable logging**, plus **rollback and quarantine** to revert changes and isolate the agent after interrupt. *Build:* AutoFirm's single kill-switch config flag (CLAUDE.md §5.6) does: (a) halt all external calls atomically, (b) snapshot state for resume/audit, (c) write the halt event to the append-only log (A6), (d) quarantine the offending agent's outputs.
3. **Pre-execution gates + layered shutdown (from CodeX analysis).** A single post-hoc kill switch is insufficient for multi-step plans across sub-agents; use *pre-execution* gates and *layered* shutdown + real-time scope enforcement. *Build:* AutoFirm gates BEFORE each privileged action (not only after), and the kill-switch propagates to all live subagents.

## REJECT / DEFER
- **Reject AutoGuard's specific mechanism as AutoFirm's internal kill-switch.** AutoGuard relies on the *target* agent being externally-aligned and on hiding prompts in HTML — that is a defense against *third-party* malicious agents crawling your site, NOT a way to control your *own* trusted-but-possibly-compromised agents. AutoFirm needs a *deterministic, out-of-band* kill-switch (a control-plane flag the agent cannot overwrite), per the CodeX warning "kill switches don't work if the agent writes the policy."
- **Defer the bandit-optimized prompt approach** — probabilistic and model-dependent; AutoFirm's halt must be deterministic and fail-closed.

## Concrete build implications
- Sharpens the **A7 kill-switch contract**: out-of-band, deterministic, agent-cannot-disable, with state-capture + immutable logging + quarantine + rollback; pre-execution gates + propagation to all subagents.
- The **"agent must not write its own kill policy"** constraint is a hard fail-closed invariant linking A7 -> A6 (audit) and A8.3 (secrets/credential scoping: the kill-switch credential is never in agent scope).
