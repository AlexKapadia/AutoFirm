"""__main__: the module entrypoint delegates to the transport CLI's main()."""

from __future__ import annotations

import importlib


def test_main_module_imports_the_cli_main() -> None:
    module = importlib.import_module("autofirm.cockpit.__main__")
    from autofirm.cockpit.transport.cockpit_cli import main as cli_main

    # the entrypoint binds the transport CLI's main as its delegate (raise SystemExit(main())).
    assert module.main is cli_main
