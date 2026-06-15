# BEST-PARTS — Generative Agents

## ADOPT
- **The recency + relevance + importance retrieval score as AutoFirm's default memory ranker.**
  Build implication: the retriever returns top-k by `0.995^{hours} (recency) + cosine (relevance)
  + LLM_poignancy/10 (importance)`. Crucially it is a **deterministic, explainable score** — every
  retrieved memory can state *why* it surfaced (which of the three drove it), satisfying CLAUDE.md
  s3.11 "explain every decision". This is a concrete, testable formula for L2.A4.
- **Importance/poignancy scoring** as a write-time signal to decide what is worth promoting from
  Storage to longer-lived tiers (links to the maturity model in folder 01).
- **Reflection-on-threshold** as the trigger mechanism for AutoFirm's reflection job: accumulate
  importance, fire a reflection pass when it crosses a configurable threshold (their 150 is a tuned
  constant — AutoFirm must make it a parameter, NOT a magic constant; see Reject below).

## REJECT / DEFER
- **Reject hard-coding the constants (0.995, threshold 150, alpha=1).** These were tuned for a game
  sandbox; copying them verbatim would be overfitting (CLAUDE.md s3.9). Adopt the *form*; expose
  decay, threshold, and weights as **configured, validated parameters** and select them on a golden
  set per L2.A4's branch-experiment.
- **Defer the social-simulation specifics** (planning a day, agent-to-agent gossip) — out of scope
  for the company-operations memory layer.

## Build implication (concrete)
Defines the **explainable retrieval-ranking formula** (recency/relevance/importance, weights as
tunable parameters) and the **importance-threshold reflection trigger** for L2.A4, both feeding the
"explain every retrieval" requirement and the `evidence/` ablation chart (which component matters).
