"""Fail-closed mutation gate (the ACCEPTANCE SIGNAL -- ADR-001 §3 step 6; CLAUDE.md §3.6).

What this does
--------------
Runs ``mutmut`` over the configured paths and then **decides pass/fail by reading
the mutmut result cache directly**, so the gate is genuinely enforced rather than
asserted. The build FAILS (exit 1) if ANY mutant is not killed -- i.e. any
``survived``, ``timeout``, ``suspicious``, or ``untested`` mutant on the mutated
modules. Only ``ok_killed`` (and explicitly-skipped) mutants pass.

Why it exists / where it sits
-----------------------------
1. **``mutmut results`` is broken under Python 3.13 + pony-orm** (it raises
   ``TypeError: 'QueryResultIterator' object is not iterable`` in its printer), so
   the Makefile/CI cannot rely on it to read the score. This script reads the
   ``.mutmut-cache`` SQLite DB itself, which is stable.
2. **The mutation gate must fail closed.** Previously the Makefile ran
   ``-mutmut run`` (a leading ``-`` ignores the exit code) followed by the broken
   ``mutmut results`` -- so a surviving mutant could never fail the build. This
   script closes that gap: survivors -> non-zero exit -> red gate (CLAUDE.md §5.6).
3. **Windows mutmut stalls on infinite-loop mutants** (a mutated loop bound such
   as ``k *= 2`` -> ``k = 2`` busy-loops, and mutmut 2.x's timeout does not abort a
   busy Python loop on native Windows). The full pass over the loop-bearing audit
   modules is therefore the Linux-CI enforcement plane (where ``signal``-based
   per-test timeouts work); locally a developer can scope this to the
   non-loop-bearing core. See ``docs/architecture/experiments/
   E5-tamper-evident-log-results.md`` ("Known tooling limitation").

Usage
-----
    python scripts/run_mutation_gate.py [--paths PATH [PATH ...]] [--no-run]

``--paths``   Override the modules to mutate (default: mutmut's ``paths_to_mutate``
              from ``pyproject.toml``). On a Windows dev box, pass the non-loop
              core only (e.g. the hashing primitives) to avoid the known stall.
``--no-run``  Skip the ``mutmut run`` and only grade the existing cache (useful in
              CI after a separate ``mutmut run`` step, or for fast re-grading).

Exit codes
----------
0  every mutant was killed (gate GREEN).
1  one or more mutants survived / timed out / are suspicious / untested (gate RED),
   OR mutmut could not run, OR the cache is missing (fail-closed: a gate that
   cannot run is a FAILED gate, never a skipped one -- CLAUDE.md §5.6).
"""

from __future__ import annotations

import argparse
import contextlib
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

# mutmut 2.x persists per-mutant status in this SQLite file at the repo root.
_CACHE_FILE = ".mutmut-cache"


