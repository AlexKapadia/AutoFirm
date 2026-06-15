# BEST-PARTS — Multiagent Debate (Du et al., ICML 2024)

## ADOPT
1. **Debate as a targeted QUALITY/VERIFICATION pattern, not a general topology** — use multi-agent
   debate where AutoFirm needs **factuality + reasoning robustness** (e.g. the CRO's research-claim
   verification, the QA gate, contested design decisions). *Build implication:* AutoFirm's QA / North
   Star reviews can run a small debate (3 agents, ≤4 rounds) to cross-examine a verdict, with cited
   evidence that this reduces hallucination and corrects errors even when all agents start wrong.
2. **The diminishing-returns parameterization (3 agents, ~2–4 rounds)** — adopt as the **default knob
   setting** for any debate AutoFirm runs; ">4 rounds ≈ 4 rounds" means cap rounds to control cost.
3. **"Stubborn" prompting → better final answers** — encode in AutoFirm's debate prompts: bias agents
   to defend their reasoning rather than capitulate, to avoid premature herding consensus.
4. **Mixed-model debate helps (11/14→17)** — *Implication:* AutoFirm can debate *across* model tiers
   (e.g. Opus + Sonnet) for higher quality on critical verdicts, complementing the orchestrator-worker
   model split (source 02).

## REJECT
- **Debate as AutoFirm's PRIMARY coordination topology** — REJECT: it is compute-expensive, requires
  all agents to share full context (the opposite of the breadth-first parallelism AutoFirm relies on,
  source 02), convergence "is not guaranteed," and large-N debate hits "context length error." It does
  not scale to running a whole company. Use hierarchy (03) as the backbone; insert debate as a
  *bounded sub-routine*.
- **Unbounded rounds / herding** — REJECT: showing ongoing votes "amplifies herding … can yield
  premature consensus" (corroborated by source 09 Tian et al.). Cap rounds; hide running tallies.

## Build implication (concrete)
- A reusable **bounded-debate verification primitive** (3 agents, ≤4 rounds, stubborn prompts, optional
  cross-tier models, no live vote display) wired into the QA / CRO / North Star gates (CLAUDE.md §2,
  §4.9). Explicitly NOT the platform's main topology. Feeds the L2.A9 evaluation design.
