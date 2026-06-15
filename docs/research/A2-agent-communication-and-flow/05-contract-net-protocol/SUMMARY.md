# SUMMARY — The Contract Net Protocol (Smith 1980)

## Full citation
- **Title:** The Contract Net Protocol: High-Level Communication and Control in a Distributed
  Problem Solver
- **Author:** Reid G. Smith
- **Year:** 1980
- **Venue:** IEEE Transactions on Computers, Vol. C-29, No. 12, pp. 1104-1113
- **DOI:** 10.1109/TC.1980.1675516 ·
  https://dl.acm.org/doi/10.1109/TC.1980.1675516 ·
  https://en.wikipedia.org/wiki/Contract_Net_Protocol

## Questions it informs
- **L1.A2.2** (structured negotiation as a coordination/workflow pattern — PRIMARY prior art)
- L1.A2.1 (the message sequence underlying cfp/propose/accept — supporting)

## GRADE tier: High
Foundational peer-reviewed paper (IEEE TC), the canonical task-allocation negotiation protocol;
basis of the FIPA Contract Net interaction protocol (source 04). Heavily cited primary work.
No down-rate.

## Key claims (faithful)

- **Purpose:** CNP specifies "problem-solving communication and control for nodes in a
  distributed problem solver," where task distribution is achieved by a **negotiation process**
  between nodes with tasks and nodes able to execute them. Introduced 1980 by Reid G. Smith.

- **Roles:** each node can act as a **manager** or a **contractor**; a task assigned to a node
  can be **further decomposed** by the contractor (recursive task decomposition).

- **The negotiation cycle (bidding scheme):**
  1. **Task announcement** — the manager broadcasts/announces a task to candidate contractors.
  2. **Bids** — potential contractors submit bids (proposals) on tasks they can perform.
  3. **Award** — the manager chooses among bids and awards the contract.
  (FIPA later formalized this as CFP -> propose -> accept-proposal/reject-proposal — source 04.)

- **Property:** decentralized control of task execution with efficient multi-agent
  communication; the subcontractor model supports dynamic, opportunistic allocation.

## Reproducibility note
The manager/contractor roles and the announce->bid->award cycle are the defining, widely-cited
content of Smith (1980) and are reproduced identically in standard MAS texts and the FIPA
Contract Net spec — a reviewer can confirm against IEEE TC C-29(12) or the FIPA SC00029
Contract Net Interaction Protocol specification.
