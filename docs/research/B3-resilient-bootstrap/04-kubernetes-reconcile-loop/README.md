# Kubernetes Controller / Operator Reconcile Loop (level-triggered, idempotent)

> Research note for AutoFirm — workstream **B3: Resilient Bootstrap**.
> Bar: primary-source, exact citation, faithful structured summary, the reconcile contract
> reproduced exactly, plus a "best-parts-to-take" note mapped to the W3 self-healing bootstrapper.
> Sourcing standard: CLAUDE.md §3.3 / §4.6.
> Companion note: `03-ibm-mape-k-autonomic/` (MAPE-K supplies the loop's *shape*; this note
> supplies the *safety mechanics* — level-triggered + idempotent reconcile — that make re-running
> the loop converge instead of corrupting state).

---

## 1. Full citations

1. **The Kubernetes Authors. "Controllers." *Kubernetes Documentation — Concepts › Cluster
   Architecture.*** `https://kubernetes.io/docs/concepts/architecture/controller/`
   (The canonical statement of the controller = non-terminating control loop driving current
   state toward desired state; the thermostat analogy; control-via-API-server vs direct control.)

2. **The Kubernetes SIGs `controller-runtime` project. `Reconciler` interface — package
   `sigs.k8s.io/controller-runtime/pkg/reconcile`.**
   `https://pkg.go.dev/sigs.k8s.io/controller-runtime/pkg/reconcile`
   (The canonical engineering contract: `Reconcile(ctx, Request) (Result, error)`; reconcile is
   **idempotent**, **level-based not edge-based**, and compares specified vs actual cluster
   state then acts to converge them.)

3. **B. Burns, B. Grant, D. Oppenheimer, E. Brewer, J. Wilkes. "Borg, Omega, and Kubernetes."
   *ACM Queue*, vol. 14, no. 1, 2016 (also *Communications of the ACM*, vol. 59, no. 5).**
   (The reconciliation-controller philosophy: declarative desired state + independent controllers
   that continuously reconcile observed toward intended state, preferred over imperative
   orchestration; supports robustness to component failure.)

---

## 2. Faithful structured summary

### 2.1 Controller = a non-terminating control loop (Kubernetes docs)

> "In Kubernetes, controllers are control loops that watch the state of your cluster, then make
> or request changes where needed. **Each controller tries to move the current cluster state
> closer to the desired state.**"

> "In robotics and automation, a *control loop* is a **non-terminating loop** that regulates the
> state of a system." — the **thermostat** analogy: the set temperature is the *desired state*,
> the room temperature is the *current state*, and the thermostat acts (heat on/off) to bring
> current toward desired.

A controller **"tracks at least one Kubernetes resource type."** That resource's `spec` field
expresses the **desired state**; **"the controller(s) for that resource are responsible for
making the current state come closer to that desired state."**

Two ways a controller acts:

- **Control via the API server** (e.g. the Job controller): it does not do the work directly; it
  **tells the API server to create or remove objects (Pods)**, and other control-plane
  components act on that, "and eventually the work is done."
- **Direct control** (e.g. a node autoscaler talking to a cloud provider): it reads desired state
  from the API server, then **communicates directly with an external system** to bring current
  state in line.

**Convergence is continuous, not a one-shot terminal state:**

> "Your cluster could be changing at any point as work happens and control loops automatically
> fix failures. This means that, potentially, your cluster never reaches a stable state. **As long
> as the controllers for your cluster are running and able to make useful changes, it doesn't
> matter if the overall state is stable or not.**"

### 2.2 The Reconciler contract (controller-runtime — reproduced exactly)

```go
type Reconciler interface {
    Reconcile(ctx context.Context, req Request) (Result, error)
}
```

The four load-bearing properties of the contract, faithfully:

1. **Compare desired vs actual, then act to converge:**
   > "reconcile implementations compare the state specified in an object by a user against the
   > actual cluster state, and then perform operations to make the actual cluster state reflect
   > the state specified by the user."
   Worked example from the docs: *object spec says 5 replicas, actual cluster has 1 Pod → create
   4 Pods.* (Compute the **diff**, then apply only the diff.)

2. **Level-based, NOT edge-based:**
   > "Reconciliation is level-based, meaning action isn't driven off changes in individual Events,
   > but instead is driven by **actual cluster state read from the apiserver or a local cache.**
   > For example if responding to a Pod Delete Event, the Request won't contain that a Pod was
   > deleted, instead the reconcile function **observes this when reading the cluster state and
   > seeing the Pod as missing.**"

3. **The Request carries only an identity, not the event/contents:** the `Request` is just the
   `NamespacedName` of the object to reconcile — it does **not** say which event fired or what
   changed. The reconciler must *fetch live state and figure it out itself*. This is what makes
   missed/duplicated/coalesced events harmless.

