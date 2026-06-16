# Experiment: Async Concurrency Runtime for the Saga / `--resume` Control Loops

> **Status: COMPLETE — winner = AnyIO.** Escalated by ADR-001 §7 as the one genuine
> fork in the implementation stack. Branch-per-experiment study (CLAUDE.md §3.4/§4.4):
> `experiment/concurrency-runtime`. Decision is the orchestrator's to merge; this doc
> records the pre-registered golden set, the 3-way numbers, and why AnyIO won.

---

## 1. Question (ADR-001 §7)

Plain **asyncio** (stdlib) vs **AnyIO** (structured concurrency over asyncio) vs
**Trio** as the runtime for the **saga executor** behind `claude -p --resume`
(`substrate.md` §4). The saga contract (`data-contracts.md` §4; A3 synthesis,
Garcia-Molina & Salem 1987 src 08, SagaLLM/Chang & Geng 2025 src 10): an ordered
list of locally-atomic steps, **every forward action has a registered
compensator**, a coordinated **checkpoint** with an **idempotent replay log**, and
**replay never double-applies**. ADR-001 §7 frames this as *correctness, not
style*: "structured concurrency's cancellation-scope guarantees may materially
harden the compensator/idempotent-replay invariants against orphaned tasks on
cancellation."

## 2. Design — one executor, three adapters (justified)

The saga **semantics** (ordered steps, mandatory compensators, exactly-once
rollback, idempotent replay, append-only log) are pure and runtime-independent.
What differs between runtimes is **how cancellation and child tasks are
expressed**. So the executor is written **once** (`saga_executor.py`) against a
thin **`RuntimeAdapter`** seam, and only the adapter swaps. This is the most
faithful apples-to-apples comparison: identical engine, three ~37-line adapters.

One place the adapter *cannot* paper over a difference, recorded honestly:
**cancellation injection**. Trio forbids manually raising/catching `trio.Cancelled`
— cancellation **must** originate from a cancel scope — so the harness injects a
**real** scope cancel (`ctx.request_cancel()` → fired cancel scope) rather than
raising the exception by hand. That is the only faithful path across all three.

## 3. Pre-registered golden set + metric (set BEFORE measuring)

Saga length 6; measured identically per runtime (`saga_bakeoff_metrics.py`):

| Metric | Definition | Target |
|---|---|---|
| Cancellation-safety violations | cancel injected at every step boundary AND mid-step; count runs not landing `COMPENSATED` or whose compensators did not run **exactly once** in reverse | 0 |
| Idempotency double-applies | crash + resume from every prefix; count any forward action applied > once | 0 |
| Orphaned tasks | after a cancelled run, count event-loop tasks still alive beyond the entry task | 0 |
| Determinism violations | distinct outcomes over 30 identical runs, minus 1 | 0 |
| Clarity/complexity proxy | adapter SLOC + cyclomatic complexity (radon); strength of the structural (scope-level) cancel guarantee | lower / stronger |

## 4. Results — 3-way numbers

**Correctness (all perfect — the saga semantics are shared, so all three tie):**

| Metric | asyncio | AnyIO | Trio |
|---|---|---|---|
| Cancellation-safety violations | **0** | **0** | **0** |
| Idempotency double-applies | **0** | **0** | **0** |
| Orphaned tasks | **0** | **0** | **0** |
| Determinism violations | **0** | **0** | **0** |

**Clarity / structure proxy (the tie-breaker — radon 6.0.1, Python 3.13):**

| Proxy | asyncio | AnyIO | Trio |
|---|---|---|---|
| Adapter SLOC | 38 | 37 | 36 |
| Avg cyclomatic complexity | 1.45 | **1.27** | **1.27** |
| `checkpoint` cyclomatic complexity | **3** | 1 | 1 |
| Structural cancel guarantee | weakest | strong | strongest |

The decisive line is **`checkpoint` complexity**: asyncio = 3 because the stdlib
has **no scope-level cancel object**, so the adapter hand-rolls a cancel *flag*
that `checkpoint` must poll and raise on; AnyIO and Trio = 1 because a **fired
cancel scope** raises automatically. Trio's guarantee is the strongest
(language-enforced: a nursery cannot exit with a live child, `trio.Cancelled`
cannot be forged), AnyIO's is strong (real `CancelScope` + nursery join), asyncio's
is weakest (`TaskGroup` joins children but cancel is opt-in per await).

## 5. Why AnyIO won

All three are **correct** to zero violations, so the choice turns on the
clarity/structure proxy **and** ecosystem fit:

- **AnyIO buys Trio-grade structured cancellation (CC 1.27, checkpoint CC 1) while
  running on the asyncio backend ADR-001 §1 already mandates** (`psycopg3`,
  `httpx`). This is the "and, not either/or" hybrid default (CLAUDE.md §3.5):
  structured-concurrency guarantees **without** abandoning the asyncio ecosystem.
- **Trio is marginally simpler (SLOC 36 vs 37) and structurally strongest**, but it
  is a **separate event-loop ecosystem** — the platform's asyncio-native I/O
  libraries (`psycopg3` RLS sessions, `httpx`) would need a Trio bridge, a real
  integration cost for a 1-SLOC clarity gain. Rejected on ecosystem fit, not
  correctness.
- **asyncio is the stdlib baseline (zero deps) but the most complex adapter** and
  the weakest cancel guarantee (hand-rolled flag). Rejected: it makes the
  correctness-critical cancellation path the *hardest to read*, the opposite of
  what ADR-001 §7 wants for a regulator-defensible core.

