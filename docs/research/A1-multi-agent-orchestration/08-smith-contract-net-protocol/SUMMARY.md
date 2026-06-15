# SUMMARY — The Contract Net Protocol: High-Level Communication and Control in a Distributed Problem Solver

## Full citation
- **Title:** The Contract Net Protocol: High-Level Communication and Control in a Distributed
  Problem Solver
- **Author:** Reid G. Smith
- **Year:** 1980 (December)
- **Venue:** IEEE Transactions on Computers, Vol. C-29, No. 12, pp. 1104–1113.
- **DOI:** 10.1109/TC.1980.1675516

## Questions informed
- **L1.A1.1** (market/auction-based coordination pattern — completes the method-space survey) — PRIMARY.
- L1.A1.3 (dynamic role/task assignment via negotiation) — supporting.

## GRADE tier
**High.** Foundational, peer-reviewed IEEE Transactions paper; the canonical origin of market/auction
(bidding) coordination in multi-agent / distributed AI. Pre-LLM (indirectness down-rate for LLM
agents), but the negotiation/bidding mechanism is domain-independent and remains the reference
pattern for decentralized task allocation.

## Key claims (faithful)

### Mechanism
- The Contract Net Protocol (CNP) specifies "problem-solving communication and control for nodes in a
  distributed problem solver." "Task distribution is affected by a **negotiation process**, a
  discussion carried on between nodes with tasks to be executed and nodes that may be able to execute
  those tasks."
- Roles are dynamic, not fixed: a node acts as a **manager** (announces a task) or a **contractor**
  (bids to perform it); a node can be both for different tasks.

### The negotiation cycle (standard formulation)
1. **Task announcement** — the manager broadcasts a task with eligibility specs and bid requirements.
2. **Bid** — capable contractors submit bids describing their suitability.
3. **Award** — the manager evaluates bids and awards the contract to the chosen contractor.
4. **(Report/result)** — the contractor executes and returns results; subtasks may recursively become
   their own contract nets.

### Properties
- Decentralized, opportunistic allocation: work goes to the most suitable available node via mutual
  selection (manager selects contractor; contractor decides whether to bid), without a central
  scheduler dictating assignments.

## Reproducibility note
The negotiation cycle (announce → bid → award) is the canonical, universally-reproduced description
of CNP and is the load-bearing item. Citation verified via IEEE/ACM records (DOI 10.1109/TC.1980.1675516).
