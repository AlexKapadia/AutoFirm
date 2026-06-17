# Research Note — The Twelve-Factor App (factors relevant to a one-command, OS-portable, self-healing bootstrap)

**Research org:** AutoFirm CRO / Head of Research
**Workstream:** B3 — Resilient Bootstrap (W3: one-command, OS-portable Windows + Linux self-healing setup)
**Source class:** Primary / professional methodology (industry canon, authored by a Heroku co-founder)
**Sourcing bar:** CLAUDE.md §3.3 (peer-reviewed/primary/professional sourcing; faithful reproduction; exact citation), §4.6, §5.6.

---

## 1. Full citation

> Wiggins, Adam. *The Twelve-Factor App.* Originally drafted ~2011, published 2012 (Heroku). Online manifesto.
> Canonical site: https://12factor.net/ (Adam Wiggins, author/editor; Heroku, originator).
> Factor pages cited here:
> - I. Codebase — https://12factor.net/codebase
> - II. Dependencies — https://12factor.net/dependencies
> - III. Config — https://12factor.net/config
> - IV. Backing services — https://12factor.net/backing-services
> - V. Build, release, run — https://12factor.net/build-release-run
> - X. Dev/prod parity — https://12factor.net/dev-prod-parity
>
> Accessed 2026-06-17. Quotations below are reproduced verbatim from the canonical pages; attribution is to Wiggins / Heroku, 2012.

Note on fidelity: where a phrase appears in quotation marks it is reproduced verbatim from 12factor.net. Surrounding text is faithful structured summary, not paraphrase dressed as quotation.

---

## 2. Faithful structured summary — the factors most relevant to W3

### Factor I — Codebase
**Headline (verbatim):** *"One codebase tracked in revision control, many deploys."*

- *"There is always a one-to-one correlation between the codebase and the app."* Multiple codebases mean a distributed system, not one app; sharing code across apps is a violation (extract shared code into libraries instead).
- A **deploy** is *"a running instance of the app"* — production, staging, and each developer's local machine are all deploys of the **same** codebase. Different running versions, identical codebase foundation.

### Factor II — Dependencies (the core of W3's isolation requirement)
**Headline (verbatim):** *"Explicitly declare and isolate dependencies."*

- **Key principle (verbatim):** *"A twelve-factor app never relies on implicit existence of system-wide packages."* All dependencies are declared **completely and exactly** via a **dependency declaration manifest**.
- Two **complementary** practices, both required:
  1. **Dependency declaration** — specify all required libraries via a manifest file.
  2. **Dependency isolation** — use a tool during execution to prevent system-wide packages from leaking in / interfering.
- Per-ecosystem tooling cited verbatim:
  - **Python:** *"Pip handles declaration while Virtualenv provides isolation."*
  - **Ruby:** *"Bundler offers the `Gemfile` manifest format for dependency declaration and `bundle exec` for dependency isolation."*
  - **Clojure:** Leiningen's `lein deps`.
- **Onboarding benefit (the W3 payoff):** with explicit declaration, *"new developers need only the language runtime and dependency manager installed, then can run a deterministic build command to set up the complete environment."*
- **System tools:** an app must **not** assume `ImageMagick`, `curl`, etc. exist — *"If the app needs to shell out to a system tool, that tool should be vendored into the app"* for portability.

### Factor III — Config (provider keys live in the ENVIRONMENT)
**Headline (verbatim):** *"Store config in the environment."*

- **Definition:** config is *"everything that is likely to vary between deploys"* — database credentials, **external service keys**, and per-deploy values such as hostnames.
- **Core principle (verbatim):** *"Config varies substantially across deploys, code does not."* The methodology mandates **"strict separation of config from code"**; storing config as constants in code is a violation.
- **The litmus test (verbatim):** *"whether the codebase could be made open source at any moment, without compromising any credentials."*
- **Mechanism:** store config in **environment variables** (env vars). They can be changed between deploys without code changes, reduce accidental credential exposure in version control, and *"work across programming languages and operating systems"* (directly relevant to Windows + Linux parity).
- **Against grouped environments:** do **not** group config into named sets (`development`/`staging`/`production`); this *"does not scale cleanly."* Env vars should be *"granular controls, each fully orthogonal to other env vars."*

### Factor IV — Backing services (the provider key / gateway as an attached resource)
**Headline (verbatim):** *"Treat backing services as attached resources."*

- A backing service is *"any service the app consumes over the network as part of its normal operation"* — databases, message queues, SMTP, caches, plus third-party offerings (S3, API services, etc.).
- **Key distinction (verbatim):** *"The code for a twelve-factor app makes no distinction between local and third party services."* Both are **attached resources**, *"accessed via a URL or other locator/credentials stored in the config."*
- Resources can be *"attached to and detached from deploys at will"* — a failed provider can be swapped for another **by changing config only, no code change.** (Directly underwrites a swappable provider/gateway and degraded-mode fallback.)

