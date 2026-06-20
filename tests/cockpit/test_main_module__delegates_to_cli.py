"""__main__: the module entrypoint delegates to the transport CLI's main()."""

from __future__ import annotations

import importlib
import runpy
import sys

import pytest

from autofirm.cockpit.core.cockpit_version import cockpit_version


def test_main_module_imports_the_cli_main() -> None:
    module = importlib.import_module("autofirm.cockpit.__main__")
    from autofirm.cockpit.transport.cockpit_cli import main as cli_main

    # the entrypoint binds the transport CLI's main as its delegate (raise SystemExit(main())).
    assert module.main is cli_main


# runpy re-executing an already-imported package __main__ warns benignly; the guard behaviour
# under test is unaffected, so silence the expected RuntimeWarning to keep the gate output clean.
@pytest.mark.filterwarnings("ignore::RuntimeWarning")
def test_entry_guard_runs_main_only_when_executed_as_main(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # Execute the module AS __main__ so the `if __name__ == "__main__"` guard fires and runs
    # main() (version needs no auth). Under the real guard this raises SystemExit(0) and prints
    # the version; a mutant that rewrites the literal (e.g. "XX__main__XX") would NOT fire the
    # guard, so no SystemExit would be raised -> this test fails -> the guard mutant is killed.
    monkeypatch.setattr(sys, "argv", ["autofirm-cockpit", "version"])
    with pytest.raises(SystemExit) as exc:
        runpy.run_module("autofirm.cockpit", run_name="__main__")
    assert exc.value.code == 0
    assert cockpit_version() in capsys.readouterr().out
