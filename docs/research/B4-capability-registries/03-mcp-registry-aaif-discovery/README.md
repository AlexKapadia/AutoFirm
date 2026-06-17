# 03 — MCP Registry (AAIF) — runtime capability discovery & metadata

> Workstream B4. The official MCP Registry is the closest production analogue of a
> **growable, federated, schema-versioned capability catalog** — the antithesis of
> a hardcoded enum. It teaches W4 how to model `CapabilityDescriptor` metadata
> (capabilities, versioning, namespace, verification status) and — by what it
> deliberately does NOT do — exactly where W4 must add its own trust layer.

## Full citation

- **Model Context Protocol — Official MCP Registry** (preview launched **September
  2025**), governed by the **Agentic AI Foundation (AAIF)**. Open catalog + REST
  API backed by an **OpenAPI specification** (`server.json` metadata schema).
  - Spec / repo: <https://github.com/modelcontextprotocol/registry>
  - MCP specification: <https://modelcontextprotocol.io/specification>
- Technical overview used for faithful summary: **WorkOS, "MCP Registry
  Architecture: A Technical Overview"** (2026).
  <https://workos.com/blog/mcp-registry-architecture-technical-overview>
- Corroborating engineering reference on **dynamic tool discovery**:
  agentic-community / `mcp-gateway-registry`, `docs/dynamic-tool-discovery.md`.

## Faithful structured summary (architecture reproduced exactly)

**What it is.** A centralized **metadata catalog + API** enabling AI applications
to *discover* MCP servers and their capabilities at runtime. It is explicitly a
*catalog*, not a runtime proxy. Server publishers submit metadata describing each
server: **endpoint, capabilities, versioning information, namespace identifier**,
input/output schemas, and authentication mechanisms.

**Schema versioning for forward compatibility.** The metadata contract carries its
own **schema version**, *"enabling the registry to evolve its metadata contract
over time while maintaining backward compatibility."* New fields are additive;
older clients keep parsing. (Directly applicable: W4 `CapabilityDescriptor` must be
versioned-and-additive so the registry can grow new descriptor fields without a
migration that rewrites history.)

**Namespace ownership / identity.** Publish-time identity verification:
GitHub-based auth (`io.github.username/*` pattern) and **domain validation via DNS
or HTTP proof**. Namespace **uniqueness** is enforced. This is the registry's
*identity* control (who may claim a name) — distinct from *payload* trust.

**Federation (subregistries).** A canonical upstream registry plus **subregistries**
that, while staying compatible through the **shared OpenAPI schema**, can:
*enrich metadata with ratings and audit information*; *combine published servers
with internal implementations*; and *apply organization-specific policies*. This is
the pattern for a private/internal capability registry that still speaks one schema.

**Dynamic tool discovery (runtime).** Gateways layer a *Dynamic Tool Discovery and
Invocation* capability on top: an agent queries the registry/gateway to *learn
which tools exist at runtime* and decide which it may use — capabilities are not
baked into the agent at build time.

**Trust boundary — what the registry deliberately does NOT do (verbatim spirit):**
> The registry's trust boundary is limited to metadata. It does **not** (in the
> preview) enforce cryptographic validation of server payloads or tools.

It also does not proxy runtime traffic, run/audit servers, or enforce package-level
integrity. **Clients independently verify server responses.** Governance is
community moderation + maintainer-managed denylists. **This gap is the cue for W4:
metadata discovery ≠ trust; W4 must add signing/verification (see source 06).**

## Best parts to take (mapped to the W4 design)

1. **`CapabilityDescriptor` modeled on `server.json` fields.** Carry
   `namespace`/id, `version`, `capabilities`, declared I/O contract, and an
   explicit **`verification_status`** field (verified / unverified / revoked).
   *Maps to:* W4 "CapabilityDescriptor … verification status".
2. **Schema-versioned, additive descriptor evolution.** Stamp every descriptor with
   a schema version; only add fields, never repurpose. The registry grows new
   descriptor *kinds* without rewriting the append-only log. *Maps to:* W4
   generality (no ceiling) + event-sourcing immutability (source 01).
3. **Namespace uniqueness + identity proof at "publish" time.** In W4, a capability
   is "published" when a role's responsibility yields it; its namespace is the
   role/org identity that emitted it. Enforce uniqueness in the projection so two
   roles cannot silently forge the same capability id. *Maps to:* W4 unforgeable
   capabilities (source 04).
4. **Federation = internal vs public capability registries.** Mirror the
   subregistry model: AutoFirm's *internal* per-company capability registry speaks
   the same descriptor schema as a public catalog, enriched with audit/verification.
   *Maps to:* W4 generality across any company.
5. **Treat discovery as untrusted by default.** The MCP registry's explicit
   non-verification of payloads is the cautionary lesson: in W4, a discovered
   capability is **fail-closed** until signed+verified. *Maps to:* W4 security
   controls (source 06) + CLAUDE.md §5.6.

## Cross-links

- **04** capability-security (unforgeable, least-privilege) — closes the trust gap.
- **06** supply-chain security — the concrete attacks this trust gap enables.
- **07** plugin/extension registries — sibling "growable registry" architecture.