4. **Idempotent:** running `Reconcile` repeatedly for the same object must produce the same
   result. If a controller crashes and restarts it **does not replay missed events** — it reads
   current state and reconciles. If something (a human, a failure) drifts the resource, **the next
   reconcile fixes the drift.** The framework may call `Reconcile` "thousands of times per object."

### 2.3 Why level-triggered + idempotent self-heals (the key insight)

- **Edge-triggered** systems react to *the transition* ("a Pod was deleted") — if you miss the
  edge (crash, dropped event, network blip), you miss the work forever and state silently diverges.
- **Level-triggered** systems react to *the current level* ("there are 4 Pods, there should be 5")
  — they re-derive the needed action from observed reality on every pass. **A missed event is not
  fatal**: the next reconcile reads the world as it actually is and corrects it. Events are merely
  *hints to wake up and look*; correctness comes from reading state, never from the event payload.
- **Idempotence** is the safety property that makes re-running free of harm: because each pass
  applies only the *diff* between desired and observed (create the 4 missing Pods, not "create 5"),
  re-running on an already-correct system is a no-op. This is precisely why the loop can run
  "thousands of times," survive crashes, and tolerate concurrent external change.

Together: **declarative desired state + level-triggered reconcile + idempotent apply = a
continuously self-healing system that converges from *any* starting state and self-corrects drift
on the next pass.** (The Borg/Omega/Kubernetes paper frames this as the central design lesson:
declarative reconciliation controllers are more robust than imperative orchestration.)

---

## 3. Best-parts-to-take — mapped to the W3 self-healing bootstrapper

The reconcile contract is the *mechanism* that makes the MAPE-K-shaped bootstrapper (note `03-`)
**safe to re-run and impossible to half-break**. The bootstrapper is a controller; the dev/CI
environment is the managed resource; the desired state is "all doctor checks green."

| Reconcile concept | W3 bootstrapper mapping | Payoff for "always runs / never blocks" |
| --- | --- | --- |
| **Controller = non-terminating loop driving current→desired** | The bootstrapper loops its doctor→fix pass until the **doctor report** is all-green, and is safe to invoke again later. | The bootstrap is never a fragile one-shot script; it is a convergent loop. |
| **`Reconcile` = compare specified vs actual, apply the diff** | A `bootstrap_step` is one reconcile step: **`check()`** reads actual state (observe), **`apply()`** performs only the missing change (the diff). | A step that finds its precondition already satisfied does nothing — no double-install, no clobber. |
| **Level-based, not edge-based** | `check()` reads *current reality* (is the venv present? is the service up? is the var set?), **never** "what changed since last time." | If a prior run died midway, or a tool was removed out-of-band, the next run *sees the real gap and fixes it* — missed steps self-heal. |
| **Idempotent** | Every `apply()` is written to be safe to re-run: create-if-absent, start-if-stopped, set-if-unset. | Re-running the one command on a healthy env is a clean no-op; on a partial env it completes only the gaps. This is the literal "never hits blockers" property. |
| **Request carries identity, not event** | The bootstrapper doesn't trust "what the user did last"; it re-derives the whole plan from a fresh `check()` sweep. | No hidden state, no replay logic to get wrong. |
| **`degraded_mode_policy` / fail-closed** | When a step *cannot* be reconciled (missing secret, unreachable external dep), refuse the unsafe action and converge to an explicit **degraded but safe** state, reporting the gap (self-protection, CLAUDE.md §5.6). | The loop contains failure instead of aborting the whole bootstrap — it always *runs to a defined state*. |

### Design implications for W3 (1–2 key ones)

1. **Make `bootstrap_step.check()/apply()` a true reconcile step, not a script line.** `check()`
   must read *live, current* environment state (level-triggered) and `apply()` must apply *only the
   diff* and be safe to call when already-satisfied (idempotent). Then the whole bootstrapper is
   `for step in steps: if not step.check(): step.apply()` wrapped in a converge-loop that repeats
   until every `check()` passes (or a step hits `degraded_mode_policy`). This single structural
   choice is what delivers "always runs / never hits blockers": **any** starting environment —
   fresh, partial, drifted, or already-perfect — converges to green on repeated passes, and a
   crash mid-run is recovered simply by running the command again.

2. **Treat the doctor report as the controller's `status`/observed-state and `degraded_mode_policy`
   as fail-closed convergence, not crash.** The doctor sweep is the level read; the bootstrapper
   should always converge to a *named* terminal state (GREEN or explicitly-DEGRADED-with-reasons),
   never an unhandled exception. Combined with idempotence, this means the bootstrap command is
   safe to put on the auto-resume watchdog (CLAUDE.md §4.8): re-invoking it is always either a
   no-op or forward progress, never corruption.
