# BEST-PARTS — Mintzberg's Configurations

## What AutoFirm ADOPTS

1. **The five coordinating mechanisms are AutoFirm's coordination primitive set.** They map almost
   1:1 onto agent-orchestration primitives:
   - *Direct supervision* = orchestrator dispatching/monitoring subagents (the default).
   - *Standardization of outputs* = **typed output contracts** between agents (A2) — coordinate by
     agreeing on the result shape, not by chatting. **AutoFirm's primary mechanism at scale.**
   - *Standardization of work processes* = slash-commands / skills / fixed workflows (DAGs).
   - *Standardization of skills* = preloaded skill-profiles per subagent (progressive disclosure).
   - *Mutual adjustment* = free-form agent-to-agent negotiation — powerful but **does not scale**
     (Mintzberg: only viable in small/adhocratic settings), so AutoFirm should bound it.
   - **Build implication:** the org engine selects a coordinating mechanism per unit; "standardize
     outputs" is preferred as the org grows (this is the org-theory<->MAS bridge, L1.A2.3).

2. **"Standardize outputs to scale" is the central scaling lesson.** Mutual adjustment is cheap with
   few agents and explodes with many (cf. Graicunas, source 06). To scale the agent company,
   AutoFirm must shift coordination from mutual adjustment -> standardized outputs/skills as agent
   count rises. This is a concrete, testable scaling rule.

3. **Configurations as a contingency menu for client orgs.** When AutoFirm designs a *client*
   company, the configuration is chosen by the work's nature:
   - Startup/early -> **Simple Structure** (direct supervision).
   - High-volume manufacturing/back-office -> **Machine Bureaucracy** (standardized processes).
   - Consulting/hospital/law (expert work) -> **Professional Bureaucracy** (standardized skills).
   - Multi-product/multi-geography corporation -> **Divisionalized Form** (standardized outputs).
   - R&D / creative / novel problems -> **Adhocracy** (mutual adjustment).
   - **Build implication:** L2.B2 maps an industry-panel row -> a Mintzberg configuration as the
     starting structure, then refines via the Star (source 02).

4. **The six basic parts = role inventory for the agent org.** strategic apex (orchestrator),
   middle line (sub-orchestrators / domain leads), operating core (IC subagents), technostructure
   (the agents that standardize: QA, test-design, schema-design), support staff (tooling/MCP),
   ideology (CLAUDE.md itself). Useful as a completeness checklist for org design.

## What AutoFirm REJECTS / caution
- **Reject mutual adjustment as a scaling strategy.** Keep it for tiny, high-uncertainty pods only.
- **Reject rigid Machine-Bureaucracy defaults for creative/novel work** — it suppresses the
  adaptation high-uncertainty client builds need (matches Galbraith OIPT, source 01).
- Caution: real orgs are *hybrids* of configurations (Mintzberg acknowledges this) — AutoFirm
  should allow blended configurations, not force a single pure type (CLAUDE.md §3.5 hybrids).

## Quantification for evidence/
- **Coordination-mechanism-vs-scale curve:** measured coordination overhead under "mutual
  adjustment" vs. "standardized outputs" as agent count grows — expected crossover demonstrates the
  scaling rule (ties to Graicunas, source 06). Headline scaling chart for L2.ORG.
