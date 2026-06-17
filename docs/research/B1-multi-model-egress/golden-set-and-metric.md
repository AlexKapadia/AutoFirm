# W1 Multi-Model Egress — Golden Set & Metric Proposal

> **Status:** DRAFT for ratification at **Gate 1**. Proposed by the CRO research org as the
> pre-agreed, frozen evaluation contract for Workstream 1 (multi-model gateway: deterministic
> selection policy + optional learned router + ensemble-quorum reconciliation behind a
> self-hosted OpenAI-compatible gateway). Per CLAUDE.md §3.4 / §4.5, the golden set and metric
> are **defined up front, before any competing approach is implemented**, so candidates compete
> on identical, pre-registered conditions and only the evidence-backed winner merges to `main`.

This document defines **(A)** the golden prompt set, **(B)** the metrics and their exact
definitions, **(C)** the acceptance gates, and **(D)** the determinism / no-overfit guardrails.
It deliberately separates the **platform-test** golden set (synthetic, used to validate W1
mechanics) from the later **public-data E2E validation** (CLAUDE.md §3.12) — W1's golden set is
**synthetic-fixture only**, with prompts shaped after the four public-company industries but
carrying **no real PII, client data, or confidential documents**.

---

## A. Golden prompt set (~40 deterministic prompts)

**Shape:** 4 public-company industries × 4 task types × ~2–3 prompts each = **40 prompts**.

Industries (chosen because their public artifacts — 10-Ks, product pages, press releases,
support docs — are abundant and let the *later* E2E gate use real public data without sensitive
material). For the W1 golden set itself the inputs are **synthetic but industry-shaped**:

| # | Industry | Synthetic input shape (no real entities) |
|---|----------|------------------------------------------|
| 1 | SaaS / software | mock product changelogs, pricing tables, synthetic support tickets |
| 2 | Consumer retail / e-commerce | mock catalog entries, returns-policy text, synthetic reviews |
| 3 | Financial services | synthetic earnings-call snippets, mock disclosure paragraphs (no real filings) |
| 4 | Healthcare / life-sciences services | synthetic clinical-ops notes, mock formulary entries (NO real PHI/PII) |

Task types (each must have a **deterministic, machine-checkable expected output** so correctness
is exact — never a subjective LLM-judge for the W1 gate):

| Task | Definition | Expected-output form | Why deterministic-checkable |
|------|------------|----------------------|------------------------------|
| **summarise** | condense a ≤2k-token doc to a fixed schema (e.g. 3 bullet facts + 1 risk) | structured JSON with required keys; key facts as a closed set | exact-match on required facts + schema-valid; ROUGE only as a secondary, non-gating signal |
| **extract** | pull named fields (amounts, dates, entities) into JSON | JSON with exact expected values | **exact-match to the unit** — numeric/string equality |
| **classify** | assign one label from a closed taxonomy | single enum label | exact label equality |
| **route** | decide which model tier/capability a request needs given a synthetic intent | one of `{cheap, mid, strong, ensemble}` per a published rubric | exact match to the rubric-derived label |

**Construction rules (anti-overfit, CLAUDE.md §3.9):**
- Each prompt has a **deterministic expected answer** derived from the synthetic fixture by a
  rule the model never sees — *not* by running a model and freezing its output (that would bake
  in a model's bias and overfit the gate to one model).
- Prompts span the **edge-case matrix** (CLAUDE.md §3.6): include degenerate inputs (empty field,
  single token, max-length doc), threshold-edge cases (just-over / just-under any cost or
  confidence cutoff), the "strong-on-every-axis-but-one-hard-rule-excludes-it" class for the
  `route` task, missing/`None`/partial fields for `extract`, and at least 2 **adversarial /
  prompt-injection** documents that must NOT alter the structured output.
- A **held-out shadow set** (≈10 additional prompts, same construction, *not* used for any
  threshold tuning) measures generalisation. Any learned router or threshold is fit ONLY on the
  golden set and reported on the shadow set; a gap > a pre-agreed delta is a RED (overfit) flag.

Stored as `evidence/`-bound synthetic fixtures + an expected-output manifest; the suite runs
from the one project command (`make test`) with **no network** in unit tests (gateways mocked).

---

## B. Metrics — exact definitions

All four are **pre-registered** and reported with uncertainty (mean ± 95% CI where applicable),
per CLAUDE.md §3.10. The metric notation below is AutoFirm's own (the research papers'
metrics — PGR/APGR/AIQ/IBC — are reproduced faithfully in the per-paper READMEs and inform, but
do not replace, these acceptance metrics).

