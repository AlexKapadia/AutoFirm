# One-Command Developer Experience — Scripts to Rule Them All & 12-Factor

## Citation (exact)
- GitHub Engineering, "Scripts to Rule Them All", github.blog, 2015.
  https://github.blog/2015-06-30-scripts-to-rule-them-all/  (pattern repo: github/scripts-to-rule-them-all)
- The Twelve-Factor App (Adam Wiggins / Heroku, 2011-2012), factors:
  I. Codebase, V. Build/Release/Run, X. Dev/prod parity. https://12factor.net/
- (Also cited in B3-09/B3-10; here used for the DX/feel dimension, not re-deriving idempotency.)

## Faithful summary
Scripts to Rule Them All defines a normalized set of script entrypoints that every repo at GitHub exposes,
so a developer can move between projects without relearning setup. The canonical scripts:
- script/bootstrap — install all dependencies; resolve everything needed to run from a fresh clone.
- script/setup — get the app set up for the first time (db create/migrate/seed); often calls bootstrap.
- script/update — update an existing checkout to run latest (re-resolve deps, run migrations).
- script/server — start the app.
- script/test — run the test suite. (Plus script/console, script/cibuild.)

The two load-bearing DX principles:
1. Normalized interface. The same command names mean the same thing in every project — so onboarding is
   "clone, then run one known command", regardless of language or framework. The contract is the interface,
   not the implementation.
2. Works from a fresh clone AND on re-run. script/bootstrap must succeed on a clean machine and be safe to
   re-run on an already-set-up one (idempotent). This is what makes setup feel flawless rather than fragile.

Twelve-Factor reinforces the "feel": I. Codebase (one codebase, many deploys), V. strict separation of
build/release/run, X. Dev/prod parity (keep dev, staging, prod as similar as possible — same OS, same
backing services). A flawless setup is one command, reproducible, and identical across environments.

## Best parts to take -> AutoFirm
- The single normalized command is the product. The mandate is "flawlessly simple (one command)". Map the
  Scripts-to-Rule-Them-All inventory onto AutoFirm subcommands so the contract is obvious:
    bootstrap+setup+server  ->  autofirm up      (converge env via B3, build via composition root, supervise, self-test)
    test                    ->  make test        (already exists; the gated suite)
    a status/console        ->  autofirm status
    a doctor/check          ->  autofirm doctor   (B3 read-only check)
    graceful stop           ->  autofirm down
  One command (up) does the whole "set up AND activate" — exactly the user requirement.
- Fresh-clone AND re-run, both green. The acceptance bar (from B3 + this folder): clean clone -> autofirm up
  -> live + self-test passes, AND a second autofirm up is a no-op that ends in the same live state. The
  "feels flawless vs crappy" difference is precisely this idempotent re-runnability + a single command.
- Dev/prod + OS parity (12-Factor X). up must behave identically on Windows AND Linux (the substrate runs
  PowerShell-launched Claude sessions on Windows; CI is Linux). One command, two OSes, same result — quantify
  it as a hard acceptance criterion (see design doc).
- Keep make test as the deeper gate; up wraps the fast path. up is the everyday "make it live" door; the full
  adversarial/mutation gate stays in make test. up can optionally invoke the smoke subset, not the 10-minute
  mutation run, so "flawless" also means "fast".

## Cross-link (no duplication)
B3-09 (12-Factor) and B3-10 (Scripts-to-Rule-Them-All) already grounded the idempotent-bootstrap mechanics.
B7-05 reuses the SAME sources only for the developer-experience / single-normalized-entrypoint dimension
(what makes setup FEEL flawless and how the command inventory should read), and explicitly defers all
idempotency/crash-resume mechanics to B3. No mechanism is re-derived.
