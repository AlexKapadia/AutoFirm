# BEST-PARTS — Electronic agents / attribution (the most AutoFirm-critical source)

## ADOPT
- **A1. "The deployer is bound" is a foundational design axiom.** Under UETA §14 / E-SIGN §7001, when
  AutoFirm's agent forms a contract, **the operating company (deployer/user), not the agent, is the
  legally bound party.** Every contract-executing capability must therefore (a) record the **authorizing
  principal** and (b) prove the action was **within granted authority** — because liability flows to that
  principal. Build implication: a mandatory `authorizing_principal` + `authority_scope` on every
  contract action; absent or out-of-scope → **refuse** (fail-closed).
- **A2. Bound the agent's authority explicitly ("decision perimeter").** The legal gap is that
  autonomy can exceed the user's specific intent. AutoFirm closes it with **explicit, machine-readable
  authority limits** (max contract value, allowed counterparties, allowed deal types) checked
  deterministically before any "accept". This is the legal twin of the §3.5 hard-guardrail core and
  directly answers the apparent-authority risk.
- **A3. Human sign-off gate above a threshold.** For material contracts (value/risk over a configured
  threshold) require **HITL approval** (CLAUDE.md §2) — the audit log then shows the human authorization
  that makes attribution clean. Ties to source 07's "human sign-off on material decisions" recommendation.

## REJECT / DEFER
- **R1. REJECT any design that lets the agent self-grant authority or form a contract without a recorded
  principal + scope.** That is the precise failure mode UETA's "programming and use" gap warns about.
- **R2. DEFER apparent-authority edge cases** (where a counterparty reasonably believed authority existed)
  to a risk-register flag + legal-review escalation — the doctrine is unsettled (Proskauer Part III
  pending); AutoFirm mitigates by **publishing clear authority limits** to counterparties where feasible.

## Build implication (concrete)
- **Component:** `legal/contracting/authority_guard.py` + reuse of A6.2 audit log and A7 HITL gate.
- **Contract:** `ContractAction{ authorizing_principal, authority_scope{max_value, counterparties[],
  deal_types[]}, within_scope: bool, human_signoff: Optional[approval], audit_ref }`.
- **Test (adversarial, safety-critical):** action with no principal → REFUSED; action exceeding
  max_value without sign-off → REFUSED; action to a non-allowed counterparty → REFUSED; boundary tests
  on the value threshold (just-under/at/just-over). These mutation-tested for teeth (CLAUDE.md §3.6).
