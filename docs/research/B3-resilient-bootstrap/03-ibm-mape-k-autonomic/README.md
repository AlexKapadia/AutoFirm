# IBM MAPE-K & the Vision of Autonomic Computing (self-CHOP)

> Research note for AutoFirm — workstream **B3: Resilient Bootstrap**.
> Bar: primary-source, exact citation, faithful structured summary, key loops reproduced
> exactly, plus a "best-parts-to-take" note mapped to the W3 self-healing bootstrapper.
> Sourcing standard: CLAUDE.md §3.3 (deep peer-reviewed/primary research, exact citation,
> never misrepresent a formula/finding) and §4.6 (tidy `docs/research/`, one folder per source).

---

## 1. Full citations

1. **IBM. *An Architectural Blueprint for Autonomic Computing.* IBM White Paper, 4th edition,
   June 2006.** IBM Corporation, Autonomic Computing.
   (The canonical statement of the MAPE-K control loop, the autonomic manager / managed
   resource / touchpoint model, and the sensors+effectors manageability interface.)

2. **J. O. Kephart and D. M. Chess. "The Vision of Autonomic Computing." *IEEE Computer*,
   vol. 36, no. 1, pp. 41–50, January 2003.** DOI: 10.1109/MC.2003.1160055.
   (The foundational paper that frames autonomic computing by analogy to the human autonomic
   nervous system and defines the four self-management properties — "self-CHOP".)

Supporting/secondary references consulted for faithful reproduction of the loop and the
self-* definitions: the SENG-371 lecture transcription of the IBM MAPE-K reference model
(University of Victoria, `engr.uvic.ca/~seng371/lectures/L6-371-S13-bw.pdf`) and the
*Autonomic computing* article on Wikipedia (`en.wikipedia.org/wiki/Autonomic_computing`),
cross-checked against the primary citations above.

---

## 2. Faithful structured summary

### 2.1 The vision (Kephart & Chess, 2003)

The driving thesis is that software/hardware complexity is outrunning the ability of human
administrators to install, configure, tune, heal, and protect systems by hand; the proposed
escape is **self-management** — systems that run themselves under high-level objectives set
by humans, exactly as the **human autonomic nervous system** governs heart rate, respiration,
and homeostasis *without conscious intervention*. The administrator states *what* is wanted
(policy/goals), not *how* to achieve it; the system continuously regulates itself to meet that
intent. The four self-management properties (**self-CHOP**) are defined as:

| Property | Definition (faithful) |
| --- | --- |
| **Self-configuration** | Automatic configuration of components and the system, following high-level policy; components dynamically adjust to incorporate new components and adapt to their environment. |
| **Self-healing** | Automatic **discovery, diagnosis, and correction of faults** — the system detects, isolates, and repairs problems (software or hardware) to keep functioning. |
| **Self-optimization** | Automatic **monitoring and control of resources** to ensure optimal functioning with respect to the defined requirements — continual tuning of parameters and resource use. |
| **Self-protection** | **Proactive identification and protection from arbitrary attacks** and cascading failures — anticipates, detects, and defends against threats. |

These are emergent properties of a system whose elements each run a self-managing **control
loop**; that loop is specified concretely by IBM's blueprint as MAPE-K.

### 2.2 The autonomic element: manager, managed resource, touchpoint

The architectural unit is the **autonomic element** = an **autonomic manager** plus the
**managed resource(s)** it governs, connected through a **manageability interface** called the
**touchpoint**. The touchpoint exposes exactly two kinds of manageability endpoint:

- **Sensors** — provide the ability to *observe* the managed resource: retrieve current state,
  emit metrics, and surface events ("get" / "notify").
- **Effectors** — provide the ability to *change* the managed resource: apply configuration,
  carry out actions, set parameters ("set" / "call").

The autonomic manager **reads via sensors and acts via effectors** — a closed external
feedback loop wrapped around the resource. Autonomic managers themselves expose a touchpoint,
so managers can be composed hierarchically (a higher manager treats a lower one as a managed
resource), which is how local self-management aggregates into system-wide self-management.

### 2.3 The MAPE-K control loop (reproduced exactly)

The autonomic manager implements an intelligent control loop with four functions operating
over a shared **Knowledge** base — **M·A·P·E over K**:

```
                 ┌───────────── Autonomic Manager ─────────────┐
                 │                                              │
       Analyze ──┼──► Plan                                      │
          ▲      │      │                                       │
          │      │      ▼                                       │
       Monitor   │   Execute            (all four share K)      │
          ▲      │      │                                       │
          │      │      ▼                                       │
          │      │   ┌──────── Knowledge (K) ────────┐          │
          │      │   └───────────────────────────────┘          │
          └──────┼──── Sensors        Effectors ──────┘         │
                 └──────────│──────────────│────────────────────┘
                            ▼              ▼
                 ┌──────── Managed Resource (Touchpoint) ───────┐
                 └──────────────────────────────────────────────┘
```