### Factor V — Build, release, run (strict stage separation)
**Headline (verbatim):** *"Strictly separate build and run stages."*

- **Build stage:** *"a transform which converts a code repo into an executable bundle known as a build"* — fetches dependencies, compiles binaries/assets at a specific commit.
- **Release stage:** *"takes the build produced by the build stage and combines it with the deploy's current config."* Release = build + config, ready to run.
- **Run stage:** *"runs the app in the execution environment, by launching some set of the app's processes against a selected release."*
- **Strict separation (verbatim):** *"The twelve-factor app uses strict separation between the build, release, and run stages."* Consequently *"it is impossible to make changes to the code at runtime, since there is no way to propagate those changes back to the build stage."*
- **Release immutability:** every release has *"a unique release ID, such as a timestamp ... or an incrementing number"*; *"releases are an append-only ledger and a release cannot be mutated once it is created. Any change must create a new release."*

### Factor X — Dev/prod parity (the OS-portability mandate)
**Headline (verbatim):** *"Keep development, staging, and production as similar as possible."*

- Three historical gaps to close: **Time gap** (code takes weeks/months to ship), **Personnel gap** (devs write, ops deploy), **Tools gap** (different stacks locally vs prod — e.g. Nginx/SQLite/OS X vs Apache/MySQL/Linux).
- Comparison the methodology draws (traditional → twelve-factor):

  | Aspect | Traditional App | Twelve-Factor App |
  | --- | --- | --- |
  | Time between deploys | Weeks | Hours |
  | Code authors vs. deployers | Different people | Same people |
  | Dev vs. production environments | Divergent | As similar as possible |

- **Backing-services rule (verbatim):** *"The twelve-factor developer resists the urge to use different backing services between development and production"* — because *"code that worked and passed tests in development or staging [may] fail in production."*

---

## 3. Best-parts-to-take — mapped to W3 (one-command, OS-portable, self-healing setup)

| W3 design lever | Twelve-Factor basis | How AutoFirm should apply it |
| --- | --- | --- |
| **Provider keys in the ENVIRONMENT, never in code** | III (config in env; open-source litmus test) + IV (credentials stored in config) | Read every provider/gateway key from an env var (or secret manager) at runtime. The repo must pass the litmus test — open-sourceable with zero credentials inside. This is the hook for **degraded mode**: when a key is **absent**, the env-driven config naturally yields "no key present" → fail to a documented degraded path rather than crashing or hard-coding a default. (Ties to CLAUDE.md §5.6 fail-closed.) |
| **Explicit dependency isolation (venv) as an idempotent bootstrap step** | II (declare + isolate; never rely on system-wide packages; "deterministic build command") | Bootstrap creates/uses an **isolated virtualenv** and installs **only** from a pinned manifest — never touching system Python/site-packages. Re-running must converge on the same isolated env (idempotent). New-clone onboarding = "have the runtime + a package manager, run one command." |
| **Build / release / run separation** | V (strict separation; immutable releases) | Keep `install`/build (resolve+install deps into the venv) distinct from `run`. The one-command bootstrap performs build+release-style setup; execution is a separate, simple, repeatable step. No mutating code at runtime. |
| **Dev/prod + Windows/Linux parity** | X (keep environments as similar as possible; env vars "work across ... operating systems") + II (vendor system tools, don't assume them) | The single setup command and the same pinned manifest must produce an **equivalent isolated environment on Windows and Linux**. Do not assume OS-specific system tools exist — vendor or detect them. Env-var config is the portable contract that closes the tools/time/personnel gaps. |
| **Swappable provider/gateway** | IV (attached resources; swap by config only) | Treat each LLM/provider/gateway as an attached resource selected by config URL/key; swapping or failing over to a fallback provider is a **config change, not a code change** — the mechanical basis for resilient/self-healing provider selection. |
| **One codebase, many deploys** | I (one-to-one codebase↔app; every machine is a deploy) | A single repo + the same bootstrap produces a valid deploy on any developer machine, CI runner, or operator box — the precondition for "works on any fresh clone, any machine." |

**Headline takeaway for W3:** Twelve-Factor gives the *contract* — declare-and-isolate dependencies (II), config-from-environment with the open-source litmus test (III), swappable attached resources (IV), strict build/run separation (V), and cross-OS parity (X). It defines *what* a portable, credential-safe, self-healing setup must satisfy; the *normalized one-command interface* that delivers it is the Scripts-to-Rule-Them-All pattern (see sibling note `10-github-scripts-to-rule-them-all`).
