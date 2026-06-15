# BEST-PARTS — MemGPT

## ADOPT
- **OS-style tiered memory (main vs external context, with paging) as AutoFirm's memory-management
  pattern.** Build implication: a memory manager that keeps a small working context and pages
  episodic/semantic records in/out on demand — the operational layer that sits above the
  CoALA stores (folder 02) and the retriever (03-07). This is the answer to "how does a long-horizon
  build session not overflow context" (ties to A3 long-horizon / resume).
- **Self-editing memory via explicit function calls** as the *interface* AutoFirm exposes to agents
  (read/write/search memory as tools), which makes every memory operation an **auditable, typed
  action** (joins A6 provenance, A2 typed contracts).
- **Archival vs recall storage distinction** maps cleanly to AutoFirm's durable semantic store vs
  the full episodic log.

## REJECT / DEFER
- **Constrain self-directed memory writes under governance.** An LLM freely editing its own memory is
  the write-time-corruption surface (folder 12). Adopt the function-call interface but route every
  write through Write-Authorization + provenance + rollback (A4.4) rather than trusting the agent.
- **Defer the full "LLM as OS" framing** — useful metaphor, but AutoFirm's scheduler/orchestrator is
  the real OS; MemGPT informs the memory subsystem only.

## Build implication (concrete)
Specifies the **tiered memory-manager with paging + a typed self-edit function interface** for
L2.A4, with every write governed (not autonomous) — the operational glue between memory and
long-horizon resume (A3) and governance (A6/A7).
