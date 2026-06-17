# W3 — Idempotency & Degraded-Mode Specification

> **Workstream 3: effortless, idempotent, self-healing one-command setup that "always runs" and "never hits blockers".**
> This spec is the design contract derived from the B3 research library (folders `01`–`10` in this directory). It wraps AutoFirm's existing `make install` / `make test` (see `Makefile`) and the fail-fast gated pipeline in a typed, idempotent, self-healing bootstrap.
> Status: **research-phase design draft** (not yet implemented). Institution-grade bar per `CLAUDE.md` §3.2.

---

## 0. Research provenance (what each principle rests on)

| W3 mechanism | Primary source(s) | Folder |
| --- | --- | --- |
| `check()→apply()` re-runnable no-op | Burgess, convergent operator (`Ôq=q₀`, `Ôq₀=q₀`); idempotence `f(f(x))=f(x)` | `01`, `02` |
| Scope a *fully-enumerated* capability baseline; deterministic order | Traugott, congruence > convergence; "same changes, same order" | `02` |
| Self-healing converge loop (Monitor→Analyze→Plan→Execute) | IBM MAPE-K; Kephart & Chess self-CHOP | `03` |
| Level-triggered idempotent reconcile; missed events self-heal next pass | Kubernetes controller / controller-runtime `Reconcile` | `04` |
| Crash-atomic durable state ledger (write-temp→fsync→rename→fsync-dir) | Pillai et al., OSDI '14 | `05` |
| Idempotent forward replay; "skip if already done" | ARIES "repeating history" + LSN redo rule | `06` |
| Per-capability circuit breaker + bulkhead isolation + fail-fast | Nygard, *Release It!* | `07` |
| Degrade non-critical / fail-static / fail-closed-vs-open | Google SRE book; §5.6 | `08` |
| Config (keys) in environment; isolate dependencies (venv); dev/prod + OS parity | Twelve-Factor (II, III, IV, V, X) | `09` |
| Normalized one-command entry, safe on fresh-clone AND re-run | GitHub "Scripts to Rule Them All" | `10` |

**Cross-link:** B3 is the *bootstrap-level* crash-resume substrate. The *agent/long-horizon* recovery semantics live in `docs/research/A3-long-horizon-autonomy/` — `08-garcia-molina-sagas` (compensating transactions) and `09-elnozahy-rollback-recovery` (checkpoint/rollback). A3's sagas and checkpoints are only as safe as B3-05's atomic-write primitive; B3-06 (ARIES idempotent redo) is the principle A3 inherits. Complementary layers, no duplication.

---

## 1. The precise idempotency contract

### 1.1 The typed `BootstrapStep`

Every unit of setup is a typed step exposing two pure-intent methods, plus metadata. This is a Kubernetes-style reconcile step (`04`) realising a Burgess convergent operator (`01`).

```python
class StepState(Enum):
    SATISFIED  = "satisfied"   # check() passed; apply() is a no-op
    APPLIED    = "applied"     # apply() ran and converged this run
    DEGRADED   = "degraded"    # capability unavailable; platform stays UP (see §2)
    FAILED     = "failed"      # security/required step could not converge → fail closed

class BootstrapStep(Protocol):
    id: str                      # stable, self-documenting (e.g. "venv.create")
    requires: tuple[str, ...]    # ids that must be SATISFIED/APPLIED first (DAG edge)
    criticality: Criticality     # REQUIRED | SECURITY | OPTIONAL  (selects fail mode, §2)

    def check(self, env: EnvProbe) -> bool:
        """Membership test for the desired state q₀. TRUE ⇒ already converged ⇒
        apply() MUST NOT run. Read-only, side-effect-free, fast. (Burgess: observe X
        against acceptance predicate; K8s: read live current state, level-triggered.)"""

    def apply(self, env: EnvProbe) -> None:
        """Converge to q₀. MUST be safe to call when partially-applied (crash mid-apply).
        Fires only on deviation. After apply(), check() MUST return TRUE."""
```

### 1.2 The contract clauses (binding)