def _force_utf8_console() -> None:
    """Make this script's own stdout/stderr UTF-8 so it cannot crash on emoji.

    On a native Windows console the default code page is cp1252, which cannot
    encode the emoji mutmut prints in its banner/progress output. Re-emitting
    that text (or our own future output) through a cp1252 stream raises
    ``UnicodeEncodeError`` and aborts the gate before it can grade anything.
    Forcing UTF-8 here is non-semantic: it only changes how bytes are written,
    never the PASS/FAIL decision (which is made from the cache, not stdout).
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:  # text streams on 3.7+ expose reconfigure()
            # Non-fatal: a stream that refuses reconfiguration (e.g. already
            # detached/redirected) must not break the gate, so suppress the
            # exotic ValueError/OSError rather than aborting.
            with contextlib.suppress(ValueError, OSError):  # pragma: no cover
                reconfigure(encoding="utf-8", errors="replace")

# The only statuses that count as a killed (good) mutant. Everything else --
# survived, timed out, suspicious, or never tested -- fails the gate (fail-closed:
# we refuse to pass on anything we did not prove the suite kills).
_KILLED_STATUSES = frozenset({"ok_killed"})
# Explicitly skipped mutants are neither killed nor survivors; mutmut excludes
# them from the score. We treat them as non-failing but report them.
_SKIPPED_STATUSES = frozenset({"skipped"})


def _run_mutmut(paths: list[str] | None) -> None:
    """Run ``mutmut run`` (fail-closed if mutmut itself cannot execute).

    mutmut returns a non-zero exit code when mutants survive; that is expected and
    is NOT treated as a hard error here -- the authoritative pass/fail decision is
    made by :func:`_grade_cache` reading the result cache. A *crash* (mutmut not
    importable / not installed) is fatal.
    """
    cmd = [sys.executable, "-m", "mutmut", "run"]
    if paths:
        for p in paths:
            cmd += ["--paths-to-mutate", p]
    try:
        # We deliberately do not check the return code: mutmut exits non-zero when
        # mutants survive, but the cache (graded below) is the source of truth.
        #
        # mutmut prints an emoji banner with its OWN print() inside the child
        # process. On a cp1252 Windows console that child's stdout is cp1252 too,
        # so the emoji raises UnicodeEncodeError *inside mutmut* before it sends
        # anything down a pipe. Forcing the child's I/O encoding to UTF-8 (via the
        # standard PYTHONIOENCODING / PYTHONUTF8 env vars) is what actually stops
        # the crash. We then capture and re-emit mutmut's output through our own
        # UTF-8-hardened stdout for visibility. This is purely an I/O concern --
        # it never touches the pass/fail decision (graded from the cache below).
        child_env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
        result = subprocess.run(  # fixed argv, no shell -> no injection
            cmd,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="utf-8",
            errors="replace",
            env=child_env,
        )
        if result.stdout:
            print(result.stdout, end="")
    except FileNotFoundError as exc:  # pragma: no cover - environment failure
        # fail-closed: a mutation gate that cannot run is a FAILED gate.
        print(f"MUTATION GATE: FAILED -- mutmut could not be executed: {exc}")
        raise SystemExit(1) from exc


def _grade_cache() -> int:
    """Read ``.mutmut-cache`` and return process exit code (0 = all killed).

    Reads the SQLite cache directly because ``mutmut results`` crashes on
    Python 3.13 + pony-orm. Fail-closed: a missing/empty cache fails the gate.
    """
    cache = Path(_CACHE_FILE)
    if not cache.exists():
        # fail-closed: no cache => mutmut never recorded results => gate FAILED.
        print(f"MUTATION GATE: FAILED -- no {_CACHE_FILE} found (mutmut did not run).")
        return 1

    conn = sqlite3.connect(str(cache))
    try:
        rows = conn.execute(
            "SELECT status, COUNT(*) FROM mutant GROUP BY status"
        ).fetchall()
        # Enumerate the individual survivor mutants (everything not killed and not
        # explicitly skipped) so a CI run REPORTS WHICH mutants survived, not just
        # how many. We join Mutant -> Line -> SourceFile (Pony ORM maps the FK
        # attributes to integer columns of the same name) to recover a stable,
        # human-actionable identifier: the source file, the line number + text the
        # mutant was applied to, the per-line mutant index (mutmut's own handle for
        # `mutmut show <file> <index>`), and the recorded status. This is purely
        # diagnostic output -- it never touches the PASS/FAIL decision below, which
        # is still computed from the status counts (fail-closed, CLAUDE.md §5.6).
        killed_csv = ",".join(f"'{s}'" for s in sorted(_KILLED_STATUSES))
        skipped_csv = ",".join(f"'{s}'" for s in sorted(_SKIPPED_STATUSES))
        survivor_rows = conn.execute(
            "SELECT sf.filename, l.line_number, m.\"index\", m.status, l.line "
            "FROM mutant m "
            "JOIN line l ON m.line = l.id "
            "JOIN sourcefile sf ON l.sourcefile = sf.id "
            f"WHERE m.status NOT IN ({killed_csv}) "
            f"AND m.status NOT IN ({skipped_csv}) "
            "ORDER BY sf.filename, l.line_number, m.\"index\""
        ).fetchall()
    finally:
        conn.close()

    counts = dict(rows)
    total = sum(counts.values())
    if total == 0:
        # fail-closed: zero mutants means nothing was actually tested.
        print("MUTATION GATE: FAILED -- the cache records zero mutants.")
        return 1

    killed = sum(n for s, n in counts.items() if s in _KILLED_STATUSES)
    skipped = sum(n for s, n in counts.items() if s in _SKIPPED_STATUSES)
    # Everything that is neither killed nor explicitly skipped is a survivor class.
    survivors = total - killed - skipped

    score = killed / (total - skipped) if (total - skipped) else 0.0
    print("=== MUTATION GATE (acceptance signal -- CLAUDE.md §3.6) ===")
    print(f"  total mutants : {total}")
    print(f"  killed        : {killed}")
    print(f"  skipped       : {skipped}")
    print(f"  survivors     : {survivors}  (survived/timeout/suspicious/untested)")
    print(f"  mutation score: {score:.4f}  (killed / non-skipped)")
    for status, n in sorted(counts.items()):
        print(f"    - {status}: {n}")

    if survivors > 0:
        # fail-closed: any survivor means a test is too weak (CLAUDE.md §3.6) ->
        # add a HARDER adversarial test that kills it, then re-run. RED gate.
        # Enumerate each survivor so the gate REPORTS WHICH mutants escaped (so the
        # fix is actionable: each line below is a test gap to close). The count is
        # authoritative; this list is its breakdown.
        print(f"SURVIVING MUTANTS ({survivors}):")
        for filename, line_number, index, status, line_text in survivor_rows:
            source = (line_text or "").strip()
            location = f"{filename}:{line_number} (mutant #{index}, {status})"
            print(f"  - {location}")
            if source:
                print(f"      line: {source}")
        print("MUTATION GATE: FAILED -- surviving mutant(s); the suite has a gap.")
        return 1
    print("MUTATION GATE: PASSED -- every mutant killed (0 survivors).")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the mutation gate and return the process exit code."""
    _force_utf8_console()  # never let a cp1252 console crash the gate on emoji
    parser = argparse.ArgumentParser(description="Fail-closed mutation gate.")
    parser.add_argument(
        "--paths",
        nargs="+",
        default=None,
        help="Modules to mutate (default: pyproject's paths_to_mutate).",
    )
    parser.add_argument(
        "--no-run",
        action="store_true",
        help="Grade the existing cache without re-running mutmut.",
    )
    args = parser.parse_args(argv)

    if not args.no_run:
        _run_mutmut(args.paths)
    return _grade_cache()


if __name__ == "__main__":
    raise SystemExit(main())
