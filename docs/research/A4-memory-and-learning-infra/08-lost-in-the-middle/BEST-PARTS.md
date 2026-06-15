# BEST-PARTS — Lost in the Middle

## ADOPT
- **"A big context window is not memory" as a binding design axiom.** Build implication: AutoFirm
  MUST NOT solve long-horizon recall by dumping history into the prompt — relevant facts get lost in
  the middle. This is the empirical justification for the entire external-memory + retrieval layer
  (folders 03-07) over naive context-stuffing.
- **Position-aware context assembly.** Build implication: when the retriever returns top-k memories,
  AutoFirm places the **highest-ranked items at the start and end** of the assembled context, not the
  middle, and keeps the assembled context short — a concrete, testable context-builder rule.
- **A regression test:** insert a known fact at the middle of a long context and assert AutoFirm
  still retrieves+uses it (proving the memory layer compensates for the LLM's positional bias).

## REJECT / DEFER
- **Reject the "just use a longer model" shortcut** for memory — empirically insufficient.

## Build implication (concrete)
Justifies retrieval-over-stuffing and adds the **position-aware context-assembly rule (rank-1 at
edges)** plus a **middle-of-context recall regression test** to L2.A4.
