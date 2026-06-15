# BEST-PARTS - New Horizons Socialization Meta-Analysis (Bauer et al. 2025)

## ADOPT
1. **Confirms the three-indicator onboarding DoD (role clarity, self-efficacy, social
   acceptance) with current peer-reviewed evidence** - giving source 06's adopted DoD a second,
   independent High-tier anchor. ADOPT with confidence; the agent-onboarding gates (clarity ack /
   capability preflight / role-set handshake) are now doubly-cited.
2. **Elevate "social acceptance" -> functional connectedness as a first-class onboarding gate, not
   an afterthought.** The 2025 evidence makes social acceptance *central*. For agents this maps to
   **role-set integration**: the agent must be reachable by and able to reach its dependencies, be
   registered as the single-writer, and have its handoff/communication contracts live BEFORE it
   acts. ADOPT a strict "no work until connected" rule - this is now the empirically-central
   onboarding lever, not the weakest.
3. **Adaptability / agency for exploratory roles.** For experiment/research agents, structure
   onboarding to permit **managed ambiguity** (the individualized profile, source 05) so the agent
   can redefine its approach - the 2025 paper's "agency/adaptability" point justifies offering
   BOTH institutionalized and individualized onboarding profiles per role type.

## REJECT
- **Remote/hybrid human-connection interventions (virtual coffee, buddy programmes, belonging
  initiatives).** No agent analogue. REJECT the human-relational program design; translate
  "connection" strictly to **machine addressability + registry membership + contract liveness**.

## Build implication
- **Component:** reinforces `org-engine/onboarding-verifier`; bumps the **social_acceptance gate**
  (role-set handshake + registry single-writer registration) from optional to MANDATORY before
  first action.
- **Test:** an agent whose role-set is unreachable, or whose single-writer claim conflicts with an
  existing owner, FAILS the connection gate and is blocked - deterministic, audited, and the
  highest-weighted onboarding check per the 2025 evidence.
