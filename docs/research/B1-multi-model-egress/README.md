# B1 — Multi-Model Egress / Cross-Provider Gateway (Workstream 1) — Research Library

Deep, primary-sourced research for AutoFirm's **multi-model egress gateway**: a deterministic
selection policy + an optional learned router + ensemble-quorum reconciliation behind a
self-hosted, OpenAI-compatible gateway. Institution-grade bar; research gates building
(CLAUDE.md §2 CRO, §3.3, §4.6). One folder per source.

## Sources (one folder per source — §4.6)

| Folder | Source | One-line takeaway |
|--------|--------|-------------------|
| `2023-frugalgpt-llm-cascades` | FrugalGPT (Chen, Zaharia, Zou — 2023, arXiv 2305.05176) | Budget-constrained **deterministic cascade**: cheap→expensive, escalate only when a trained reliability scorer is below threshold. |
| `2023-automix-self-verification-cascade` | AutoMix (Madaan et al. — NeurIPS 2024, arXiv 2310.12963) | **Self-verification + POMDP meta-verifier** routes SLM→LLM under noisy confidence; **IBC** efficiency metric. |
| `2024-routellm-learned-router` | RouteLLM (Ong et al. — 2024, arXiv 2406.18665) | **Learned pairwise (strong/weak) router**; **PGR/APGR** metrics; over-2× cost reduction. |
| `2024-routerbench-routing-benchmark` | RouterBench (Hu et al. — 2024, arXiv 2403.12031) | **N-way routing benchmark**; convex-hull "Zero-router" baseline; **AIQ** (normalised area under quality–cost curve). |
| `2024-hybrid-llm-quality-router` | Hybrid LLM (Ding et al. — ICLR 2024) | Quality-gap router with a single threshold `τ` sweeping the cost–quality curve. |
| `2023-llm-blender-ensemble` | LLM-Blender (Jiang et al. — ACL 2023) | **Rank-then-fuse** ensemble: pairwise ranker (PairRanker) + generative fuser (GenFuser). |
| `2023-self-consistency-majority-vote` | Self-Consistency (Wang et al. — ICLR 2023) | **Sample-and-marginalize majority vote** over reasoning paths; deterministic tie-break needed. |
| `2024-mixture-of-agents` | Mixture-of-Agents (Wang et al. — 2024) | **Layered aggregation** of multiple LLMs; later layers refine earlier outputs. |
| `circuit-breaker-and-resilience-patterns` | Fowler / Nygard / Microsoft / AWS | Circuit-breaker state machine, **full-jitter backoff**, bulkhead isolation (failover correctness). |
| `litellm-proxy-gateway` | LiteLLM Proxy (BerriAI) docs | Self-hosted OpenAI-compatible gateway; per-token price catalog; **estimated** cost. |
| `openrouter-gateway` | OpenRouter docs | Hosted multi-provider gateway; returns **actual** cost (`usage.cost`) — `provider_reported` source. |

## Bake-off & metric
- `golden-set-and-metric.md` — the pre-registered (Gate-1) golden prompt set, the four acceptance
  metrics (functional correctness, failover correctness = 1.0, cost-attribution exact-to-the-unit,
  p95 added latency), and the determinism / no-overfit guardrails.

## Faithfulness status (CRO Gate-0)
All reproduced formulae carry inline citations. **Verified 2026-06-17 against canonical sources:**
AutoMix IBC (ar5iv 2310.12963), RouteLLM PGR/APGR (ar5iv 2406.18665). FrugalGPT's per-dataset
table figures and RouterBench's exact `R̃_θ` curve definition remain explicitly flagged in-file
for PDF/data-schema re-check before regulator-facing quotation.