### B.1 Functional correctness vs expected — **≥ single-model CLI baseline**

For a candidate routing/ensemble policy `R` over the N golden prompts:

```
Correctness(R) = (1/N) * Σ_{i=1..N}  match(output_R(prompt_i), expected_i)
```

where `match(·,·)` is:
- **exact equality** for `extract`, `classify`, `route` (string/numeric/enum, to the unit);
- **schema-valid AND required-fact-set ⊆ output** for `summarise` (closed-set fact match).

**Baseline:** the same suite run through the existing single-model **Claude Code CLI path**
(one model, no routing). The acceptance bar is:

```
Correctness(R)  ≥  Correctness(CLI_baseline)
```

i.e. routing/ensemble must **not regress** functional correctness while it reduces cost or adds
resilience. (This mirrors RouteLLM's PGR framing — gains measured relative to the strong-model
reference — but uses our own deterministic graders, not BART/LLM-judge, to avoid the
quality-proxy mismatch flagged in the RouteLLM/Hybrid-LLM notes.)

Reported alongside, **per task type**: precision/recall for `classify`/`extract`, and the
cost-vs-correctness point so the candidate can be placed on a cost-quality curve (the
RouterBench "non-decreasing convex hull" / AIQ idea — a candidate must sit **on or above** the
Zero-router interpolation hull of {cheap-only, strong-only}).

### B.2 Failover correctness = **no lost request** (and no silent wrong-source answer)

Under injected provider faults (timeouts, 429s, 5xx, connection resets, partial streams),
measured over a fault-injection campaign of F induced failures:

```
FailoverCorrectness =  (requests that returned a correct-OR-cleanly-refused result)
                       ----------------------------------------------------------- = 1.0  (required)
                                    (total requests issued)
```

Acceptance is **exactly 1.0**: **zero lost requests**. Every request must either (a) be served
by a healthy fallback provider with a still-correct answer, or (b) **fail closed** with an
auditable error — never silently drop, never hang past the deadline, never return a
truncated/garbage answer dressed up as success. The circuit-breaker must transition
Closed→Open→Half-Open per the documented state machine, and a request routed during `Open` must
go to a fallback, not the tripped provider. Retries follow **full-jitter backoff**
(`sleep = random(0, min(cap, base*2^attempt))`) and are **bounded** (no unbounded retry storm).

Sub-checks (all must pass): (i) breaker trips at the configured failure threshold; (ii) breaker
re-closes only after the configured success count in Half-Open; (iii) bulkhead isolation — one
provider's saturation does not exhaust another provider's pool; (iv) idempotency — a
retried/failed-over request is **not double-executed** in a way that double-counts cost.

### B.3 Cost-attribution exactness — **to the unit**

For every request, the gateway must attribute cost with **zero numerical error on the
deterministic path** (CLAUDE.md §3.11). Define, per request `j`:

```
attributed_cost_j   = Σ over actual billed attempts a:  price_map(model_a) · tokens_{a,in/out}
authoritative_cost_j = provider/gateway-reported per-request cost for the same billed attempts
```

Acceptance:

```
| attributed_cost_j  −  authoritative_cost_j |  ≤  ε_unit     for ALL j
```

with `ε_unit` = the smallest representable currency/credit unit (i.e. **exact to the unit**,
not "within a few percent"). Aggregate spend over the run must reconcile to the sum of
per-request costs with no rounding drift. **Telemetry requirements that make this checkable:**
- per-request token counts (in/out, and per attempt on failover/retry) captured **in-band**;
- per-request cost captured **in-band** (no async follow-up call required for the gating path);
- the **price map is pinned and version-stamped**; estimated cost (e.g. LiteLLM price-map) is
  reconciled against a **provider-authoritative** figure (e.g. OpenRouter `usage.cost`), and the
  **credit↔USD unit convention is recorded** so attribution does not mis-scale.
- retries/fallbacks are attributed **per actual billed attempt** (no double-counting; no
  un-counted hidden attempt).

