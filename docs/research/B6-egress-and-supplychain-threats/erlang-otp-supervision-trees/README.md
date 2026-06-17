# Erlang/OTP Supervisor Behaviour & "Let It Crash" — Supervision-Tree Resilience

## 1. Full citation

- **Primary spec:** "Supervisor Behaviour," *Erlang/OTP System Documentation — OTP Design Principles*
  - **Org:** Ericsson AB / the Erlang/OTP team
  - **URL:** https://www.erlang.org/docs/23/design_principles/sup_princ.html
- **Foundational thesis:** Joe Armstrong, *"Making Reliable Distributed Systems in the Presence of Software Errors,"* PhD thesis, Royal Institute of Technology (KTH), Stockholm, **2003** — origin of the "let it crash" / supervision-tree model.

## 2. Faithful structured summary

**What a supervisor is.** A supervisor's job is *"to keep its child processes alive by restarting them when necessary."* It manages child lifecycle: starts children in order, monitors them, terminates them in reverse order.

**Restart strategies (exact):**
- **`one_for_one`:** *"If a child process terminates, only that process is restarted."*
- **`one_for_all`:** *"If a child process terminates, all other child processes are terminated, and then all child processes, including the terminated one, are restarted."*
- **`rest_for_one`:** the crashed child and all children started *after* it terminate and restart.
- **`simple_one_for_one`:** dynamically-added instances of one child type.

**Maximum restart intensity (critical for resilience without amplification, exact):** *"If more than MaxR number of restarts occur in the last MaxT seconds, the supervisor terminates all the child processes and then itself."* Defaults `MaxR=1`, `MaxT=5s`. This is the built-in guard against an infinite restart loop consuming resources.

**Child restart types (exact):**
- **`permanent`:** *"A permanent child process is always restarted."*
- **`temporary`:** *"A temporary child process is never restarted."*
- **`transient`:** *"restarted only if it terminates abnormally"* (exit reason other than `normal`, `shutdown`, `{shutdown,Term}`).

**"Let it crash" philosophy (Armstrong, 2003):** separate the concerns of *normal operation* from *error recovery*. Don't litter worker code with defensive error handling; let a faulty process die cleanly and let a dedicated supervisor restart it from a known-good state. Errors stay **localized** and don't corrupt the wider system.

## 3. Best parts to take → AutoFirm controls

- **Grounds supervised auto-restart for the gateway and CLI sessions.** AutoFirm runs unattended; the egress gateway and each `claude` CLI session need a supervisor (systemd `Restart=`, Kubernetes liveness probe, or a parent process) that restarts a crashed component from a clean state — the direct analogue of `one_for_one`. This is the resilience answer to the gateway-as-SPOF: a crash is recovered automatically, not left dead until a human notices.
- **Maximum restart intensity = the anti-crash-loop cap.** `MaxR in MaxT` is the authoritative pattern for *bounded* restarts: AutoFirm must cap restart frequency and, on exceeding it, **escalate / halt and trip the kill-switch** rather than thrash forever. This pairs with OWASP API4's "limit number of restarts" and SRE's crash-loop warning — fail-closed when recovery isn't converging.
- **Restart-type semantics map to AutoFirm component criticality.** The gateway is `permanent` (always restart). A one-shot validation job is `temporary`/`transient`. This gives a principled, auditable restart policy instead of ad-hoc retries.
- **"Let it crash" = blast-radius isolation.** Each CLI session is an isolated supervised worker; a crash (or a poisoned/looping agent) is killed and restarted without touching sibling sessions or the deterministic core — reinforcing AutoFirm's least-privilege, per-session isolation and propose-then-dispose split (the supervisor is part of the deterministic disposer, never the LLM).
- **Escalation up the tree** grounds the out-of-band kill-switch as the top-of-tree supervisor: when local restart caps are exhausted, escalate to a platform-wide halt.