**Verdict: AnyIO** — the structured-concurrency guarantee that hardens the
compensator/replay invariants, delivered on the asyncio backend the rest of the
platform targets. Losers (`asyncio_adapter.py`, `trio_adapter.py`) are **deleted
in the same change** (no-graveyard, CLAUDE.md §3.8); their numbers are preserved
here and in git history (`experiment/concurrency-runtime` M2-M4).

## 6. Tests with teeth + mutation

- **67 → (post-prune) saga tests**: boundary-exact unit asserts at every step
  boundary (clean / abort / boundary-cancel / mid-step-cancel), resume-from-every-
  prefix idempotency, 50x determinism, and a **Hypothesis property + chaos** test
  (max_examples 200) over random step count × random fault kind × fault offset
  asserting exactly-once compensation, full reverse rollback, and no double-apply.
  The property test **caught a real bug**: a cancel requested *during the last
  step* (no following iteration to deliver it) falsely COMMITTED — fixed by a final
  post-loop cancellation checkpoint.
- **Mutation gate** (the acceptance signal, CLAUDE.md §3.6; ADR-001 §3 step 6) is
  run on the winner's saga-core (`saga_executor.py` + `saga_model.py`) via the
  repo's `scripts/run_mutation_gate.py`. See §7 for the score / platform note.

## 7. Mutation score (winner saga-core) — 0 survivors

Run via `mutmut` (2.5.1) on the AnyIO winner's saga-core, native Windows,
`PYTHONUTF8=1`, Python 3.13.3. The saga modules use **only bounded `for` loops**
(no `while`), so the Windows infinite-loop-mutant stall (the audit-module
limitation in the E5 results) **does not apply here** — mutmut completes locally.

| Winner module | Mutants | Killed | Survivors | Score |
|---|---|---|---|---|
| `saga_executor.py` | 25 | 25 | **0** | 100% |
| `saga_model.py` | 49 | 49 | **0** | 100% |
| `runtimes/anyio_adapter.py` | 9 | 9 | **0** | 100% |
| **Total saga-core** | **83** | **83** | **0** | **100%** |

**Survivors hunted then killed (genuine test gaps, not equivalents):**
- `StepContext.already_applied=True/False` (executor) — the flag handed to user
  code; pinned by a forward-sees-False / compensator-sees-True test.
- `SagaState` member string values, the fail-closed `ValueError` messages, and the
  adapter `name` / type-guard message — killed with **exact-string** asserts
  (`str(exc) == ...`), since `pytest.raises(match=)` is a regex *search* a whole-
  string-wrap mutant (`"msg"`→`"XXmsgXX"`) survives.
- `frozen=True`/`slots=True` on every model dataclass — killed by a
  `FrozenInstanceError`-on-write test + a `not hasattr(obj, "__dict__")` test
  (immutability = the append-only/no-rewrite invariant, A6).
- `CancelScope(shield=True)`→`shield=False` (adapter) — killed by a **chaos test**:
  a boundary-cancel saga whose compensators hit a real `anyio` checkpoint mid-
  rollback; without the shield the fired cancel interrupts compensation and the
  saga *falsely COMMITs* — the exact fail-closed violation the shield prevents.
- The `@dataclass`-decorator-removal and `seen=None` mutants initially read as
  "survived" because a broken `__init__` raised at **collection** time (pytest
  exit-2, which mutmut mis-scores); moving the constructions into test **bodies**
  turns them into clean exit-1 failures that mutmut scores as kills.

**Justified equivalent mutants (`# pragma: no mutate`, CLAUDE.md §3.6):** the
`_T = TypeVar("_T")` line (adapter) and the `ForwardAction`/`Compensator` type
aliases (model). Under `from __future__ import annotations` every annotation is a
string and is never evaluated at runtime, so mutating an alias value (→`None`) or a
forward-ref's text is provably runtime-equivalent — no behaviour a test can observe.

> **Scope note (acceptance bar).** This branch is based on old `main` (`f0c2565`),
> which still carries the inherited audit-module survivors being fixed separately;
> a full-repo mutation pass would fail on those regardless of the saga work. The M5
> acceptance bar is the **saga modules at 0 local survivors** + all local gates
> green (below). After the audit fix lands on `main`, this branch is rebased and
> full CI runs before merge.

**Local gates (2026-06-16, `PYTHONUTF8=1`, Python 3.13.3):** ruff ✓ · mypy
`--strict` ✓ (19 files) · bandit ✓ (0 findings, `-r src -c pyproject.toml`) ·
pytest 157 passed · coverage **100% line / 100% branch** (gate ≥90/85).

## 8. Reproduce

```
pip install -e ".[test]"            # installs anyio + (bake-off) trio
PYTHONPATH=src python -m pytest tests/orchestration/saga -q
python -m radon raw -s src/autofirm/orchestration/saga/runtimes/*.py
python -m radon cc  --total-average src/autofirm/orchestration/saga/runtimes/*.py
```

Citations: Garcia-Molina & Salem 1987 (sagas, A3 src 08); Elnozahy et al. 2002
(coordinated checkpointing, src 09); Chang & Geng 2025 SagaLLM (SA/SO/SD +
compensation graph, src 10). All as transcribed in
`docs/research/A3-long-horizon-autonomy/SYNTHESIS.md`.
