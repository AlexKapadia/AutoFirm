# BEST-PARTS — Tran et al. 2025 (Collaboration Mechanisms Survey)

## ADOPT
1. **The three-axis taxonomy as AutoFirm's coordination vocabulary** — (TYPE: cooperation /
   competition / coopetition) × (STRUCTURE: centralized / decentralized / hierarchical) ×
   (STRATEGY: rule-based / role-based / model-based). *Build implication:* AutoFirm's org engine
   (L2.ORG) is a **hierarchical + role-based + cooperative** system; this survey gives the cited
   coordinate that names that choice and its alternatives.
2. **Hierarchical = "low bottleneck, tasks distributed across levels"** — direct support for a
   COO/CTO-style hierarchy over a single mega-agent. *Implication:* the orchestrator-worker tree in
   CLAUDE.md §2/§4.1 is the survey's hierarchical structure; cite this for the design-decision record.
3. **Failure-mode hooks** — "one agent's failure can be amplified" and "central-agent failure causes
   collapse" → AutoFirm needs (a) per-agent verification gates and (b) no single un-backed-up
   orchestrator (kill-switch + resumable state, ties to A3/A7).

## REJECT / not-adopt
- **Decentralized peer-to-peer as the primary topology** — REJECT: survey flags "high communication
  overheads"; AutoFirm needs auditability and a single accountable decision-owner (CLAUDE.md §2),
  which a flat P2P mesh undermines.
- **Competition / coopetition as the default mode** — REJECT for internal org coordination (use
  cooperation); RETAIN narrowly for the **branch-per-experiment** evaluation (CLAUDE.md §3.4), which
  is a controlled competition between approaches judged on a golden set, not free-running rivalry.

## Build implication (concrete)
- Drives the **orchestration-topology design-decision record** for L2.A1: chosen coordinate =
  *hierarchical / role-based / cooperative*, with decentralized-P2P and competition explicitly
  rejected-with-reason. The named failure modes become **required test cases** in A9 (fault
  amplification, orchestrator-failure recovery).
