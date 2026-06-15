# BEST-PARTS — LTM Security Survey

## ADOPT
- **The six-phase lifecycle (Write/Store/Retrieve/Execute/Share/Forget) as AutoFirm's memory
  threat-model spine.** Build implication: the A4 memory layer's threat model (CLAUDE.md s5.6,
  THREAT_MODEL_PATH) is structured by these six phases; every phase gets at least one fail-closed
  control and one adversarial test.
- **The five governance primitives WA/PV/PS/RB/VF as MANDATORY, fail-closed memory controls** — this
  is the safety/correctness-critical core of A4 and directly satisfies CLAUDE.md s5.6:
  - **WA**: no memory write without an authenticated, authorized source (fail closed: no auth -> refuse write).
  - **PV**: every memory record carries a queryable provenance lineage (joins A6 provenance / append-only audit).
  - **PS**: retrieval is tenant/principal-scoped IN THE DATA LAYER (joins A8.2 multi-tenant isolation — NOT by convention).
  - **RB**: versioned snapshots + write logs enable rollback to a known-safe state.
  - **VF**: deletions are *verified* irrecoverable, not best-effort (joins folder 14).
- **The gap finding (store/share/forget under-defended)** tells AutoFirm exactly where to over-invest
  its adversarial test budget: cross-agent propagation and verified-forget are weak spots in the
  literature, so AutoFirm must build+test them deliberately rather than assume.

## REJECT / DEFER
- **Reject "trust the writing agent" designs** — the survey shows write-time poisoning is the
  best-studied, highest-impact attack; every write must pass WA. (Constrains A-Mem/MemGPT self-edit, folders 03/09.)
- **Defer LLM-based memory-security tooling** as a sole control — the survey flags it as sparse/
  unproven; use deterministic checks first, LLM checks as defense-in-depth.

## Build implication (concrete)
Mandates the **five governed memory primitives (WA, PV, PS, RB, VF), fail-closed**, and a
**six-phase memory threat model + adversarial test per phase** for L2.A4 — the binding security
contract joining A4 to A6 (provenance/audit), A7 (fail-closed), and A8.2 (data-layer tenant isolation).
