# BEST-PARTS — OSS-Fuzz empirical study (MSR 2021)

## ADOPT
1. **Continuous, coverage-guided fuzzing at every external-input boundary** of client products (CLAUDE.md §3.6 "fuzz every external-input boundary"). The OSS-Fuzz evidence (23,907 bugs / 316 projects) shows fuzzing finds bugs at scale that other techniques miss, especially crash/availability and memory-safety classes. AutoFirm should run libFuzzer/AFL++-class fuzzers (or Atheris for Python, Jazzer for JVM) on parsers and untrusted-input handlers.
2. **Design CI for flaky-bug reality.** Because a notable share of fuzz bugs are flaky, AutoFirm's fuzz gate must **re-run and corroborate** a crash before failing the build, and quarantine flaky findings rather than blocking blindly — otherwise the gate becomes noise.
3. **Treat availability bugs (52%) as first-class.** Crashes/timeouts/OOM are the majority class; AutoFirm's fuzz harnesses must assert on hangs/OOM, not only on memory-corruption sanitizer trips.

## REJECT
- Reject fuzzing only "security" code — the data shows the majority of fuzz-found defects are robustness/availability bugs across ordinary parsing/serialization code.

## Open item (not relied upon)
- Exact memory-safety percentage and median time-to-fix were not cleanly verifiable this pass; do not cite a specific number until re-verified from the paper's tables.

## Concrete artifact this drives
- A `fuzz-gate` CI stage: per-language coverage-guided fuzzer + sanitizers, time-boxed, with crash-corroboration and flaky-quarantine; seeds derived from real public sample inputs (never client PII, per CLAUDE.md §3.12).
