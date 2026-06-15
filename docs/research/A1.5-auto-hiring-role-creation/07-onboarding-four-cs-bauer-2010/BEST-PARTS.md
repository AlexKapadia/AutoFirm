# BEST-PARTS - Four Cs of Onboarding (Bauer 2010, SHRM)

## ADOPT
1. **The Four Cs as AutoFirm's concrete onboarding checklist (agent-translated):**
   - **Compliance** -> provision the agent's **scoped credentials, tools, permissions, and the
     governance rules** it must obey (least-privilege, fail-closed, audit). This is the
     security-by-default onboarding step (ties to A7/A8). MANDATORY first.
   - **Clarification** -> deliver the **charter** (role, scope, success signal) and obtain the
     RoleReceived ack = role clarity (ties to sources 04, 06).
   - **Culture** -> load the **standing rules of the workspace** (CLAUDE.md, the program docs,
     single-writer + must_study rules, naming/structure conventions) so the agent acts in-norm.
     This is the literal `must_study` content.
   - **Connection** -> register the agent in the **role registry** and establish its
     communication contracts with its role set (who it reports to, who consumes its outputs).
2. **The passive->proactive levels as a maturity model.** AutoFirm should run **proactive
   onboarding (all four Cs)** by default, not compliance-only. ADOPT the levels as an explicit
   quality bar: a spawn that only provisions credentials (Compliance) but skips Clarification/
   Culture/Connection is a *passive* (defective) onboarding.
3. **Culture-C justifies the `must_study` rule directly.** The "Culture" C is the cited
   organizational-theory grounding for AutoFirm's `must_study` requirement: newcomers must absorb
   norms/values before acting. ADOPT must_study as the Culture-C implementation.

## REJECT
- **Affective/relational depth of "Connection" (belonging, friendship networks).** For agents,
  Connection reduces to **functional addressability** (can reach role set) + registry membership.
  REJECT the social-belonging interpretation; keep the structural one.

## Build implication
- **Component:** `org-engine/onboarding` runs a 4-stage pipeline:
  `Compliance(credentials+rules) -> Clarification(charter+ack) -> Culture(must_study) ->
  Connection(registry+role-set handshake)`, in order, each a hard gate.
- **Contract:** onboarding status is the highest contiguous C reached; only `Connection`-complete
  agents may take task actions.
- **Test:** each C is an independent gate with a deterministic pass/fail; an `evidence/` chart
  reports the distribution of onboarding completeness (target: 100% reach Connection).
