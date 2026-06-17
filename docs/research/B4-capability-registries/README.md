# B4 — Capability Registries / Growable Skill Catalog (Workstream 4) — Research Library

Deep, primary-sourced research for a **growable, tamper-evident capability registry**: how agents
discover, package, and safely load capabilities, with an append-only audit trail and
least-privilege security. Institution-grade bar; research gates building (CLAUDE.md §2 CRO, §3.3,
§4.6). One folder per source.

## Sources (one folder per source — §4.6)

| Folder | Source | One-line takeaway |
|--------|--------|-------------------|
| `01-fowler-event-sourcing-cqrs` | Fowler — Event Sourcing / CQRS (2005, martinfowler.com) | An **append-only event log** is the source of truth; current state is a projection — a natural capability-growth log. |
| `02-rfc6962-hash-chained-append-only-log` | Laurie, Langley, Kasper — RFC 6962 (IETF, 2013) | **Tamper-evident Merkle log**: leaf `SHA-256(0x00‖d)`, node `SHA-256(0x01‖L‖R)`, `k` = largest power of two `< n`. |
| `03-mcp-registry-aaif-discovery` | MCP Registry (Anthropic / AAIF, 2025) | Runtime **capability discovery + metadata** for Model Context Protocol servers/tools. |
| `04-anthropic-agent-skills-nl-packaging` | Anthropic — Agent Skills (2025–26) | **Natural-language capability packaging** with progressive disclosure; "treat like installing software." |
| `05-capability-based-security-least-privilege` | Dennis & Van Horn (CACM 1966); SkillFortify (2026) | **Unforgeable capabilities** grant least-privilege access — authority is the token, not an ACL check. |
| `06-supply-chain-security-dynamic-skills` | Li et al.; SkillFortify; SKILL-INJECT (2026) | Dynamically-loaded skills are a **supply-chain attack surface**; sign, scope, and verify before load. |
| `07-org-capability-growth-modelling` | Teece, Pisano, Shuen (SMJ 1997); Kogut & Zander (Org Sci 1992) | **Dynamic-capabilities / combinative-capabilities** theory for modelling how an org's capability set grows. |
| `08-plugin-extension-registry-architecture` | Microsoft — VS Code extension architecture (docs) | A **growable plugin/extension registry** pattern (contribution points, activation events) — not hardcoded. |

## Design spec
- `registry-design-and-generality-spec.md` — synthesises the sources into the registry design:
  append-only hash-chained capability log, capability-based access scoping, signed-skill
  verification, and the generality guardrails.

## Faithfulness status (CRO Gate-0)
All eight sources carry complete citations (title, authors/org, year, venue, URL/DOI). The
RFC-6962 hashing reproduced in `02` and in the spec was **verified verbatim 2026-06-17 against
rfc-editor.org/rfc/rfc6962 §2.1**. No overclaims found.
