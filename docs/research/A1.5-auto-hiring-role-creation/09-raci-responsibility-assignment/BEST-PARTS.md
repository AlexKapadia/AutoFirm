# BEST-PARTS - RACI / decision-rights matrices

## ADOPT
1. **Single-accountable-owner rule == the single-writer rule.** RACI's hardest invariant - exactly
   ONE Accountable per item - is the org-theory twin of AutoFirm's single-writer rule (one agent
   owns one artifact/directory). ADOPT RACI as the cited justification: every artifact and every
   decision has exactly one accountable agent; "R"s (workers) may be many, but "A" is unique.
2. **Per-task R/A/C/I tagging as the inter-agent communication contract.** When a manager authors
   a role-spec, it should tag the role's relationship to each task/artifact: who **executes (R)**,
   who **signs off (A)**, who is **consulted (C)** (must be queried before acting), who is
   **informed (I)** (gets an audit notification). ADOPT this as the structured contract feeding
   L2.A2 (agent communication) and L2.A6 (audit: every I-edge is an audit log entry).
3. **RAPID/DACI for the manager's decision rights.** For the *decision* to spawn/retire a role,
   use a RAPID/DACI-style split so AutoFirm encodes WHO recommends a spawn (gap-detector), WHO
   approves it (manager - the human-in-the-loop or senior orchestrator gate), and WHO performs it
   (org-engine). ADOPT decision-rights separation for the spawn/retire gate - prevents an agent
   unilaterally creating roles (fail-closed governance).
4. **Make exclusion explicit (CAIRO "O").** AutoFirm should explicitly record which roles are
   **out-of-loop** for an artifact - reinforcing tenant/scope isolation (no implicit access).

## REJECT
- **Heavyweight matrix ceremony / per-cell RACI for every micro-task.** Overkill for fast agent
  ops. ADOPT the *invariant* (one accountable owner; explicit C/I edges) at the artifact/decision
  level, not a full hand-maintained matrix for every step.

## Build implication
- **Component:** `role-charter.accountability` (RACI tags) + `org-engine/spawn-decision-gate`
  (RAPID/DACI decision rights) + `audit-log` (I-edges become provenance entries).
- **Contract/invariant:** for any owned artifact, `count(Accountable agents) == 1` - the single-
  writer invariant, now RACI-grounded.
- **Test:** property test asserts every artifact in the role registry has exactly one accountable
  owner and that no spawn/retire occurs without a logged approver (decision-rights gate). Feeds an
  `evidence/` "zero ambiguous-ownership" metric.
