# 04 — Anthropic Agent Skills — NL capability packaging & progressive disclosure

> Workstream B4. Agent Skills are the production pattern for **declaring,
> composing, versioning, and discovering a capability in natural language** — a
> capability as a self-contained, version-controlled folder with machine-readable
> metadata that an agent loads *on demand*. This is the model for how a W4
> capability is *packaged and dynamically loaded* (and why dynamic loading must be
> signed/verified — see source 06).

## Full citation

- **Anthropic, "Agent Skills — Overview"**, Claude Developer Platform docs (2025–26).
  <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview>
- **Anthropic Engineering, "Equipping agents for the real world with Agent
  Skills"**. <https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills>
- Skills API: `/v1/skills` endpoints; beta headers `skills-2025-10-02`,
  `code-execution-2025-08-25`, `files-api-2025-04-14`.
- Open-source skills: <https://github.com/anthropics/skills>

## Faithful structured summary (mechanics reproduced exactly)

**What a Skill is.** *"Modular capabilities that extend Claude's functionality.
Each Skill packages instructions, metadata, and optional resources (scripts,
templates) that Claude uses automatically when relevant."* A Skill is a
**filesystem directory**, version-controlled, organised *"like an onboarding guide
you'd create for a new team member."*

**Declaration — `SKILL.md` YAML frontmatter (required fields reproduced exactly):**

```yaml
---
name: pdf-processing          # ≤64 chars; lowercase letters, numbers, hyphens only;
                              #   no XML tags; reserved words "anthropic"/"claude" banned
description: Extract text and tables from PDF files, fill forms, merge documents.
            Use when working with PDF files or when the user mentions PDFs, forms,
            or document extraction.   # non-empty, ≤1024 chars, no XML tags;
                              #   MUST state both WHAT it does and WHEN to use it
---
```

Required fields are **`name`** and **`description`**. The `description` is the
*discovery surface*: it is what the agent matches a request against.

**Progressive disclosure — three levels (reproduced exactly):**

| Level | When loaded | Token cost | Content |
|---|---|---|---|
| **1 — Metadata** | Always (startup) | ~100 tokens/skill | `name` + `description` from YAML frontmatter |
| **2 — Instructions** | When skill triggered | < 5k tokens | `SKILL.md` body (workflows, guidance) |
| **3 — Resources/code** | As needed | effectively unlimited | bundled `*.md`, scripts run via bash (code never enters context) |

Mechanism: at startup only metadata is in the system prompt — *"you can install
many Skills without context penalty; Claude only knows each Skill exists and when
to use it."* On a match, the agent reads `SKILL.md` via bash (Level 2); referenced
files / scripts load only when needed (Level 3). Scripts give **deterministic
operations without consuming context** — *"the script code itself never enters
context."*

**Composition.** *"Compose capabilities: Combine Skills to build complex
workflows."* Skills are independent directories that stack; the agent selects and
chains the relevant ones at runtime.

**Versioning & management.** The Skills API (`/v1/skills`) gives *"programmatic
control over skill versioning and management."* Skills are self-contained,
independently deployable, version-controlled folders.

**Security (Anthropic's own warning, verbatim spirit):** *"Use Skills only from
trusted sources… a malicious Skill can direct Claude to invoke tools or execute
code in ways that don't match the Skill's stated purpose."* Risks named:
**prompt-injection via fetched external content, tool misuse, data exfiltration**;
remedy named: **audit thoroughly, treat like installing software.** Runtime is
*capability-scoped by surface* — API skills have **no network access** and no
runtime package install; Claude Code skills have full local access. (This
surface-scoped privilege is a real-world least-privilege precedent for W4.)

## Best parts to take (mapped to the W4 design)

1. **`CapabilityDescriptor` ≈ SKILL.md frontmatter.** Adopt the `name` +
   `description`(what + when) contract as the human/machine discovery surface of a
   W4 capability; keep it short, declarative, NL-matchable. *Maps to:* W4
   capabilities derived from `RoleCharter.responsibilities` (an NL "what + when").
2. **Progressive disclosure for thousands of capabilities.** At maturity W4 holds
   thousands of capabilities; mirror Level-1 metadata-only indexing so the *whole
   registry* is cheap to scan and only the matched descriptor's detail is
   materialised. *Maps to:* W4 "thousands of capabilities, no ceiling".
3. **Capability = self-contained, version-controlled unit with a version stamp.**
   Each `CapabilityRegistryEvent` records the descriptor *version*; composition is
   explicit and replayable. *Maps to:* W4 versioned descriptors + pure-replay.
4. **Surface-scoped runtime privilege is least-privilege in practice.** Mirror "API
   skills get no network" — a W4 capability is loaded with *only* the authority its
   declaration claims, scoped by context. *Maps to:* W4 least-privilege loading.
5. **Anthropic's own security warning is the W4 mandate.** "No structural
   separation between instruction and data" + "treat like installing software"
   ⇒ W4 dynamic capability loading must be **signed, verified, and fail-closed**
   (source 06), never load-on-trust. *Maps to:* W4 security controls.

## Cross-links

- **06** supply-chain security — quantifies the exact attacks Anthropic warns of.
- **03** MCP registry — the discovery/catalog counterpart to skill packaging.
