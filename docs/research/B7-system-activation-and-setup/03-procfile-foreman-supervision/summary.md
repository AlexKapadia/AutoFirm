# Process Declaration & Supervision — Foreman / Procfile / honcho / supervisord

## Citation (exact)
- David Dollar, Foreman — "manage Procfile-based applications", 2011.
  Repo: https://github.com/ddollar/foreman  ·  Man page: https://ddollar.github.io/foreman/
  Intro: "Introducing Foreman", blog.daviddollar.org, 6 May 2011.
- honcho — Python port of Foreman. https://honcho.readthedocs.io/
- Supervisor (supervisord) — process control system. http://supervisord.org/
- The Twelve-Factor App, IX. Disposability & VIII. Concurrency (process model).
  https://12factor.net/disposability  ·  https://12factor.net/concurrency

## Faithful summary
Foreman / Procfile declare an application long-running processes once and run them all with one command:

> "Foreman is a manager for Procfile-based applications... abstract away the details of the Procfile format,
> and allow you to either run your application directly or export it to some other process management format."

- Procfile grammar (exact): each line is "name: command", e.g. "web: bundle exec thin start" /
  "job: bundle exec rake jobs:work". The Procfile is a single declarative inventory of process types.
- One command starts them all: "if no additional parameters are passed, foreman will run one instance of
  each type of process defined in your Procfile." Scale per type with -m process=num.
- honcho is the Python implementation of the same model.

supervisord is a long-running process control system: it starts configured programs as subprocesses and,
crucially, keeps them running — automatically restarting a process that exits unexpectedly (configurable
autostart / autorestart), aggregating their stdout/stderr, and exposing start/stop/status control. It is
the "keep it up" half that a one-shot launcher lacks.

Twelve-Factor IX (Disposability): processes should "start up and shut down gracefully... maximize robustness
with fast startup and graceful shutdown", be robust against sudden death, and be crash-only safe.
VIII (Concurrency): the app is a set of processes; scale by the process model.

Together: declare the long-lived components once; one command activates them; a supervisor keeps them alive
and lets them be cleanly disposed of. "Activate" therefore means processes actually running and staying up,
not merely "constructed".

## Best parts to take -> AutoFirm
- AutoFirm is a single Python process, not a fleet of OS processes — so do NOT pull foreman/supervisord in
  as runtime deps (that re-fragments the system and breaks runtime-minimalism of pyproject.toml). Take the
  principle: an in-process supervisor (a small PlatformSupervisor class under src/autofirm/runtime/) that
  starts the long-lived loops and keeps them up.
- Declare the long-lived components once (the in-code analogue of a Procfile): the heartbeat scheduler
  (heartbeat_scheduler.py), the comms bus delivery loop (inter_agent_message_bus.py), the market-intel daily
  sensing beat (daily_sensing_heartbeat.py), the saga/operate control loop (orchestration/saga,
  e2e/company_operate_flow.py), and the auto-resume watchdog (CLAUDE.md §4.8). The supervisor is handed these
  by the composition root and runs them under one asyncio/AnyIO event loop (AnyIO chosen per ADR-001 §7).
- Keep-it-up = restart with a circuit breaker. Reuse B3-07 (Nygard) circuit-breaker semantics already in the
  degraded-mode spec: a loop that crashes is restarted with backoff; a loop that keeps crashing trips open
  and is reported by status, never silently dead. This is supervisord autorestart done in-process.
- Graceful disposability (12-Factor IX). autofirm down sends a cooperative cancel to every supervised loop
  and waits for them to drain (audit-flush, ledger-fsync) — crash-only safe because B3 atomic ledger means
  an ungraceful kill still resumes cleanly.
- Export path (optional, future). Foreman export idea maps to generating a systemd unit / Procfile from the
  same declared inventory — keep the inventory the single source of truth.

## Cross-link (no duplication)
B3 ensures the environment is converged and degradation is safe. B7-03 adds the running-and-staying-up
dimension: B3 says "the venv exists and the key is probed"; B7-03 says "the comms bus and heartbeats are
actually looping and will be restarted if they die." The circuit-breaker primitive is shared (cited from
B3-07), applied here to process liveness rather than capability availability.
