# BEST-PARTS — Malone & Crowston 1994 (Coordination Theory)

## ADOPT
1. **"Coordination = managing dependencies between activities" as AutoFirm's design axiom** — the
   orchestrator's whole job is dependency management. *Build implication:* AutoFirm should make
   **inter-task dependencies explicit and typed** (a dependency graph / DAG between subtasks), then
   apply the matching mechanism — instead of relying on emergent agent chatter (which source 04 shows
   is where 39.1% of failures live). This is the theoretical backbone for the L2.A1 / L2.ORG design.
2. **The dependency→mechanism lookup table as a routing engine** — AutoFirm classifies each inter-agent
   relationship and applies the cited mechanism:
   - **Prerequisite** → notification/sequencing/tracking → *gate-based phases* (CLAUDE.md §4.2).
   - **Shared resource** (scarce agent/compute/context budget) → bidding/priority → *span caps +
     token budget* (ties source 02's token economics).
   - **Usability** → **standardization of outputs** → *typed data contracts between stages*
     (CLAUDE.md §4.1, cross-ref A2.3). This is the cited justification for AutoFirm's typed contracts.
   - **Task/subtask** → goal selection + decomposition → *the planning agent* (HALO A_plan, source 03).
   - **Simultaneity** → scheduling/synchronization → *fan-out/fan-in join barrier* (CLAUDE.md §4.3).
3. **Task assignment IS resource allocation** — sizing/assigning the scarce "time of actors" is a
   shared-resource problem → AutoFirm's agent-spawn decision can use the cited allocation methods
   (priority, market/bidding — connects to source 08 Contract Net).

## REJECT / scope
- **Nothing rejected** — this is foundational theory, not a competing system. Caveat: it predates LLMs
  (indirectness), so AutoFirm adopts the *abstraction*, not any specific 1994 mechanism implementation.

## Build implication (concrete)
- AutoFirm represents work as an **explicit typed dependency graph**, and the orchestrator routes each
  dependency type to a cited coordination mechanism (the table above). "Standardization of outputs" →
  **typed contracts** become a first-class platform artifact (drives L2.A1, L2.ORG, and the A2
  message-schema branch). This turns coordination from vibes into a designed, testable mechanism.
