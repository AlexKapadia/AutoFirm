# 05 — Capability-based security — unforgeable, least-privilege capabilities

> Workstream B4. This is the formal security model that keeps a *dynamic* capability
> from becoming a *forgeable* one. Classic object-capability theory (Dennis & Van
> Horn, 1966) plus modern formal adaptations to AI skills (SkillFortify) give W4
> the rules under which capabilities stay **unforgeable, least-privilege, and
> confined** even as the registry grows to thousands of entries.

## Full citation

- **J. B. Dennis & E. C. Van Horn, "Programming Semantics for Multiprogrammed
  Computations"**, *Communications of the ACM*, **1966** — origin of the capability
  (an unforgeable token of authority). DOI: 10.1145/365230.365252.
- **Object-capability model**, foundational survey (Mark S. Miller et al. lineage;
  *Robust Composition*, 2006). Wikipedia overview:
  <https://en.wikipedia.org/wiki/Object-capability_model> and
  <https://en.wikipedia.org/wiki/Capability-based_security>
- **V. P. Bhardwaj, "Formal Analysis and Supply Chain Security for Agentic AI
  Skills" (SkillFortify)**, **arXiv:2603.00195v1**, Feb 2026 — formal capability
  lattice + confinement theorem for agent skills.
  <https://arxiv.org/html/2603.00195v1>
- **"A Formal Security Framework for MCP-Based AI Agents"**, **arXiv:2604.05969** —
  capability/verification model for MCP agents (corroborating).

## Faithful structured summary (definitions reproduced exactly)

**Capability (Dennis–Van Horn / obj-cap).** *"A capability describes a transferable
right to perform one or more operations on a given object."* It is *"a communicable,
unforgeable token of authority that refers to a value which references an object
along with an associated set of access rights."*

**Two non-negotiable properties:**
- **Unforgeability:** *"Capabilities are unforgeable and can only be created or
  passed by processes that already have them. You can't just create a new
  capability out of thin air."* Authority is held, never fabricated.
- **Authority by reference only (no ambient authority):** to act on an object you
  must *hold* a capability to it; mere knowledge of a name grants nothing. This
  *"makes privilege escalation impossible"* by construction — there is no ambient
  permission to escalate from.

**Least privilege & confinement.** Capability systems realise least privilege
because *"programs directly share capabilities with each other according to the
principle of least privilege."* A subject's authority is exactly the transitive
closure of the capabilities it holds — nothing more.

**SkillFortify formalisation (reproduced exactly):**
- **Capability Set (Definition 4.3):** a function mapping resources
  `{filesystem, network, environment, shell, skill_invoke, clipboard, browser,
  database}` to access levels `{NONE, READ, WRITE, ADMIN}`, forming a **complete
  lattice**. (A capability is a point in this lattice; "more authority" = lattice
  join.)
- **Capability Confinement (Theorem 5.6):** in capability-safe execution, *"skills
  cannot acquire authority beyond the transitive closure of declared
  capabilities."* — i.e. a skill's *runtime* authority is upper-bounded by its
  *declared* authority.
- **Static analysis soundness (Theorem 4.9):** *"if analysis reports no violations,
  concrete execution cannot exceed declared capabilities."* (Declaration is
  enforceable, not advisory.)
- **`Permits()` check (Definition 5.3):** runtime resource access is gated by an
  explicit permit derived from the held capability set — deny if not permitted.

**The lattice property is what makes it scale to thousands.** Because capability
composition is lattice join/meet, "least authority for a task" is computable and
monotone; you never need a hand-maintained enum of allowed combinations.

## Best parts to take (mapped to the W4 design)

1. **A W4 capability is an unforgeable token, not a string.** Bind each
   `CapabilityDescriptor` to a cryptographic identity (the emitting role/org + a
   signature) so it cannot be fabricated by a process that didn't earn it via the
   audited org lifecycle. *Maps to:* W4 "unforgeable" + signed loading (source 06).
2. **Declared capability set as a lattice over scoped resources.** Model each
   capability's authority as a point in the `{NONE,READ,WRITE,ADMIN}` lattice over
   scoped resources; "least privilege for this role" = the lattice meet of what its
   responsibilities require. No magic allow-lists. *Maps to:* W4 least-privilege +
   generality (computed, not enumerated).
3. **Confinement bound enforced at load (`Permits()` gate).** Runtime authority of
   a dynamically-loaded capability is upper-bounded by its declaration; deny any
   access outside the transitive closure. *Maps to:* W4 "least-privilege dynamic
   capability loading" + fail-closed.
4. **No ambient authority in the projection.** The `org_event → capability`
   projection grants a role a capability *only* because an audited event conferred
   it; there is no global "anyone can do X". A FIRED role's authority drops to the
   lattice bottom. *Maps to:* W4 unforgeable + append-only revocation.
5. **Declaration is enforceable (static-soundness analogue).** W4 must *verify*, not
   trust, that a loaded capability cannot exceed its descriptor — make the
   descriptor the enforced upper bound, tested adversarially. *Maps to:* W4 security
   controls + CLAUDE.md §5.6.

## Cross-links

- **06** supply-chain security — what happens when these properties are absent.
- **02** hash-chain — binds capability provenance to a tamper-evident log.
- Repo: `A7-safety-and-control/05-camel-defeating-prompt-injection-by-design`
  (capability/control-data separation as injection defence).
