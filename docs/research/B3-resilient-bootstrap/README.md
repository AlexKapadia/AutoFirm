# B3 — Resilient, Idempotent Bootstrap (Workstream 3) — Research Library

Deep, primary-sourced research for a **resilient, idempotent bootstrap** that can crash mid-apply
and resume safely, degrade gracefully, and converge to a desired state from any starting point.
Institution-grade bar; research gates building (CLAUDE.md §2 CRO, §3.3, §4.6). One folder per source.

## Sources (one folder per source — §4.6)

| Folder | Source | One-line takeaway |
|--------|--------|-------------------|
| `01-burgess-cfengine-convergence` | Burgess — CFEngine (USENIX LISA 1995; MARS 2005) | **Convergent operators** drive a system to a fixed point; `Ô² = Ô` (idempotence), `Ôq₀ = q₀` (convergence). |
| `02-traugott-congruence-vs-convergence` | Traugott & Brown (LISA 2002) | **Order matters**: congruence (rebuild-from-baseline) vs convergence vs divergence; convergence alone never reaches congruence. |
| `03-ibm-mape-k-autonomic` | IBM Autonomic Computing blueprint; Kephart & Chess (IEEE 2003) | **MAPE-K loop** (Monitor-Analyze-Plan-Execute over shared Knowledge) — the self-managing control loop. |
| `04-kubernetes-reconcile-loop` | Kubernetes / controller-runtime docs | **Level-triggered, idempotent reconcile** to desired state; `Reconcile(ctx, req) (Result, error)`. |
| `05-pillai-crash-consistency` | Pillai et al. (OSDI 2014) | Crash-consistent update = `write-temp → fsync(tmp) → rename → fsync(dir)`; basis of a crash-safe checkpoint. |
| `06-aries-idempotent-recovery` | Mohan et al. — ARIES (ACM TODS 1992, DOI 10.1145/128765.128770) | **Repeating-history redo** is idempotent via the **LSN rule** (redo iff `page.LSN < record.LSN`) → safe replay-after-crash. |
| `07-nygard-stability-patterns` | Nygard — *Release It!* (2007/2018) | Stability patterns: circuit breaker, bulkhead, fail fast, graceful degradation. |
| `08-google-sre-graceful-degradation` | Google SRE Book (2016/2020) | **Graceful degradation / load shedding**; fail-static and the fail-open vs fail-closed choice. |
| `09-twelve-factor-app` | Wiggins / Heroku — 12factor.net (2012) | Explicit dependencies, config in the environment — portability + reproducible bootstrap. |
| `10-github-scripts-to-rule-them-all` | GitHub Engineering blog (2015) | A **normalized, idempotent one-command** setup interface (`script/bootstrap`, `script/setup`, …). |

## Design spec
- `idempotency-and-degraded-mode-spec.md` — maps every source above to the bootstrap design:
  idempotent forward replay, a crash-atomic completed-steps ledger, `check()`-based skip,
  and degraded-mode behaviour.

## Faithfulness status (CRO Gate-0)
All ten sources carry complete citations. Reproduced formulae (Burgess `Ô²=Ô`/`Ôq₀=q₀`, ARIES
LSN redo rule, Pillai atomic-rename protocol, K8s reconciler signature) checked verbatim against
the cited primary sources. No overclaims found.