- **Monitor (M).** Collects, **aggregates, correlates, and filters** details (metrics,
  topology, configuration, offered capacity, throughput, events) from the managed resource via
  its **sensors**, and reports the salient, processed state up to Analyze. It is the "what is
  true right now" function.

- **Analyze (A).** Provides mechanisms to **correlate and model complex situations**; it
  interprets the monitored state against the Knowledge base (policies, models, history),
  **determines whether a change is required**, and can predict future states. It answers "is
  the current state acceptable, and if not, what is wrong?"

- **Plan (P).** Constructs the set of actions needed to achieve the goals/objectives — a
  **policy-driven change plan** (a sequence of actions / a workflow). It answers "what should
  be done to move toward the desired state?"

- **Execute (E).** Carries out the planned changes against the managed resource through its
  **effectors**, updating Knowledge with the actions taken. It answers "do it." 

- **Knowledge (K).** The **shared** data store used by all four functions: standard policies,
  symptoms, change plans, topology, metrics, logs, and learned models. Knowledge persists
  *across* loop iterations, which is what lets the loop learn and stay coherent over time.

**The loop is continuous and non-terminating** (analogous to a regulatory feedback loop): the
manager perpetually senses, reasons, and acts to keep the managed resource within policy. A
single self-CHOP property is just this loop specialised — e.g. **self-healing** = the loop
where Monitor detects a fault symptom, Analyze diagnoses it, Plan selects a repair, Execute
applies the repair through effectors, with Knowledge supplying known symptoms→remedies.

---

## 3. Best-parts-to-take — mapped to the W3 self-healing bootstrapper

The W3 one-command bootstrapper that "always runs / never hits blockers" **is an autonomic
element**: the bootstrapper is the *autonomic manager*, and the dev/CI environment (toolchains,
venv, services, config, secrets-presence) is the *managed resource*. MAPE-K supplies the exact
shape of its control loop and self-CHOP supplies its quality bar.

| MAPE-K / self-CHOP concept | W3 bootstrapper mapping | Why it justifies "always runs / never blocks" |
| --- | --- | --- |
| **Monitor + Analyze** | The **doctor report** — probe the environment (sensors: `check()` calls reading tool versions, paths, service health) and diagnose which preconditions are unmet. | The doctor *observes current state* and *names the gap* before any action — the M+A half of the loop. No blind action. |
| **Plan + Execute** | The **self-healing bootstrapper** — from the doctor's diagnosis, construct the ordered repair plan and apply it (effectors: install/create/start/repair). | This is the P+E half: turn "what's wrong" into "do exactly these fixes," i.e. self-healing per Kephart & Chess (discover → diagnose → correct faults). |
| **A single `bootstrap_step` with `check()` / `apply()`** | One reconcile-style autonomic step: `check()` = sensor probe (Monitor), `apply()` = effector action (Execute), and the step is only applied when `check()` says it must be. | Each step is its own tiny MAPE loop; the bootstrapper is a *composition* of autonomic elements — exactly IBM's hierarchical-manager pattern. |
| **`degraded_mode_policy`** | **Self-protecting, fail-closed** behaviour: when a precondition is missing/ambiguous (e.g. a secret or external dependency is absent), refuse the unsafe path and run in an explicitly-degraded, safe mode rather than proceeding. | Maps to **self-protection** and to CLAUDE.md §5.6 "fail closed". The loop never crashes the operator; it contains the blast radius and reports. |
| **Knowledge base (K)** | The bootstrapper's known **symptom→remedy table** and recorded prior runs/policies. | Lets the loop converge faster and learn — same symptom resolves the same way every run. |
| **Continuous, non-terminating loop** | The bootstrapper **re-runs its full M→A→P→E pass until the doctor reports all-green**, then is safe to re-run later. | A continuously-convergent loop is precisely why it "always runs": each pass drives current state closer to desired state; a partially-broken environment is *healed on the next pass*, not a hard failure. |

**Design implication (carries into the reconcile note `04-`):** Structure the bootstrapper as a
**MAPE-K control loop, not a linear script**. A linear "install A; then B; then C" script
fails the moment any prerequisite is already-present, partially-present, or externally changed.
An autonomic-manager-shaped bootstrapper instead *senses desired-vs-current per step, plans only
the missing fixes, executes via idempotent effectors, and loops to convergence* — which is what
makes a one-command bootstrap robust enough to "always run / never hit blockers." Self-healing
(repair faults) and self-protection (fail-closed degraded mode) are the two self-CHOP properties
the bootstrapper must exhibit; self-configuration is what each `apply()` performs.

The reconcile/level-triggered/idempotent mechanics that make this loop *safe to re-run* are the
subject of the companion note **`04-kubernetes-reconcile-loop/`**.
