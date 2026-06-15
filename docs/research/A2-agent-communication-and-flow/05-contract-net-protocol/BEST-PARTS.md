# BEST-PARTS — Contract Net Protocol

## What AutoFirm should ADOPT and why

1. **The manager/contractor model as AutoFirm's dynamic delegation primitive.** ADOPT
   announce -> bid -> award as the typed protocol the orchestrator uses to assign work to
   dynamically-spawned role agents (L2.ORG dynamic spawn/re-scope). Build implication: when the
   orchestrator has a task but the best agent is not predetermined, it issues a `cfp`
   (capability-matched via Agent Cards, source 01); candidate agents `propose`; orchestrator
   awards. This is the evidence-backed pattern for AutoFirm's "dynamic, modular company".

2. **Recursive decomposition by the contractor.** ADOPT: an awarded agent may itself become a
   manager and sub-contract — the hierarchical orchestrator-worker tree (links A1). Build
   implication: gives a principled, bounded recursion for the agent org, but fan-out stays an
   explicit decision (CLAUDE S4.1) — the protocol makes each sub-contract an *auditable awarded
   contract*, not a silent spawn.

3. **Award as an auditable, attributable decision.** ADOPT logging every announce/bid/award as
   signed messages. Build implication: feeds A6 append-only audit — "who was awarded what, why
   (which bid won)" is recorded -> directly serves A2's "audited inter-team comms" priority and
   the explain-every-decision rule (S3.11).

## What AutoFirm should REJECT / DEFER

- **REJECT open competitive bidding as the *default*** for ordinary, well-structured work.
  Justified: most AutoFirm flows have a known structure where a deterministic DAG is cheaper and
  more reliable (source 08) — reserve CNP negotiation for genuinely *dynamic* allocation where
  the right agent is not known in advance. Using CNP everywhere adds latency/cost.
- **DEFER market-priced bidding / utility auctions.** AutoFirm agents are cooperative internal
  workers, not self-interested market participants; capability-fit, not price, drives the award.

## Concrete build implication
CNP is the chosen **dynamic task-allocation protocol** in AutoFirm's flow library (alongside the
deterministic DAG from source 08): used for "I have a task, who is best?" cases. Drives a test:
every awarded contract is traceable to the winning bid and logged; a task with no qualified bid
fails closed (no silent self-assignment) — mitigating MAST FM "agent disobeys role / unilateral
executive decision" (source 02).