1. **Convergence (Burgess `01`).** For any starting environment state `q`, `apply()` drives it to the desired acceptance set `q₀`; and `q₀` is a fixed point. Formally the operator satisfies `Ôq = q₀` and `Ôq₀ = q₀`. Convergence ⊃ idempotence (`f(f(x))=f(x)`).
2. **`check()` gates `apply()` (`01`,`04`).** The bootstrapper NEVER calls `apply()` without `check()` returning false first. This — not "running the install command twice happens to be safe" — is what makes a re-run a **provable no-op**. Accidental idempotence is forbidden.
3. **Acceptance by predicate, not literal (generality, §3.9).** `check()` tests a property (`python >= 3.11`, `import autofirm succeeds`, `gitleaks on PATH`), never an exact fixture value. No magic constants that only pass the sample environment.
4. **Crash mid-`apply()` is safe to resume (`05`,`06`).** `apply()` is forward-only and re-entrant: if the process dies partway, re-running `check()→apply()` converges. No undo/compensation at this layer (that's A3's saga concern). Mirrors ARIES redo-only "repeating history".
5. **Durable, crash-atomic ledger (`05`).** Completed-step state is recorded to a durable ledger written via the **atomic-rename protocol**:
   ```
   1. write JSON to  .autofirm/bootstrap_ledger.json.tmp   (same directory as target)
   2. fsync(tmp_fd)                 # data durable BEFORE the swap — enforces ordering
   3. os.replace(tmp, target)       # atomic dir-entry swap: old-or-new, never torn
   4. fsync(dir_fd)                 # make the rename itself durable
   ```
   A crash leaves the ledger fully-old or fully-new, never partially written.
6. **`check()` is the source of truth; the ledger is an audit/optimisation cache (`06`).** On resume the bootstrapper still re-runs `check()` for every step in DAG order; the ledger lets it *skip the work fast* and is the audit record, but the live `check()` is authoritative (level-triggered, `04`). If the ledger and reality disagree, reality wins — self-healing drift correction.
7. **Deterministic order (`02`).** Steps form a DAG via `requires`; topological order is stable across runs ("same changes, same order"). Orthogonal steps may run in any order (commutativity), but the resolved order is reproducible.
8. **Converge loop (`03`,`04`).** The bootstrapper is a MAPE-K loop: `for step in topo_order: if not step.check(env): step.apply(env)`, then re-verify; it always terminates in a **named** state (all-GREEN, or explicitly DEGRADED with reasons), never an unhandled exception. Safe under the §4.8 auto-resume watchdog because re-invocation is always a no-op or forward progress.

### 1.3 The `doctor` report (read-only Monitor + Analyze, `03`)

`doctor` runs every step's `check()` only (never `apply()`), and prints, per step: `id`, `criticality`, observed-vs-desired, and resulting `StepState`. It is the read-only self-knowledge surface — like `kubectl get` / a K8s status. Exit code: `0` if no `FAILED` step (DEGRADED is allowed and reported), non-zero if any required/security step is `FAILED`.

---

## 2. Degraded-mode policy

**Principle (`07`,`08`, §5.6).** A missing *optional* dependency degrades **only that capability** (bulkhead isolation — one dead dependency cannot sink the ship), emits an audit event, and the platform stays UP. A missing *security/compliance* capability **fails closed** (refuses the dependent action) — it never silently degrades to insecure. Each capability is a circuit breaker (`enabled → degraded/open → probing/half-open → enabled`); every state transition is audited; degraded capabilities are re-probed so they self-heal when the key/gateway returns. **Never a whole-platform hard block.**

The deciding column is **`criticality`**: `OPTIONAL` → degrade; `SECURITY`/`REQUIRED` → fail closed for that capability (but still not a silent crash — it converges to a named `FAILED`/`DEGRADED` state and reports).

### 2.1 Degraded-mode policy table

