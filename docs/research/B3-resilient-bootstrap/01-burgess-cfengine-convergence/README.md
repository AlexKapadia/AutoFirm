# Burgess — CFEngine Convergence & Convergent Operators

> Research note for AutoFirm CRO research org. Workstream **B3 — Resilient Bootstrap**.
> Bar: institution-grade, primary-sourced, exact citation, faithful reproduction (CLAUDE.md §3.3, §4.6).

---

## 1. Full citation

**Primary (foundational paper):**
Mark Burgess, *"Cfengine: A Site Configuration Engine"*. **USENIX Computing Systems**, Vol. 8, No. 3, 1995. Oslo College / University of Oslo.
PDF: <https://www.usenix.org/legacy/publications/compsystems/1995/sum_burgess.pdf>
(This is the foundational CFEngine paper introducing a high-level, language-based, *declarative* interface for system administration, where one file defines the configuration of all hosts on a network.)

**Primary (formal convergent-operator treatment — the source quoted verbatim below):**
Mark Burgess, *"A Tiny Overview of CFEngine: Convergent Maintenance Agent"*. In **Proceedings of MARS/ICINCO**, INSTICC / SciTePress, 2005. Oslo University College.
PDFs: <http://markburgess.org/papers/tiny_intro.pdf> · <https://www.scitepress.org/Papers/2005/11592/11592.pdf>
This paper restates and formalises the maintenance model fully described in Burgess (2003/2004) and gives the **explicit fixed-point equations** for convergence vs. idempotence reproduced below.

**Supporting / origin of the named concept:**
Mark Burgess, *"Computer Immunology"*. **Proceedings of LISA XII (USENIX)**, 1998 — where "convergence" was first named explicitly in system administration. (Burgess, *Tiny Overview*, §8: *"named explicitly in the Computer Immunology essay in (Burgess, 1998)"*.)

> Citation note: the fixed-point formalism (Eq. 2 below) is fully proven in Burgess, *"Configurable Immunity for Evolving Human-Computer Systems"*, **Science of Computer Programming / Theoretical Computer Science** treatments (Burgess, 2003/2004b), which the 2005 overview references as `(Burgess, 2004b)`. We reproduce the overview's statement of it exactly and attribute the proof to the 2003/2004 work rather than paraphrasing the proof loosely.

---

## 2. Faithful structured summary (key definitions reproduced exactly)

### 2.1 The model: policy, operators, classes, states

> *"Policy (P) is a description of intended host configuration. It comprises a partially ordered list of operations or tasks for an agent to check."* (§2)

> *"Operators (Ô) or primitive skills/actions are the commands that carry out maintenance checks and repairs… They describe what is to be constrained."* (§2)

CFEngine is **declarative, not imperative**: the paper states it *"is not an imperative language but has many features akin to Prolog"* (§3), and:

> *"Rather than describing the steps needed to make a change, CFEngine language describes the final state in which one wants to end up."* (Wikipedia summary of CFEngine, citing Burgess)

The agent then *"ensures that the necessary steps are taken to end up in this 'policy compliant state'"* and *"can be run again and again, whatever the initial state of a system, and it will end up with a predictable result."*

### 2.2 Convergence to an ideal state (the core principle)

From the immunity-model feature list (§2), reproduced exactly:

> *"Convergent semantics encourage every transaction to bring the system closer to an 'ideal' average-state, like a ball rolling into a potential well."*
>
> *"Once the system has converged, action by the agent desists."*

And in §8 "Convergent Regulation":

> *"Cfengine uses the idea of convergence to an ideal state. This means that, no matter how many times cfengine is run, its state will only get closer to the ideal configuration."*

### 2.3 Convergence is STRICTLY STRONGER than idempotence — the exact fixed-point equations

This is the load-bearing definition. Reproduced verbatim from §8:

