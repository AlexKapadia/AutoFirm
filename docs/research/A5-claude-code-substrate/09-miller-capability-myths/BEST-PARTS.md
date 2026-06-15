# BEST-PARTS — Object-capability theory for AutoFirm's substrate security

## ADOPT (as the theoretical frame for L1.A5.3 design decisions)

- **Model every AutoFirm agent as a capability-scoped subject (POLA).** Claude Code's per-subagent
  `tools`/`disallowedTools`/`mcpServers`/`permissionMode` (source 02) + managed deny-first
  permission rules (source 05) ARE an object-capability-style grant: each agent holds exactly the
  capabilities explicitly handed to it, no ambient authority. Adopt Miller's POLA (claim 4) as the
  explicit design principle: the org engine grants each role the minimal capability set, and
  capabilities are transferable (delegation) and revocable (managed deny / kill-switch).
- **Treat the confused-deputy problem as the named threat the substrate config must prevent**
  (claim 3). In an agent context, a confused deputy = a privileged orchestrator/subagent tricked
  by prompt-injected MCP/document content (source 07) into using ITS authority to do what the
  attacker cannot. Build implication: (a) never give an agent that ingests untrusted external
  content the ambient authority to write/exfiltrate (separate the "reader" capability from the
  "writer/egress" capability across distinct subagents); (b) "no designation without authority"
  (Property A) maps to scoping file/network capabilities to exact paths/domains rather than
  granting broad ambient access — directly justifies the source-05/06 rejection of broad
  `github.com`/`Bash(curl *)` and the path-anchored Read/Edit rules.
- **Aggregate authority by subject (Property C)** — AutoFirm's audit/governance answers "what can
  THIS agent do?" by reading its role file + managed profile, not by scanning every resource.
  This is exactly the per-role capability profile design (source 02/04).

## REJECT / boundary

- **Reject ACL/ambient-authority mental models for agent security.** The paper's core result is
  that ACL + ambient authority cannot prevent confused-deputy attacks. AutoFirm must NOT rely on
  "the agent knows it shouldn't" (prompt/CLAUDE.md instructions) — source 05 confirms the substrate
  "enforces permissions, not the model." Authority is structural, not advisory.
- **Scope note:** this is foundational theory, not Claude-Code-specific; it justifies WHY the
  substrate's capability primitives are the right ones, but the enforceable mechanism details come
  from sources 02/05/06. Don't over-claim that Claude Code is a formally verified ocap system — it
  is an ocap-STYLE enforcement layer with documented gaps (source 06 limitations).

## Concrete build implications
- Contract: each role = a capability profile (tools + paths + domains + spawn rights), least
  authority, revocable via managed deny.
- Design rule (binding): untrusted-input readers and privileged writers/egress are SEPARATE
  capability subjects — never the same agent context (confused-deputy prevention).
- Test: confused-deputy red-team — injected content tries to make a privileged agent act on the
  attacker's behalf; assert the reader role lacks the write/egress capability entirely.
