<h1 align="center">AutoFirm</h1>

<p align="center">
  <strong>The infrastructure for an autonomous agent company that researches, validates, builds, markets, funds, and operates real companies — end to end.</strong>
</p>

<p align="center">
  <em>A meta-company: a platform that builds systems, automations, and its own ways of working.</em>
</p>

<p align="center">
  <img alt="status" src="https://img.shields.io/badge/status-early%20development-orange">
  <img alt="license" src="https://img.shields.io/badge/license-MIT-blue">
</p>

---

> **Status: early development.** AutoFirm is being built in the open, gate by gate, to an institution-grade
> bar. The foundation and the deep research program come first — **nothing is built before it is researched.**
> This README describes the direction; see [`docs/roadmap.md`](docs/roadmap.md) for exactly what is and isn't done.

## What AutoFirm is

You give AutoFirm an idea. It does the unglamorous, nitty-gritty work of turning that idea into a real,
operating company — and it does it as a **company of AI agents** that behaves like a real org:

- **Researches & validates first** — finds the *real* market gap (not hype), the way a sharp entrepreneur and
  a sceptical investor would, grounded in peer-reviewed and primary sources.
- **Plans, then builds** — architecture, product, a genuinely good UI, the works.
- **Operates** — marketing, outreach, financials (accurate, zero numerical errors), and the connective tissue
  to real services (databases, AI providers, integrations).
- **Self-organises** — a strict, audited hierarchy of agents that can be **hired, fired, and re-scoped** as the
  company's needs change. Every manager defines the role of its reports. New niche roles are created when gaps
  appear.
- **Runs autonomously** — sessions hand off cleanly when context runs out and **auto-resume** so the company
  can run for days or weeks unattended, fully logged and traceable.

## Principles (non-negotiable)

AutoFirm is built under a strict, self-activating engineering contract ([`CLAUDE.md`](CLAUDE.md)):

- **Research-first.** Deep, peer-reviewed research gates every build decision. See [`docs/research/`](docs/research/).
- **Evidence-driven.** Competing approaches run on their own branches and only the measured winner lands on `main`.
- **Institution-grade & secure by default.** Fail-closed, least privilege, append-only audit log, maintained
  threat model, a global kill-switch.
- **Tests with teeth.** Adversarial, property-based, mutation-tested suites — a green suite of easy tests is
  treated as worthless.
- **General, never overfit.** It must work for *any* company, not one demo.
- **Everything flows, heartbeats, and learns.**

## Architecture direction

- **Substrate:** orchestrated **Claude Code CLI sessions** — each role/team is a session with its own scoped
  brief, communicating over an audited message bus, handing off and auto-resuming to run long-haul.
- **Dynamic org:** a modular hierarchy whose roles are data, so the org can restructure itself like a real company.
- **Learning layer:** a persistent, evolving knowledge base (the right infrastructure for this is an open
  research question — see [`docs/research/`](docs/research/)).

> These are directional. The ratified architecture lives in [`docs/architecture/`](docs/architecture/) once the
> research gate is passed.

## Repository layout

```
CLAUDE.md            The binding engineering contract & operating mode
docs/research/       The deep research library — one folder per source
docs/architecture/   Ratified architecture & data contracts
docs/design/         Design briefs (when a UI is in scope)
docs/roadmap.md      Gated phase plan with live status
docs/threat-model.md Maintained STRIDE threat model
src/                 Platform source (built after the research gate)
tests/               Adversarial / property / mutation test suites
evidence/            Self-contained statistical & visual evidence showcase
```

## License

[MIT](LICENSE) © 2026 Alex Kapadia
