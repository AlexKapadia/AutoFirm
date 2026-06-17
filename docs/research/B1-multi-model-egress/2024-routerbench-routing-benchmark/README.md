# RouterBench — A Benchmark for Multi-LLM Routing Systems (2024)

> Research note for AutoFirm **W1 multi-model egress** (B1). Faithful summary of a primary
> source. Formulae reproduced exactly; transcription risk flagged where it exists.

---

## (1) Full citation

- **Title:** *RouterBench: A Benchmark for Multi-LLM Routing System*
- **Authors:** Qitian Jason Hu, Jacob Bieker, Xiuyu Li, Nan Jiang, Benjamin Keigwin,
  Gaurav Ranganath, Kurt Keutzer, Shriyash Kaustubh Upadhyay
- **Org:** Martian (with UC Berkeley collaborators)
- **Year:** 2024 (submitted 2024-03-18; v2 2024-03-28)
- **Venue:** arXiv preprint (cs.LG)
- **arXiv id:** 2403.12031
- **URL:** https://arxiv.org/abs/2403.12031 — HTML: https://arxiv.org/html/2403.12031v2

---

## (2) Faithful structured summary

### PROBLEM
*"No single model can optimally address all tasks and applications, particularly when
balancing performance with cost,"* and *"the absence of a standardized benchmark for
evaluating the performance of LLM routers hinders progress."* RouterBench supplies a large
pre-computed dataset of LLM outputs + costs so routers can be evaluated **offline,
reproducibly, without re-running inference**, plus a **theoretical framework** for comparing
routers on a cost–quality plane.

### METHOD — the benchmark + the framework

**Composition (verbatim):** *"In total, there are 405,467 samples in RouterBench, covering 11
models, 8 datasets, and 64 tasks."* Each sample stores, for a prompt, every model's response,
its quality score, and its **per-token cost**, so any router policy can be replayed offline.

**Per-query router objective** (reproduced):
```
performance_score_{ij} = λ · P_{ij} − cost_j
```
where `P_{ij}` = (predicted) performance of model `M_j` on sample `x_i`, `cost_j` its cost, and
`λ` = **willingness-to-pay (WTP)** parameter (quality per unit cost). Sweeping `λ` traces out
the cost–quality frontier.

**Non-decreasing convex hull + interpolation.** Each router (and each standalone model) is a
point `(cost, quality)` averaged over the benchmark. The reference frontier is the
**non-decreasing convex hull** of these points: for any two hull points with `c_2 ≥ c_1` it
holds that `q_2 ≥ q_1` (you never pay more for less). To realise *any* cost between two
adjacent routers `R_{θ1}, R_{θ2}`, **probabilistically interpolate**:

```
R_int(R_θ1, R_θ2, t)(x)  =  R_θ1(x) with probability t
                            R_θ2(x) with probability 1 − t
```

which yields, in expectation, a point on the straight line between the two routers' (cost,
quality) — so the achievable region is the convex hull, not just the discrete points. A
**"Zero router"** (a.k.a. zero-effort/oracle-of-hull) picks models purely from this hull with
no extra logic, serving as the baseline any *learned* router must beat.

### KEY FORMULA — AIQ (Average Improvement in Quality), reproduced exactly
```
AIQ(R_θ) = 1/(c_max − c_min) · ∫_{c_min}^{c_max}  R̃_θ  dc
```
where `R̃_θ` is the router's (interpolated, non-decreasing) **quality-as-a-function-of-cost**
curve and `[c_min, c_max]` the cost range. **AIQ is the normalised area under the
quality–cost curve** — a single scalar summarising a router across *all* cost budgets (higher
= better). It is RouterBench's headline metric, analogous to AUC but over the cost axis.
*(Transcription-risk: confirm whether `R̃_θ` is the raw or hull-projected curve and the exact
normalisation, against §3 of the paper, before using AIQ as our acceptance metric — flagged.)*

### RESULTS (headline, cite exactly)
- **Predictive routers (KNN, MLP)** reach individual-LLM-level quality at comparable or lower
  cost, **but do not significantly beat the Zero-router baseline** on most tasks — i.e. much of
  the achievable gain is already captured by simply riding the convex hull.
- **Cascading routers** (run cheap model, escalate on low judge-confidence) *"quickly
  approximate the performance of the Oracle"* when the judge is accurate; **performance
  degrades rapidly once judge error exceeds ~0.2.**
- **RAG / compound settings:** all routers *"significantly improve compared to the Zero
  Router."*
- Overall the benchmark reveals a **2–5× cost variation for comparable performance**, i.e. the
  headroom routing can capture.

---

## (3) Best-parts-to-take — for AutoFirm W1

**Adopt:**
- **Offline replay harness.** Build W1's evaluation the RouterBench way: log every model's
  output + quality + cost on a golden set once, then **replay any routing/quorum policy offline**
  against that frozen table. Deterministic, fast, no live spend — perfect for CI and the
  `evidence/` showcase. This makes router/quorum changes measurable and revertable.
- **AIQ as a single acceptance scalar.** Report **AIQ per policy** (deterministic-only,
  deterministic+learned router, ensemble-quorum) so the gateway's cost–quality competence is
  one number, plus the full quality-vs-cost curve. Pair it with PGR/APGR (RouteLLM) for pairwise
  views.
- **The Zero-router / convex-hull baseline is the bar to beat.** This is the key institutional
  discipline: a learned router that **does not beat the convex hull of the underlying models is
  worthless**. W1 must show its router (and especially its ensemble-quorum) lifts the curve
  *above* the Zero-router hull, or we ship the cheaper deterministic hull policy instead.
- **Cascade insight directly informs ensemble-quorum.** Their finding — cascades track the
  Oracle while judge-error < ~0.2, then collapse — means W1's **quorum reconciliation is only as
  good as its judge/verifier.** Budget effort into a reliable verifier and **measure its error
  rate**; gate quorum escalation on it (fail-closed to the strong model when judge confidence is
  low). This is a hard requirement, not a nicety.
- **WTP `λ` knob** maps cleanly onto a per-tenant / per-task budget setting in the gateway.

**RED flags / cautions:**
- **Benchmark-vs-real-world gap (HIGH).** RouterBench is 8 academic datasets / 64 tasks; AIQ
  rankings on it **need not hold on AutoFirm's company-building traffic.** Use RouterBench's
  *method* (replay harness, AIQ, convex-hull baseline) but build our **own golden set from our
  own telemetry** and recompute AIQ there. Never select a router because it won on RouterBench.
- **Predicted vs realised performance.** `P_{ij}` is a *prediction*; on novel prompts the
  predictor is the weak link. Keep the deterministic policy authoritative and treat learned
  scores as advisory within admissible sets only.
- **"Zero router already wins" is a warning.** If our learned router can't beat the hull, the
  added complexity (and its overfit/telemetry risk) is not justified — prefer the deterministic
  hull policy. Generality over scenario-fit.

**Could NOT fully verify:** the precise definition of `R̃_θ` inside the AIQ integral (raw curve
vs hull-projected) and the exact normalisation of `performance_score_{ij}` — confirm against §3
of the paper + the released RouterBench data schema before adopting AIQ as a gate metric.
