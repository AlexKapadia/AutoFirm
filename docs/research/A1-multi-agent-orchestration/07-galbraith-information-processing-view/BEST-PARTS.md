# BEST-PARTS — Galbraith 1974 (Information Processing View)

## ADOPT
1. **OIPT as the cited theory behind "protect your context window"** — Galbraith's proposition
   (uncertainty ⇒ more information to process between decision makers) is the **organizational
   analogue of context-flooding** in LLM agents. AutoFirm's orchestrator has finite "information
   processing capacity" (its context window); the empirical token-as-80%-of-variance finding
   (source 02) is the LLM-era confirmation of Galbraith. *Build implication:* this is the L1.A1.4
   theoretical core — cite it as the *reason* AutoFirm decomposes and delegates.
2. **The four strategies, mapped onto AutoFirm primitives** (the key adoptable artifact):
   - **Self-contained tasks** → **scoped subagents with narrow briefs** that act without cross-talk
     (CLAUDE.md §3.1/§4.1). This is the primary lever: reduce coordination need.
   - **Slack resources** → **budget headroom / retries / checkpoints** so transient failures don't
     force re-coordination (ties A3 resume).
   - **Vertical information systems** → the **typed contracts + audit log** that move state reliably
     up to the orchestrator (ties A2/A6).
   - **Lateral relations** → **bounded peer interactions** (e.g. the debate primitive, source 05) used
     sparingly where a subtask genuinely needs cross-agent information.
3. **"Hierarchy + rules handle routine; escalate exceptions upward"** — validates AutoFirm's
   gate-based, rule-driven default with orchestrator escalation only on exceptions (CLAUDE.md §4.2),
   reserving expensive coordination (debate/lateral) for high-uncertainty subtasks.

## REJECT / caution
- **Lateral relations / heavy cross-agent communication as the DEFAULT** — REJECT: Galbraith treats
  lateral relations as the *costliest, last-resort* capacity increase. AutoFirm should prefer
  self-contained tasks first (cheapest), matching source 02's "parallelize independent breadth-first
  work" and source 04's finding that inter-agent interaction is where most failures occur.
- **Direct 1:1 transfer of 1970s mechanisms** — adopt the *abstraction* (4 strategies), not literal
  liaison-role org charts (indirectness caveat).

## Build implication (concrete)
- AutoFirm's coordination policy is an **information-processing budget**: default to *self-contained
  scoped subagents* (reduce need); add *slack* (checkpoints/retries) and *vertical systems* (typed
  contracts + audit) as capacity; invoke *lateral* coordination (bounded debate) only for
  high-uncertainty subtasks. Provides the cited cost model for L2.A1 routing and the L1.A1.4 answer.