> *"This is a stronger condition than idempotence as in Couch's interpretation… Since idempotence requires only*
>
> **Ô² = Ô**,
>
> *while convergence is relative to a specific policy state q₀ (Burgess, 2004a):*
>
> **Ôq = q₀**
> **Ôq₀ = q₀.    (2)"*

Interpretation (faithful to the text):
- **Idempotence** (`Ô² = Ô`): applying the operator twice equals applying it once. Re-running is a no-op *with respect to its own first application* — `f(f(x)) = f(x)`.
- **Convergence** (`Ôq = q₀` for *any* starting state `q`, and `Ôq₀ = q₀`): the operator drives **every** state `q` to the single desired policy state `q₀`, **and** `q₀` is a **fixed point** (re-application leaves it unchanged). Convergence ⇒ idempotence at `q₀`, plus a guaranteed destination *regardless of starting state*.

The convergence-over-multiple-runs guarantee (§8):

> *"The point of convergence over multiple runs is that multiple orthogonal, convergent operations will always lead to the correct configuration, no matter which part of the configuration is incorrect, or in what order things occur… they will always converge eventually."*

### 2.4 Check-then-act ("see a problem, fix it") and re-runnable repair

The agent **observes, compares to policy, and only acts on deviation**. From §8, the explicit observe→policy→act correspondence:

> *"1. Cfagent observes : X*
> *2. Policy says : X → A*
> *3. Agent says : A → Ôfile(passwd, 0644, root)"*

i.e. the agent measures the current symbol (`X`), the policy maps the desired symbol (`A`), and the operator is only invoked to restore the object to a value in the acceptable set. The paper's worked example: a file at `mode=0644` is the desired symbol `A`; a user accidentally changes it to `mode=0600` (symbol `X`); the convergent operator restores it. If the object is already compliant, no repair fires — this is the re-runnable **no-op at the fixed point**.

Recoverability of a single failed step (§8):

> *"Cfengine addresses convergence in two ways: by making each successful operation convergent in a single step, and by checking for contrary sequences. If a single step should fail or be undermined, for whatever reason (crash, interruption, changing conditions, loss of connectivity etc), it can be repeated later; this is sufficient to ensure that simple configurations converge."*

### 2.5 Acceptable-state sets (fuzzy fixed point, not a unique point)

A desired state need not be a unique value — it is a set of *"equally good"* values (§5). For `/etc/passwd mode=a+r,o-w owner=root`: *"this is not a unique specification of file permissions, but a set of acceptable 'equally good' values."* The operator restores the object to *"any one of the values in the stable set."* This matters for design: `q₀` can be a **predicate / acceptance set**, not a single literal.

### 2.6 Order-independence via orthogonality

> *"If two operations are orthogonal, it means that they can be applied independently of order, without affecting the final state of the system… this is equivalent to requiring their commutativity."* (§8)

Convergent operators that are orthogonal commute, so the agent need not enforce a global ordering — the system reaches `q₀` regardless of the order in which independent repairs run.

### 2.7 Termination / absorbing states

> *"One would like to secure the property that changes made to a configuration move towards a definite state, terminate after a small number of iterations, and that the route taken back towards the ideal state is unique and unidirectional… We require there to be absorbing states, or for operations to behave like semi-groups."* (§8)

---

## 3. Best-parts-to-take — mapped to the W3 idempotency / bootstrap design

The W3 desired-state bootstrap contract is a **direct, regulator-defensible application of Burgess's convergent-operator fixed point**. Each design element below cites the exact principle it rests on.

