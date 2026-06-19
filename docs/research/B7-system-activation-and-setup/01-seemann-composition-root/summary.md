# Composition Root — Mark Seemann (with Steven van Deursen)

## Citation (exact)
- Steven van Deursen & Mark Seemann, ***Dependency Injection Principles, Practices, and Patterns***,
  Manning Publications, 2019. ISBN 978-1617294730.
  <https://www.manning.com/books/dependency-injection-principles-practices-patterns>
- Mark Seemann, **"Composition Root"**, *ploeh blog*, 28 July 2011.
  <https://blog.ploeh.dk/2011/07/28/CompositionRoot/>
- (Predecessor: M. Seemann, *Dependency Injection in .NET*, Manning 2011.)

## Faithful summary
The **Composition Root** is the central pattern Seemann uses to keep dependency injection from leaking
through a codebase. Reproduced from the primary sources:

> "A Composition Root is a (preferably) unique location in an application where modules are composed
> together." — and composition should take place "as close to the application's entry point as possible."

Key claims of the pattern:
1. **A single Composition Root per application/process.** Regardless of how complex the application is,
   there is exactly one place that knows how to build the full object graph.
2. **It composes the object graph, then hands off.** The Composition Root "composes the object graph,
   which subsequently performs the actual work of the application." After construction the wired graph
   runs; the root does no business logic itself.
3. **Constructor Injection is the default.** Classes declare collaborators as constructor parameters and
   never new-up their own dependencies (no `new` of collaborators inside business classes; no Service
   Locator). Only the Composition Root calls the constructors.
4. **The DI-container decision becomes local.** Once composition is isolated to one root, "the decision
   about DI Container usage becomes unimportant" — container or pure hand-wiring ("Pure DI") is an
   implementation detail confined to the root and invisible to the rest of the app.
5. **Volatile dependencies are resolved here.** External/volatile resources (clocks, network clients, key
   resolvers, audit sinks) are constructed at the root and injected down, so the leaves stay pure/testable.

The anti-pattern it replaces is **fragmentation**: when many classes each construct their own dependencies
(or reach into a global Service Locator), wiring is smeared across the codebase, the true dependency graph
is invisible, and the system is a *bag of parts* rather than a *composed whole*.

## Best parts to take -> AutoFirm
- **Direct cure for the "feels fragmented" problem.** AutoFirm already follows the prerequisite half:
  every package (`inter_agent_message_bus`, `credential_broker`, `append_only_cost_ledger`,
  `live_capability_registry`, `org_lifecycle_engine`, `session_lifecycle_engine`,
  `front_door_request_dispatcher`, `heartbeat_scheduler`, ...) uses keyword-only constructor injection with
  mandatory collaborators and no hidden global state. What is missing is the single Composition Root. Add it.
- **One and only one root**: `src/autofirm/runtime/platform_composition_root.py`. It is the *only* module
  allowed to import-and-construct every other package. Nothing else news-up cross-package collaborators.
- **Pure DI (hand-wiring), no container.** Per the source a container is optional; hand-wire in the root
  (explicit, auditable, mypy-strict, zero new runtime deps) rather than add a DI-container dependency.
- **Compose, then hand off.** The root returns a `Platform` object (the composed graph); a separate
  supervisor/CLI *runs* it (folders 02, 03). Keeps the root free of business logic.

## Cross-link (no duplication)
B3 governs *whether the environment is converged* (idempotent steps). B7-01 governs *how the converged
packages are wired into one graph*. The composition root consumes B3's converged env and produces the live
object graph -- different layer, no overlap.
