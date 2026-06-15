# BEST-PARTS — Toyota Production System (Ohno)

## What AutoFirm should ADOPT (and why)

### 1. The seven-wastes lens as an operations diagnostic — ADOPT
AutoFirm's operations playbook (L2.B11) and the orchestrator's self-review should carry an explicit
**waste taxonomy** mapped from physical manufacturing to agent/company operations:
- **Overproduction** → generating artifacts/deliverables no one asked for (CLAUDE §5.2 "nothing
  speculative" is literally this waste; this source gives it a name and the "worst-waste" priority).
- **Waiting** → agents blocked on a gate or another agent's output (idle context).
- **Transportation** → handing data between agents/tools more than necessary.
- **Over-processing** → re-doing work, over-engineering (CLAUDE §5.2).
- **Inventory** → half-finished branches/WIP piling up (ties to no-graveyard, CLAUDE §3.8).
- **Motion** → context-switching cost across files/tools.
- **Defects** → bugs/rework caught late (the most expensive; jidoka says stop-the-line early).
- **Build implication:** a `waste_audit` rubric for the COO/North-Star review (§2/§4.7) that grades
  each company-build run against these seven categories, producing a quantified waste report into
  `evidence/`.

### 2. Jidoka = "stop the line on defect" → fail-closed + stop-on-red — ADOPT
Jidoka's principle ("never pass a defect downstream; stop automatically") is the operations-theory
twin of CLAUDE §5.6 **fail-closed** and §3.7 stop-and-fix on RED. **Build implication:** every gate
(§4.2) is a jidoka stop point — a failing test / RED alignment finding halts forward flow until
fixed. Wire an andon-style signal: any subagent that detects an abnormality raises it rather than
working around it.

### 3. Pull over push (kanban) — ADOPT for the task system
AutoFirm should run work as **pull**: downstream demand (the goal / the next gate) pulls work, with
**WIP limits** so experiments/branches don't pile up as "inventory." **Build implication:** the task
list (TaskCreate) becomes a kanban with explicit WIP caps per phase; an agent pulls the next task
only when capacity exists, rather than fanning out unbounded work (limits context flooding, A1.4).

### 4. Heijunka (levelling) + the three M's (muda/mura/muri) — ADOPT as scheduling doctrine
Smooth the workload to avoid **muri** (overburden = context exhaustion / quota stalls — directly
relevant to the §4.8 watchdog) and **mura** (bursty fan-out). **Build implication:** the orchestrator
levels agent dispatch instead of spiking, improving resilience against quota resets.

### 5. 5 Whys + genchi genbutsu — ADOPT for the debug loop
The §3.7 iterate-to-perfection loop should use **5 Whys** root-cause analysis and **go-and-see**
(read the actual logs/outputs, not a summary) — exactly the autoresearch:debug discipline.

## What AutoFirm should REJECT / not over-apply

- **REJECT literal manufacturing mechanics** (physical kanban cards, takt time on a moving assembly
  line, supermarket inventory racks). AutoFirm is a software/services orchestrator — adopt the
  *principles* (pull, level, stop-on-defect), not the shop-floor apparatus. (Generality, CLAUDE §3.9.)
- **REJECT treating zero-inventory as an absolute.** Pure JIT is fragile to disruption (a known
  critique post-COVID). AutoFirm keeps *buffers* where determinism/safety demand it — consistent with
  TOC's buffer concept (see 04-goldratt). Don't strip all slack from safety-critical paths.
- **DEFER takt-time / line-balancing math** to the queueing source (05-little) which gives the exact,
  provable relationships AutoFirm needs for capacity claims.

## Concrete build implications (component / contract / test)
- **Component:** `operations/waste_audit` rubric (7-waste scorer) used by North-Star review.
- **Contract:** every gate is a jidoka stop; a RED/failed-test result is non-bypassable (fail-closed).
- **Test:** a determinism/efficacy test asserting that when a defect is injected at stage N, the
  pipeline *halts at N* and does not emit a downstream artifact (proves stop-the-line wiring).