> **Why this is a hard gate, not a nicety:** W5 (cost/finance) depends on W1's per-request cost
> being exact. A "estimated, ~roughly right" cost feed poisons every downstream
> pricing/valuation decision. See the RED flags in the gateway READMEs.

### B.4 p95 added latency (gateway overhead budget)

The gateway's own overhead (routing decision + bookkeeping + breaker check), **excluding** the
upstream model's generation time:

```
added_latency_j = wall_time(gateway_returns_j) − wall_time(upstream_first_byte_or_completion_j)
```

measured over the golden suite under nominal (no-fault) conditions. Acceptance:

```
p95( added_latency_j over all j )  ≤  L_budget
```

Proposed budget **`L_budget` = 50 ms p95** for the deterministic-policy path (routing decision +
telemetry capture), reported as a distribution (p50/p95/p99) with the latency histogram in
`evidence/`. The **ensemble-quorum** and **learned-router** paths are budgeted separately (they
legitimately add fan-out / inference latency) and reported as their own curves so the cost of
each optional layer is explicit. (Exact `L_budget` ratified at Gate 1 against measured baseline.)

---

## C. Acceptance gate (Gate-1-ratified, enforced at W1 sign-off)

A W1 routing/ensemble candidate is **GREEN** only if **all** hold on the golden set, with the
shadow set confirming generalisation:

1. **B.1** `Correctness(R) ≥ Correctness(CLI_baseline)` and the candidate sits on/above the
   {cheap, strong} cost-quality hull. (Functional non-regression.)
2. **B.2** `FailoverCorrectness = 1.0` across the full fault-injection campaign. (No lost request.)
3. **B.3** Cost attribution exact to the unit for **every** request; aggregate reconciles. (W5-critical.)
4. **B.4** `p95(added_latency) ≤ L_budget` on the deterministic path. (Overhead budget.)
5. **Generalisation:** golden-vs-shadow correctness gap ≤ pre-agreed delta (no overfit).
6. **Determinism:** identical input + pinned config/seed ⇒ **byte-identical** routing decision
   and attributed cost across ≥100 repetitions (CLAUDE.md §5.5).

100% pass + coverage are **necessary, not sufficient** (§3.6): the suite must include the
adversarial/edge matrix above, and the mutation gate must kill injected faults in the routing,
cost-attribution, and failover code before W1 is "done".

---

## D. Determinism & no-overfit guardrails (binding)

- **Deterministic core is the reference.** The deterministic selection policy (capability +
  cost + health rules) must pass the full gate **on its own**, with no learned router. The
  learned router and ensemble-quorum are **optional layers** that may only merge if they
  measurably beat the deterministic core on the pre-registered metrics — and they fail closed
  to the deterministic core when their inputs (labels, confidence) are missing or stale.
- **No magic constants.** Thresholds (cost cutoffs, confidence/quorum thresholds, breaker
  failure-count) are config, fit on the golden set, validated on the shadow set, and documented
  with the number that justified them — never hand-tuned to pass a specific prompt.
- **Quorum is task-aware.** Exact-match majority vote (with a **deterministic tie-break by
  model-priority order**) for `extract`/`classify`/`route`; rank-then-fuse is reserved for
  free-text `summarise` and is reported separately because it introduces a generative/
  non-deterministic step. Quorum must never be applied where it splits near-equal free-text and
  produces a meaningless majority (RED flagged in the ensemble notes).
- **Synthetic-only for W1.** Real public-data validation is a **separate, later** gate
  (§3.12), clearly labelled, and isolated from this synthetic suite.

---

## E. Provenance

Metrics and guardrails synthesised from the peer-reviewed / primary sources in this folder:
FrugalGPT & AutoMix (cascade + confidence-threshold escalation, IBC), RouteLLM / RouterBench /
Hybrid-LLM (PGR/APGR/AIQ, convex-hull baseline, overfit-to-benchmark warnings), LLM-Blender /
Self-Consistency / Mixture-of-Agents (quorum vs rank-then-fuse, determinism caveats), and the
circuit-breaker / full-jitter / bulkhead + LiteLLM / OpenRouter gateway notes (failover state
machine, in-band cost telemetry, estimated-vs-authoritative cost). See each per-source README
for exact citations and reproduced formulae.
