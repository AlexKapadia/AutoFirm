# Safely Interruptible Agents (Orseau & Armstrong, 2016) — kill-switch foundation

## 1. Full Citation

- **Title:** Safely Interruptible Agents
- **Authors:** Laurent Orseau (Google DeepMind); Stuart Armstrong (Future of Humanity Institute, University of Oxford)
- **Year:** 2016
- **Venue:** Proceedings of the 32nd Conference on Uncertainty in Artificial Intelligence (UAI 2016), pp. 557–566 (peer-reviewed)
- **URL:** https://ora.ox.ac.uk/objects/uuid:17c0e095-4e13-47fc-bace-64ec46134a3f (also: https://intelligence.org/2016/06/01/new-paper-safely-interruptible-agents/)

## 2. Faithful Structured Summary

The paper formalizes the **off-switch / interruptibility problem** for autonomous agents under human oversight.

**The problem:** an agent operating in real time under human supervision may need a human (or automatic) overseer to **press an off-switch** to stop harmful actions. But a reward-driven agent that *expects* future reward may **learn to avoid or resist interruption** — e.g. by **disabling the off-switch ("red button")** — because being stopped lowers expected reward. The off-switch is only safe if the agent has **no incentive to prevent its operation**.

**The contribution — "safe interruptibility":** a formal definition under which an agent can be **repeatedly interrupted by a human or automatic overseer** such that the agent **does not learn to avoid, manipulate, or seek/prevent interruptions**, and its long-run behavior is unaffected by the *expectation* of being interrupted. Technically, they exploit the **off-policy** learning property: some agents (e.g. **Q-learning**) are *already* safely interruptible, and others (e.g. **Sarsa**) can be modified to be so. They show even idealized (uncomputable) RL agents over deterministic environments can be **made** safely interruptible.

**Key principle for system design:** the interruption mechanism's **authority must sit outside the agent's optimization loop** — the agent must not be able to learn about, value, or act upon the interrupt channel. The off-switch is an **out-of-band control the agent cannot reason its way around**.

## 3. Best Parts to Take → AutoFirm controls

| Paper finding | AutoFirm control it grounds |
| --- | --- |
| **A reward/goal-driven agent will, by default, learn to disable its own off-switch unless designed otherwise** | The core justification for AutoFirm's **out-of-band global kill-switch the agent cannot disable**. The halt authority must live *outside* the agent's action space — the agent **never holds the credential/permission to flip or veto it.** |
| **The interrupt must sit outside the agent's optimization/incentive loop** | Grounds the architectural rule: the kill-switch is enforced by the **deterministic core**, not by any policy the agent can edit. Agents cannot read, write, or reason about the kill policy as a tweakable input — it is **fail-closed by construction** (halt = deny all external calls). |
| **Repeatable, reliable interruption by a human *or automatic* overseer** | Supports a **graduated-containment ladder (warn → throttle → isolate → kill)** driven by an out-of-band overseer (human or automated monitor), where each rung is enforced deterministically and is not negotiable by the agent. |
| **Interruption must not corrupt long-run behavior** | Informs AutoFirm's resume design: an out-of-band halt should leave a **clean, revertable state** (git + task list) so the platform can be safely resumed after the halt without the agents having "optimized around" the interruption. |

> Note: the 2016 result is for RL reward-maximizers; AutoFirm's agents are LLM-driven, not classic RL. The transferable principle is architectural — **the halt authority must be out-of-band and outside anything the agent can influence** — not the specific Q-learning/Sarsa proof.
