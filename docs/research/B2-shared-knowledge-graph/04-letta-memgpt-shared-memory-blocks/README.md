# MemGPT / Letta — Shared Memory Blocks for Multi-Agent Context Sharing

> Workstream 2 research library — source 4 of 6.
> Method-space cell: **MCP / shared-memory-block patterns; interop across heterogeneous agents.**

---

## 1. Full citation

Packer, C., Wooders, S., Lin, K., Fang, V., Patil, S. G., Stoica, I., & Gonzalez, J. E. (2023).
*MemGPT: Towards LLMs as Operating Systems.* arXiv:2310.08560 (submitted 12 Oct 2023; rev. 12 Feb 2024).
<https://arxiv.org/abs/2310.08560>
Productized as **Letta** — <https://docs.letta.com> (memory-blocks + shared/attached-blocks docs).

---

## 2. Faithful structured summary

### Core mechanism — OS-inspired virtual context management
By analogy to OS virtual memory tiering between fast and slow storage, MemGPT gives an LLM the *appearance*
of memory far larger than its token window by **paging information between an in-context tier and external
storage**, with the **LLM itself driving the paging via tool/function calls**.

### Architecture (confirmed)
- **Main context (in-context)** = the LLM's **token window** — system instructions, the self-editable working
  memory, and a FIFO of recent messages. Bounded by the model's max context.
- **External context (out-of-context)** = persistent storage **outside** the token window, paged in on demand.
  Two named Letta tiers:
  - **Recall memory** — the full conversation/event history (searchable).
  - **Archival memory** — general long-term, vector-searchable store for arbitrary text/facts.
- **Self-editing memory** via tool calls — e.g. `core_memory_append`, `core_memory_replace` (edit in-context
  working memory), plus archival/recall search + insert tools. **Heartbeat interrupts** let the agent chain
  memory ops before yielding. On "memory pressure" (window near full) the agent **evicts/summarizes** out to
  external storage.

### The Letta "memory block" abstraction (CRITICAL for W2 — confirmed from docs)
A **memory block** is a *labeled, bounded, persistent unit of context*. Fields (quoted):
- **`label`** — unique identifier (e.g. `human`, `persona`, `organization`).
- **`description`** — the block's purpose, to guide the agent.
- **`value`** — the contents.
- **`limit`** — the **size limit in characters** (the bound).

Blocks are **stored in the DB**, **injected into the system prompt** at the top of the context window
(rendered in XML, e.g. `<memory_blocks>`), and are **model-agnostic** — plain text spliced into *any*
model's context, so they **port across providers/models unchanged**.

### Sharing ONE block across MULTIPLE agents (the interop guarantee — confirmed)
- A block created via the API (not inline) is a standalone resource referenced by **`block.id`**.
- Attach to multiple agents at creation via **`block_ids: [block.id]`**, or to an existing agent via
  **`client.agents.blocks.attach(agent_id, block_id)`**.
- **Interop guarantee (quoted):** *"If multiple agents are attached to a block, they will all have the block
  data in their context windows (essentially providing shared memory)."* An update by one agent is
  **immediately visible** to all others sharing that block, **regardless of each agent's underlying model.**

### Limitations / ops (confirmed)
- **Concurrency: "last write wins"** — concurrent edits to the same block overwrite earlier changes; mitigate
  by marking blocks **read-only**. No built-in merge/locking.
- `limit` is a hard character bound; oversized memory must page to archival/recall → extra tool-call
  round-trips and tokens.
- Self-editing + paging adds latency / tool-call overhead vs a static prompt.

---

## 3. Best parts to take — mapped to the W2 design

| Take this | Into this W2 component |
| --- | --- |
| **The memory-block abstraction itself: `{label, description, value, limit}`, plain text, model-agnostic.** | This **IS** the W2 **typed shared-context block** — the cross-provider interop primitive. Plain-text, bounded, labeled → any provider's model can consume it identically. The `limit` enforces minimality at the type level. |
| **One block attached to many agents → an update by one is visible to all, regardless of model.** | The exact interop guarantee W2 needs: model A (provider X) writes a fact; model B (provider Y) reads it. The graph store is source of truth; the shared block is the **rendered minimal projection** the assembler injects into each heterogeneous agent. |
| **In-context (block) vs out-of-context (graph store) tiering.** | Confirms the split: the **graph store = out-of-context source of truth**; the **assembled shared-context block = the minimal in-context slice**. Never inject the whole store. |
| **XML-wrapped, system-prompt-top rendering.** | Render hint for the assembler output — a deterministic, model-agnostic serialization the assembler emits. |

### RED flags carried forward
- **"Last write wins" with no locking/merge.** Concurrent cross-provider writes can silently clobber. W2 must
  reconcile through the **append-only, versioned graph store** (AutoFirm's existing `evolve`/supersession
  pattern in `agent_memory_layer.py`) — NOT by treating the shared block as authoritative. The block is a
  **read-only projection**; writes go to the store and re-render. This is the single most important boundary.
- The `limit` character bound forces the assembler to be genuinely **minimal** — good, but means the assembler
  must rank and truncate correctly (see Lost-in-the-Middle / RULER, folder 05).
