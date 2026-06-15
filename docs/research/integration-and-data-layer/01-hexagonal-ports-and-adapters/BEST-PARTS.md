# Best parts to take - Hexagonal Architecture

## Adopt

- **Make hexagonal the spine of AutoFirm''s integration layer.** The domain/agent core defines
  **outbound ports** (Python `Protocol`/ABC interfaces) for every external dependency: persistence,
  vector store, AI providers (text/image/voice), secrets, audit log, outreach gateways. Concrete
  backends are **driven adapters** behind those ports.
- **Core depends only on port interfaces; backends are injected at the edge.** This is precisely
  the "pick your own DB/provider" requirement: a user swaps a Postgres adapter for a Mongo adapter,
  or a Gemini adapter for an OpenAI adapter, with **zero changes to the core**.
- **Use the driving-side symmetry for testability.** Cockburn''s stated intent - "developed and
  tested in isolation from its eventual run-time devices and databases" - means every outbound port
  gets an in-memory fake adapter for fast, network-free unit tests (satisfies CLAUDE.md 5.5
  "no network in unit tests").
- **Ports expressed in the domain''s own vocabulary**, not the vendor''s (e.g. `CompanyRepository`,
  not `MongoCollection`). This keeps the contract backend-agnostic and prevents a vendor''s data
  model leaking into the core.

## Reject / watch out for

- **Don''t over-port trivial dependencies.** A port per genuinely swappable boundary; not a port
  around every helper (avoids CLAUDE.md 5.2 over-abstraction).
- **The hexagon shape is not literal** - six sides carry no meaning. Use it only as a mental model
  for inside vs outside.
