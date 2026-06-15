# SYNTHESIS — B11 Operations & Supply/Delivery Foundations (L1.B11.1)

> Surveyed the FULL operations-foundations space, then chose what AutoFirm's operations playbook
> (L2.B11) should adopt. Implements DEPTH-RUBRIC §4 (survey everything, adopt/reject each) and §5
> (concrete, general, build-relevant). Every claim is sourced in the per-source folders 01-09.

## 1. The surveyed alternative space (with ADOPT/REJECT/DEFER)

| # | Framework | Origin (primary) | Domain | Verdict for AutoFirm |
|---|---|---|---|---|
| 01 | **Toyota Production System** (JIT, jidoka, 7 wastes, kanban, heijunka) | Ohno 1988 | Manufacturing flow | **ADOPT principles** (waste lens, jidoka=fail-closed, pull/WIP, level); REJECT shop-floor apparatus |
| 02 | **Lean Thinking** (value, value stream, flow, pull, perfection) | Womack & Jones 1996 | General / services | **ADOPT** as the playbook backbone (most general; value-stream map) |
| 03 | **SCOR** (Plan/Source/Make/Deliver/Return/Enable; 5 attributes) | ASCM/APICS 1996-2022 | Supply chain | **ADOPT** as the supply/delivery process + KPI skeleton |
| 04 | **Theory of Constraints** (5 focusing steps, DBR, throughput acct.) | Goldratt 1984/1990 | Flow / bottlenecks | **ADOPT** as the optimization algorithm + release rule |
| 05 | **Little's Law** (L = lambda*W) | Little 1961 (OR 9(3)) | Queueing / flow math | **ADOPT** as the deterministic capacity primitive (keystone) |
| 06 | **Service-Profit Chain** (ops->employee->customer->profit) | Heskett et al. 1994 | Service ops | **ADOPT** for service-dominant industries (independently validated) |
| 07 | **Service Blueprinting** (front/back-stage, fail points) | Shostack 1984 | Service process design | **ADOPT** as the service value-stream-map analogue |
| 08 | **Six Sigma / DMAIC** (variation reduction, DPMO) | Motorola 1986; Harry 2000 | Quality / process control | **ADOPT** DMAIC + DPMO lightly; REJECT belt bureaucracy & unshifted-sigma claims |
| 09 | **DORA / Accelerate** (4 keys: DF, LT, CFR, MTTR) | Forsgren/Humble/Kim 2018 | Software/services delivery | **ADOPT** as AutoFirm's own + client-software delivery KPIs |

**Explicitly excluded (scope boundary, named per DEPTH-RUBRIC §4.3):**
- *MRP/MRP-II/ERP planning mechanics, EOQ/inventory lot-sizing math, S&OP cadence detail* — these are
  L2.B11 *implementation* choices, not L1 foundations; defer to the applied layer.
- *Specific queueing models (M/M/1, M/G/k, Erlang-C)* — deferred from L1; start with distribution-free
  Little's Law and escalate only when waiting-time distributions are genuinely needed (a follow-up source).
- *Agile/Scrum/Kanban-method ceremonies* — the *flow* substance is covered by lean (02) + DORA (09);
  ceremony detail belongs to B14 software-delivery, not operations foundations.
- *Total Quality Management / Deming's 14 points* — Deming's PDCA/variation thinking is upstream of
  both Six Sigma (08) and lean; recorded as ancestry, not separately adopted (avoids redundancy).

## 2. How the adopted pieces compose (the unified B11 model)

The nine sources are NOT a menu of rivals — they compose into **one** operations model with a
**deterministic core + an evidence-driven measurement layer**, exactly the CLAUDE §3.5 hybrid stance:

1. **Lean (02)** supplies the backbone: define customer value -> map the value stream -> make it flow
   -> pull -> improve. The value-stream artifact is a **lean VSM** for product flows and a **service
   blueprint (07)** for service flows (industry-parameterized, B12).
2. **SCOR (03)** standardizes the process decomposition (Plan/Source/Make/Deliver/Return/Enable) and
   the balanced KPI set (Reliability/Responsiveness/Agility/Cost/Asset-efficiency), so the model is
   cross-industry by construction.
3. **Little's Law (05)** is the keystone math binding the whole model: Cycle Time = WIP / Throughput.
   It quantifies every flow claim deterministically and proves the levers are WIP and throughput.
4. **TOC (04)** says *where* to act (the constraint) and *how to release work* (drum-buffer-rope), and
   **TPS (01)** says *how to run the line* (pull + WIP limits + stop-on-defect/jidoka + level/heijunka).
   Together they are the control loop around the Little's-Law math.
5. **Six Sigma/DMAIC (08)** is the structured improvement protocol that reduces variation at the
   constraint; **DORA (09)** is the delivery-operations KPI layer for software/services (Lead Time =
   the "W" of the software value stream — closing the loop back to Little's Law).
6. **Service-Profit Chain (06)** overlays the causal economics for service-dominant companies
   (ops->employee->customer->profit), telling the playbook which KPI (loyalty/retention) is profit-linked.

## 3. Concrete recommendation for AutoFirm (build-relevant, general)

**Adopt a single, industry-parameterized operations engine** with these components (all named to map
to BEST-PARTS files):
- `operations/littles_law` — exact L=lambda*W + steady-state fail-closed guard (KEYSTONE; backs B9/B11/B14).
- `operations/value_stream_map` (lean, product) + `operations/service_blueprint` (Shostack, service) —
  selected by industry (B12).
- `operations/scor_process_model` + `operations/scor_kpi` (5 attributes; Perfect-Order-Fulfillment &
  Cash-to-Cash defaults).
- `operations/constraint_optimizer` (TOC 5 steps) + `operations/throughput_accounting` (T/I/OE) +
  a drum-buffer-rope governing AutoFirm's own task release.
- `operations/dmaic_engine` + `operations/quality_metrics` (DPMO/sigma, variation).
- `operations/service_profit_chain` (service economics) + `operations/dora_metrics` (DF/LT/CFR/MTTR).
- `operations/waste_audit` (Ohno's 7 wastes, applied to agent operations + North-Star review).

**Determinism & testing (CLAUDE §3.6, §3.11):** Little's Law, throughput accounting, SCOR KPIs, DPMO,
and the four DORA metrics are **all exact deterministic formulas** -> each ships with boundary-exact
unit tests, property tests (L == lambda*W), and fail-closed guards (unstable queue; missing customer
value; speed-metric without its paired stability metric). These numeric KPIs feed `evidence/` directly.

**Generality proof obligation (CLAUDE §3.9, B12 panel):** the engine must produce a sensible result
for ALL 8 panel industries — lean VSM + DORA lead for SaaS; SCOR + TPS for manufacturing; service
blueprint + service-profit chain for consulting/healthcare/restaurant/marketplace. Overfitting the
operations model to one industry is an instant FAIL.

## 4. Reproducibility
Every framework above is re-derivable from the primary citations in folders 01-09 (Ohno 1988; Womack &
Jones 1996; ASCM/APICS SCOR-DS; Goldratt 1984/1990; Little 1961 *Operations Research* 9(3):383-387;
Heskett et al. 1994 HBR + Kamakura et al. 2002 Marketing Science; Shostack 1984 HBR + Bitner et al.
2008 CMR; Motorola/Harry 2000 + NIH StatPearls; Forsgren/Humble/Kim 2018 *Accelerate*). The one
load-bearing formula (L=lambda*W) is from a peer-reviewed theorem with a formal proof.
