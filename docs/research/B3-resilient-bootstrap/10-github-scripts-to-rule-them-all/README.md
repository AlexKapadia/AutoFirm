# Research Note — "Scripts to Rule Them All" (the normalized, idempotent one-command setup interface)

**Research org:** AutoFirm CRO / Head of Research
**Workstream:** B3 — Resilient Bootstrap (W3: one-command, OS-portable Windows + Linux self-healing setup)
**Source class:** Professional / industry-standard engineering practice (GitHub Engineering)
**Sourcing bar:** CLAUDE.md §3.3, §4.6, §5.6.

---

## 1. Full citation

> GitHub Engineering. *"Scripts to Rule Them All."* The GitHub Blog, 30 June 2015.
> URL: https://github.blog/2015-06-30-scripts-to-rule-them-all/ (originally published on githubengineering.com).
> Reference implementation / canonical repo: **github/scripts-to-rule-them-all**, https://github.com/github/scripts-to-rule-them-all (MIT-licensed template; README defines each script's contract).
>
> Accessed 2026-06-17. Quoted phrases below are reproduced verbatim from the blog post and the repository README; attribution is to GitHub, Inc., 2015.

The pattern is itself an application of Twelve-Factor's *"deterministic build command"* idea (Factor II) — see sibling note `09-twelve-factor-app`.

---

## 2. Faithful structured summary — the normalized script interface

GitHub standardizes a `script/` directory whose filenames are normalized **by name across every project, regardless of language or stack.** The seven scripts and their stated purposes:

| Script | Stated purpose (verbatim from the repo README / blog) |
| --- | --- |
| `script/bootstrap` | *"installs/updates all dependencies"* — fulfills project dependencies (RubyGems, npm packages, Homebrew packages, Ruby/runtime versions, Git submodules). *"The goal is to make sure all required dependencies are installed."* |
| `script/setup` | *"sets up a project to be used for the first time."* Repo README: *"is used to set up a project in an initial state. This is typically run after an initial clone, or, to reset the project back to its initial state."* Also validates that bootstrapping works correctly. |
| `script/update` | *"updates a project to run at its current version."* Repo README: *"is used to update the project after a fresh pull."* Runs `bootstrap` internally and handles migrations / other tasks needed to ready the app for the **currently checked-out** version. |
| `script/server` | *"starts app."* Should call `script/update` beforehand to ensure readiness; may start additional required processes. |
| `script/test` | *"runs tests."* Repo README: *"is used to run the test suite of the application."* Can accept optional file paths for individual tests; runs linting first for faster failure; handles both development and CI environments. |
| `script/cibuild` | *"invoked by continuous integration servers to run tests."* Sets CI-specific configuration, then calls `script/test`. |
| `script/console` | *"opens a console."* Optionally accepts an environment-name argument. |

### Scripts compose / call each other
- *"Each of these scripts is responsible for a unit of work. This makes them composable, easy to call from other scripts, and easy to understand."*
- `script/setup` runs and **validates** `script/bootstrap`.
- `script/update` runs `script/bootstrap` internally.
- `script/server` calls `script/update` first; `script/cibuild` calls `script/test`.

### The normalized-interface goal (the core idea)
- *"If your scripts are normalized by name across all of your projects, your contributors only need to know the pattern, not a deep knowledge of the application."*
- *"Normalizing on script names not only minimizes duplicated effort, it means contributors can do the things they need to do without having an extensive fundamental knowledge of how the project works."*
- *"an individual contributor can do things like bootstrap or run tests without knowing how to do them for a wide range of project types."*
- **Language-agnostic:** `script/bootstrap` might run `bundle install`, `npm install`, `carthage bootstrap`, or `git submodule update` — the **interface** is fixed even though the implementation varies per stack.

