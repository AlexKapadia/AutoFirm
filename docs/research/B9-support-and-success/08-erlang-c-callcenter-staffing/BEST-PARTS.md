# BEST-PARTS — Erlang C staffing

## ADOPT
- **Erlang C as AutoFirm's deterministic SLA-feasibility / staffing calculator** for any client support operation. Given forecast volume (λ), AHT, and an SLA target (e.g. answer X% within Y seconds), compute the minimum agent/agent-capacity count `c`.
  - **Build implication (L2.B9 / ties to L1.B11 ops):** ship `erlang_c_agents(volume, aht, sl_target, sl_seconds)` and `service_level(c, A, t, aht)` as deterministic functions with EXACT formula implementation and boundary tests (instability when c ≤ A must raise/return ∞; SL→1 as c→∞; known textbook reference values must match — CLAUDE §3.11 zero-error). This makes "can we hit this SLA?" answerable, not guessed.
- **The 80/20 benchmark as the DEFAULT (not fixed) service-level prior** for synchronous channels; parameterise per industry/channel (chat, email, and async have different targets).
- **Occupancy `ρ = A/c` as a cost/wellbeing guardrail** — flag staffing plans with ρ above a configurable cap (sustained >85–90% predicts long queues + agent burnout).

## REJECT / ADAPT
- **REJECT base Erlang C where abandonment matters** — use Erlang A/X (with abandon rate) for high-wait scenarios; document which model is used. Do NOT silently assume no abandonment.
- **REJECT stationary-arrival assumption for forecasting** — feed Erlang C with interval-level (e.g. half-hourly) non-stationary forecasts, not a single daily average (real demand is inhomogeneous Poisson).
- **REJECT hard-coding 80/20** as a universal truth — it is a convention; let the client's SLA drive it (anti-overfit, CLAUDE §3.9).

## Why (cited)
- Provides the quantitative, industry-general bridge from SLA targets (source 07) to capacity, with an exact formula AutoFirm can encode and test. High-tier mathematics; the convention-vs-derived distinction is explicitly flagged to avoid over-claiming.