### 3.1 `bootstrap_step` IS a convergent operator `Ô` (justifies `check() → apply()`)
Model each typed `bootstrap_step` as a convergent operator with target capability-state `q₀`:
- **`check() -> already_applied?`** is Burgess's *observe* step — *"Cfagent observes : X"* — measuring the current symbol and testing membership in the acceptance set for `q₀`.
- **`apply()`** is the convergent operator `Ô` — invoked **only when `check()` reports the state is not in `q₀`** (the *"see a problem, fix it"* / check-then-act rule, §8 / §4.2-Traugott).
- The contract **`check() → apply()`** is exactly what guarantees `Ôq = q₀` (drive any starting state to desired) **and** `Ôq₀ = q₀` (no-op at the fixed point). Because `check()` short-circuits when already-applied, the operator satisfies the *stronger-than-idempotence* property (Eq. 2): re-running the whole bootstrapper is a **guaranteed no-op** on an already-bootstrapped environment, not merely an idempotent re-write.

> **Design implication (load-bearing):** Do NOT implement `apply()` as a blind "run the imperative steps again." Implement `check()` as the membership test against the acceptance set for `q₀`, and only call `apply()` on deviation. This is what makes the bootstrapper provably re-runnable (`Ô² = Ô` at minimum, `Ôq = q₀` in full) rather than accidentally idempotent.

### 3.2 Acceptance sets, not literals (from §2.5)
`check()` should test membership in an **acceptance predicate**, not bit-equality against one literal, mirroring the *"set of acceptable 'equally good' values"*. e.g. "Python ≥ 3.11 present" not "exactly 3.11.4". This keeps W3 **general, never overfit** (CLAUDE.md §3.9) — the fixed point `q₀` is a region, not a point.

### 3.3 Environment bootstrapper = orthogonal convergent operators, order-free (from §2.6)
Compose the environment bootstrapper from steps that are **orthogonal** wherever possible so they commute (§8). For genuinely dependent steps, encode an explicit partial order (Burgess: policy is a *"partially ordered list"*, §2). Independent steps may run in any order / in parallel and still converge — *"no matter… in what order things occur."*

### 3.4 Re-runnable single-step recovery (from §2.4)
Each step must be safe to repeat after `"crash, interruption, changing conditions, loss of connectivity"` — *"it can be repeated later; this is sufficient to ensure that simple configurations converge."* This justifies W3 running the full bootstrap on every start: a partially-bootstrapped environment converges on the next run.

### 3.5 `degraded_mode_policy` — fail a capability closed, keep the platform up
Burgess: *"Once the system has converged, action by the agent desists"*, and policy *"allows for short-term errors."* W3 mapping: if a `bootstrap_step` cannot reach `q₀` (e.g. an optional dependency is unavailable), the `degraded_mode_policy` records that **capability** as unavailable and **fails that capability closed** (CLAUDE.md §5.6 fail-closed) — but the platform stays up with the capability disabled, rather than the whole boot aborting. The step is **not marked converged**, so a later run re-attempts convergence to `q₀` automatically (§3.4). This is the convergence-as-best-effort stance (CFEngine *"statistical compliance"*: *"a system can never guarantee to be exactly in an ideal state… one approaches (converges) towards the desired state by best-effort"*).

### 3.6 `doctor` report = the observe/compliance channel
Burgess frames maintenance as a Shannon **error-correction channel** comparing observed state to policy (§2.2 immunity model; §8). The W3 `doctor` report is the **read-only observe pass** of every step's `check()`: for each capability it reports `converged | degraded | failed`, **which step fired and why** (CLAUDE.md §3.11 explainability), and what `q₀` was expected vs. what `X` was observed — without invoking `apply()`. This is the auditable, zero-numerical-error decision log.

### 3.7 Determinism & explainability
Convergent operators give **deterministic destinations** (`Ôq = q₀`), supporting the W3 determinism tests (identical environment → identical converged state) and the requirement that each decision justifies itself by stating the rule that fired.

---

## One-line takeaway
A CFEngine **convergent operator** drives *any* starting state to a single desired policy state `q₀` **and** holds it there (fixed point), a condition **strictly stronger than idempotence** (`Ô²=Ô`); this is the exact theory that justifies W3's `check() → apply()` contract and its guaranteed re-runnable no-op.