### The idempotency / fresh-checkout-and-re-run expectation
The pattern's defining operational property is that the same normalized commands are **safe on a fresh checkout AND safe to run repeatedly**:
- `script/setup` is run *"after an initial clone"* **and** *"to reset the project back to its initial state"* — i.e. it must produce a correct initial state from nothing **and** from an already-set-up tree.
- `script/bootstrap`'s job is *"to make sure all required dependencies are installed"* — a convergent ("ensure", not "add") contract: running it when deps already exist is a no-op-to-convergence, not a failure or duplication.
- `script/update` exists precisely so that **re-running after a pull** re-converges the working tree to the current version (bootstrap + migrations), rather than requiring a clean clone each time.

Together these encode the idempotency norm: **run on a brand-new clone → working project; run again on an existing checkout → still a working project, no harm.**

---

## 3. Best-parts-to-take — mapped to W3 (one-command, OS-portable, self-healing setup)

| W3 design lever | Scripts-to-Rule-Them-All basis | How AutoFirm should apply it |
| --- | --- | --- |
| **Normalized one-command entry point** | Fixed script names (`bootstrap`/`setup`/`test`) independent of language/stack | Expose a stable, memorizable interface (e.g. `make install` / `make test`, or `script/setup` / `script/test`) that any newcomer, CI runner, or operator invokes **without knowing the internals.** The W3 deliverable is exactly this: one command that works on any fresh clone, any machine. |
| **Idempotent bootstrap — safe on fresh-clone AND re-run** | `setup` = "initial state OR reset to initial state"; `bootstrap` = "make sure all deps are installed"; `update` = re-converge after pull | The bootstrap that wraps `make install` / `make test` must be **convergent**: detect-or-create the isolated venv, ensure pinned deps are present, and exit cleanly whether the env is empty, partial, or already complete. This is the mechanical core of **self-healing** — re-running heals a broken/partial environment. |
| **Composition / staged separation** | Scripts call each other (`setup`→`bootstrap`, `update`→`bootstrap`, `cibuild`→`test`) | Mirror Twelve-Factor V: keep `bootstrap` (resolve+isolate deps) distinct from `test`/`run`, with the top-level one-command wrapper composing them. CI uses the same `test` path as devs (a `cibuild`-style thin wrapper), guaranteeing dev/CI parity. |
| **OS portability (Windows + Linux)** | A normalized **interface** with per-stack implementation underneath | The single entry command should resolve to the right implementation per OS (e.g. a `make` target or a `script/` shim that works under both PowerShell/Git-Bash on Windows and `sh` on Linux), so the **same command** bootstraps both — closing Twelve-Factor X's tools gap. |
| **Low-friction onboarding / unattended runs** | "contributors only need to know the pattern, not the application" | Because the command is idempotent and normalized, an auto-resume watchdog (CLAUDE.md §4.8) or a CI runner can blindly re-invoke it after a quota/crash interruption and safely re-converge — no special knowledge, no manual cleanup. |

**Headline takeaway for W3:** "Scripts to Rule Them All" supplies the *interface and idempotency norm* — one normalized command (`make install` / `make test` behind an idempotent `bootstrap`/`setup`) that is **safe on a fresh clone and safe to re-run**, language- and OS-agnostic by design. It is the operational delivery vehicle for the Twelve-Factor *contract* in the sibling note.

---

## Design implications for W3 (combined with note 09)

1. **Bootstrap = idempotent, env-driven, isolated.** A single OS-portable command (`make install` wrapped by an idempotent `bootstrap`) (a) ensures an isolated venv exists and is populated from a pinned manifest — never system-wide packages (Factor II); (b) reads all provider/gateway keys from the **environment** so the repo stays credential-free and open-sourceable (Factor III/IV); and (c) converges identically whether run on a fresh clone or re-run on a partial/broken tree (Scripts-to-Rule-Them-All idempotency). Re-running *is* the self-heal.
2. **Absent key → degraded mode, not failure.** Because keys come from the environment (Factor III) and providers are swappable attached resources (Factor IV), a **missing** key is a detectable, first-class config state: the system fails closed into a documented degraded mode and `make test` still passes on a fresh clone with no secrets — the same normalized command working on any machine, Windows or Linux, satisfying dev/prod + cross-OS parity (Factor X).
