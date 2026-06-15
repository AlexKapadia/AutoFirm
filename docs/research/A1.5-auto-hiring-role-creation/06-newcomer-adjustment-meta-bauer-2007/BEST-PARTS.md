# BEST-PARTS - Newcomer Adjustment Meta-Analysis (Bauer et al. 2007)

## ADOPT
1. **Onboarding success == the three adjustment indicators, made measurable for agents.** AutoFirm
   should define agent onboarding "done" by agent analogues of the three empirically-validated
   mediators:
   - **Role clarity** -> the agent correctly restates its scope/charter (the RoleReceived ack;
     ties to Katz & Kahn source 04). Measurable: ack matches charter.
   - **Self-efficacy** -> the agent confirms it has the tools/skills/permissions to act (a
     capability self-check) before first action. Measurable: capability pre-flight passes.
   - **Social acceptance** -> the agent's communication contracts with its role set are
     established (it can reach its dependencies and is registered as the single-writer). Measurable:
     handshake with role set succeeds.
   ADOPT these three as the **onboarding Definition-of-Done** for a spawned agent - cited, not
   invented.
2. **Mediation insight: tactics only work THROUGH adjustment.** Don't just run an onboarding
   procedure and assume it worked; **verify the adjustment outcome** (role clarity / efficacy /
   acceptance achieved). ADOPT a post-onboarding verification gate, not a fire-and-forget step -
   this is the empirical justification for an onboarding *assertion*, not just an onboarding
   *action*.
3. **Role clarity is the first and most controllable lever.** Of the three, role clarity is the
   one AutoFirm fully controls via the charter. ADOPT: prioritise unambiguous charters (source 03
   completeness + source 04 ambiguity check) as the highest-leverage onboarding investment.

## REJECT
- **The human-motivation outcomes (job satisfaction, commitment, intention-to-remain).** These are
  affective human states with no agent analogue. REJECT as agent targets; keep only **performance**
  (task success) and the three *structural* adjustment mediators.

## Build implication
- **Component:** `org-engine/onboarding-verifier`.
- **Contract:** `OnboardingComplete = role_clarity_ok AND self_efficacy_ok AND social_acceptance_ok`
  where each is a concrete check (ack-matches-charter; capability-preflight-pass; role-set-handshake-pass).
- **Test:** spawning an agent with a malformed charter, missing tools, or an unreachable role set
  must FAIL the respective check and block first action - three deterministic, unit-testable gates,
  feeding an `evidence/` onboarding-success-rate metric (target 100% on well-formed charters).
