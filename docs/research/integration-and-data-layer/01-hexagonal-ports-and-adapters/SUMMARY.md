# Hexagonal Architecture (Ports & Adapters)

**Citation.** Alistair Cockburn, "Hexagonal Architecture" (originally "Ports and Adapters"),
alistair.cockburn.us/hexagonal-architecture. First proposed mid-1990s on the WikiWikiWeb; renamed
"Ports and Adapters" in 2005. Corroborated against Wikipedia, "Hexagonal architecture (software)"
(en.wikipedia.org/wiki/Hexagonal_architecture_(software)) and AWS Prescriptive Guidance,
"Hexagonal architecture pattern"
(docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/hexagonal-architecture.html).

> Note: alistair.cockburn.us currently serves an expired TLS certificate, so the primary text was
> read via the corroborating secondary sources above, which quote Cockburn directly. Claims below
> are limited to what those sources attribute verbatim to Cockburn.

## Stated intent (verbatim, attributed to Cockburn)

> "Allow an application to equally be driven by users, programs, automated test or batch scripts,
> and to be developed and tested in isolation from its eventual run-time devices and databases."

## Origin (verbatim)

Cockburn invented the pattern "in an attempt to avoid known structural pitfalls in object-oriented
software design, such as undesired dependencies between layers and contamination of user interface
code with business logic." In June 2005 he had "an aha! moment ... in which I saw that the facets
of the hexagon are ports and the objects between the two hexagons are adapters."

## Core concepts

- **The application (the hexagon).** Domain/business logic sits inside; it knows nothing about the
  technologies outside.
- **Ports.** A boundary/interface defined *by the application* in its own terms ("the facets of
  the hexagon are ports"). A port describes *what* the application needs or offers, not *how* it is
  delivered.
- **Adapters.** "the objects between the two hexagons are adapters." An adapter translates between
  the outside technology and a port: "As events arrive from the outside world at a port, a
  technology-specific adapter converts it into a usable procedure call or message and passes it to
  the application."
- **Symmetry of inside/outside.** All outside actors (UI, tests, batch, DBs, queues) connect the
  same way, so the core is agnostic to which technology is on the other side of a port.

## Driving vs driven sides (primary vs secondary)

Standard elaboration (Wikipedia / AWS, consistent with Cockburn's later writing):

- **Driving (primary) adapters** call *into* the application via *inbound* ports - REST controller,
  CLI, test harness.
- **Driven (secondary) adapters** are *called by* the application via *outbound* ports - database
  repository, message publisher, email/SMS gateway, AI-provider client. The application defines the
  outbound port (interface); the adapter implements it. This is where DB/external-service
  swappability lives.

This left/right asymmetry is the mechanism for backend-agnostic design: the core depends only on
outbound *port interfaces*, and concrete backends are *configurable dependencies* injected at the
edge.

## Relationship to other patterns

- A predecessor/sibling of the **Onion** and **Clean Architecture** layered models - all enforce
  that dependencies point *inward* toward the domain.
- The **Dependency Inversion Principle** is the enabling mechanism: high-level policy (domain)
  defines the interface; low-level detail (adapter) depends on it, not vice-versa.