| Missing / failing dependency | Criticality | Bootstrap action | Audit event | Resulting platform state |
| --- | --- | --- | --- | --- |
| **Provider API key absent** (e.g. LLM/model egress key) | OPTIONAL (capability) | Disable only that provider's capability; mark breaker **open**; schedule re-probe. Other providers/capabilities unaffected (bulkhead). | `capability.degraded{cap=provider:X, reason=key_absent}` | **UP, degraded** — platform & all key-independent work run; calls to provider X are refused-for-X (fail-closed *for that capability*), not platform-wide. |
| **Gateway / provider endpoint unreachable** (network/5xx/timeout) | OPTIONAL (capability) | Fail fast (`07`); trip breaker **open**; serve **fail-static** last-known-good where applicable; half-open re-probe on interval. | `capability.circuit_open{cap=gateway:Y, reason=unreachable}` → `capability.circuit_closed` on recovery | **UP, degraded** — dependent capability paused & auto-restored on recovery; rest of platform unaffected. |
| **venv missing / incomplete** | REQUIRED | This is a *convergeable* step, not a degrade: `apply()` creates the venv from the pinned manifest (`make install`). Self-heals. | `bootstrap.step_applied{id=venv.create}` | **UP after convergence** — re-running the one command fixes it (the self-heal *is* the re-run). |
| **Dependency partially installed / corrupted** | REQUIRED | `check()` detects deviation; `apply()` re-installs (idempotent). No degrade. | `bootstrap.step_applied{id=deps.install}` | **UP after convergence.** |
| **Migration pending** (schema/state-store behind) | REQUIRED | `apply()` runs the migration forward (idempotent / versioned, ARIES-style skip-if-applied `06`). If migration *cannot* run (e.g. DB unreachable), see DB row. | `bootstrap.step_applied{id=migrate}` or `bootstrap.step_blocked{id=migrate}` | **UP after convergence**; if blocked → DB-capability degraded, platform up. |
| **State store / DB unreachable** | OPTIONAL→ for stateless work | Degrade stateful capability only; queue/refuse writes-for-that-store (fail-closed for the store); breaker re-probe. | `capability.degraded{cap=store:Z, reason=unreachable}` | **UP, degraded** — stateless work proceeds; stateful work paused & restored on recovery. |
| **Secret-scanner missing** (`gitleaks` absent) | SECURITY | **Fail closed**: refuse to mark the secret-scan capability satisfied; `doctor` reports `FAILED`; do NOT silently skip (mirrors `make secretscan` fail-closed notice). Platform may still boot for non-sensitive work, but commit/egress paths that require the scan are refused. | `security.control_unavailable{control=secret_scan}` (append-only) | **UP, but the gated security path is refused** — fail-closed per §5.6; never degrade a security control to "off". |
| **Tamper-evident / audit-log sink unwritable** | SECURITY | **Fail closed** on the audited action (refuse), since the audit invariant (§5.6) cannot be upheld. | `security.audit_unavailable` (best-effort + local durable) | **Audited actions refused**; non-audited platform functions may continue. |
| **Analysis-only deps missing** (matplotlib/graphviz) | OPTIONAL | Degrade evidence/plotting capability only; runtime untouched (enforces ADR-001 §5 runtime/analysis split). | `capability.degraded{cap=analysis_render}` | **UP, degraded** — engine & tests run; only evidence rendering paused. |

> **Rule of thumb (one line):** *OPTIONAL → bulkhead-isolate + circuit-break + audit + re-probe (platform stays up). SECURITY/REQUIRED → converge if possible; if not, fail **closed** for that path and report — never degrade a security control, never block the whole platform.*

---

## 3. The W3 acceptance metric

W3 is **done** only when all of the following are objectively true (institution-grade gate, `CLAUDE.md` §4.2):

1. **One-command, OS-portable green (`09`,`10`).** From a **clean clone with no secrets present**, a single normalized command produces a green `make test` on **Windows AND Linux** — same command, parity across both OSes (Twelve-Factor X; Scripts-to-Rule-Them-All fresh-checkout property). The bootstrap wraps `make install` + the `make test` gate chain (`lint types unit mutation sast contract secretscan`).
2. **Idempotent re-run = asserted no-op (`01`,`04`).** Running the bootstrap a second time on a converged tree performs **zero mutations** — asserted, not assumed: every step's `check()` returns true, `apply()` is never called, ledger unchanged. A test asserts the no-op (e.g. mutation-counter == 0).
3. **Crash-resume converges (`05`,`06`).** Injecting a crash at every `(side-effect, ledger-write)` boundary and re-running the one command yields a final state **identical** to an uninterrupted run. Tested by crash-injection harness; atomic-rename ledger guarantees no torn state.
4. **Degraded-mode never hard-blocks (`07`,`08`).** With any single OPTIONAL dependency removed (no provider key, gateway down, analysis deps absent), the platform boots **UP, degraded**; `make test` for the no-secrets path still passes; the degraded capability is audited and auto-restores on a re-probe once the dependency returns. With a SECURITY control absent, the dependent path is refused (fail-closed) and reported — verified to never silently proceed and never block unrelated work.

**Verification owner:** these four are encoded as the W3 acceptance suite (adversarial + crash-injection + cross-OS in CI). Coverage/mutation gates are necessary-not-sufficient per §3.6; the acceptance signal is items 1–4 holding under the hardest cases.
