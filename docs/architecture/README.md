# AutoFirm Architecture — ratified at Gate 2

> **Status: not yet ratified.** Architecture is intentionally *not* written before the research gate (Gate 1)
> passes. Pre-research architecture would violate the research-first mandate (`CLAUDE.md` §3.3).

When Gate 1 is green, this directory will hold:

- `overview.md` — the system architecture, every decision cited to a `docs/research/` source.
- `data-contracts.md` — the typed contracts between components (the message bus, role specs, audit records).
- `org-model.md` — the dynamic, modular org model (roles-as-data, hierarchy, hire/fire/re-scope).
- `substrate.md` — how Claude Code CLI sessions are spawned, scoped, handed off, and auto-resumed.
- Black-&-white flow diagrams (HTML + PNG) per component and for the whole system (exported to `evidence/`).

Directional intent (to be confirmed or overturned by research, not assumed): orchestrated Claude Code CLI
sessions over an audited message bus, a roles-as-data dynamic org, and a researched-best learning layer. See
the project memory and `README.md` for the current direction.
