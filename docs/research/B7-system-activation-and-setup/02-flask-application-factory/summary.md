# Application Factory Pattern — Flask (create_app)

## Citation (exact)
- Pallets Projects, "Application Factories", Flask Documentation (stable / 3.x).
  https://flask.palletsprojects.com/en/stable/patterns/appfactories/
- Related: Flask docs, Extensions (init_app deferred-initialization pattern).

## Faithful summary
The application-factory pattern moves construction of the application object into a function instead of a
module-level global:

> "If you move the creation of the application object into a function, you can then create multiple
> instances of this app later. The idea is to set up the application in a function."

Faithful points from the official docs:
1. A factory function builds and configures the app. Conventionally named create_app() (Flask auto-detects
   create_app or make_app). It instantiates the app, applies configuration, registers blueprints/routes,
   and returns the wired instance.
2. Configuration is injected, not hard-coded. "You can have instances of the application with different
   settings to test every case" — the factory takes config so the same assembly logic serves dev/test/prod.
3. Deferred extension binding via init_app(). Extensions are created once at import time with no app bound,
   then bound inside the factory: "no application-specific state is stored on the extension object, so one
   extension object can be used for multiple apps... initialize extensions separately and call init_app() on
   them within create_app() rather than binding them directly to the app at import time." This separates
   declaration (import time) from assembly/binding (factory call time).
4. Multiple isolated instances. Because nothing global is mutated at import, multiple fully-wired app
   instances can coexist in one process — essential for parallel tests.

The pattern is the Python-idiomatic realisation of a Composition Root (folder 01): a single callable that
performs all wiring and returns the composed object, with configuration as a parameter and deferred binding
so import never has side effects.

## Best parts to take -> AutoFirm
- Make the composition root a factory: build_platform(config: PlatformConfig) -> Platform. Same assembly
  logic builds the real platform, the degraded platform, and the in-test platform — only the injected
  PlatformConfig differs (mirrors Flask's "same create_app, different settings").
- Deferred binding = graceful degradation. Flask's init_app() separation maps exactly onto B3 degraded mode:
  declare each capability object at import (no side effects), then in the factory bind it only if its
  dependency probed OK. A missing provider key means that one capability binds in degraded state instead of
  failing the whole assembly — the platform object still builds.
- No import-time side effects (12-Factor-friendly, test-friendly). import autofirm must never open a socket,
  read a secret, or construct a network client. All of that happens inside build_platform, so the package
  stays importable in CI and unit tests can build many isolated platforms with synthetic config.
- Config object, not env-reads-everywhere. A single typed PlatformConfig (loaded once from env at the CLI
  edge) is threaded into the factory, keeping env-reading at one boundary.

## Cross-link (no duplication)
Complements 01 (the principle) with the concrete callable shape. Complements B3: the factory is the place
where B3 degraded-mode policy is applied per capability during assembly.
