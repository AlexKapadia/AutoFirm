# 08 — Plugin / extension registry architecture (growable, not hardcoded)

> Workstream B4. The engineering blueprint for a registry that is **manifest-driven,
> discoverable, versioned, and enterprise-gateable** — i.e. a registry that *grows*
> as units are added, instead of a hardcoded enum recompiled into the binary. VS
> Code's extension model is the most battle-tested production example.

## Full citation

- **Visual Studio Code — Extension API / Extension Manifest (`package.json`)**,
  Microsoft. <https://code.visualstudio.com/api/get-started/extension-anatomy> and
  manifest reference. Contribution points, `activationEvents`, publisher/name
  unique ID.
- **"Manage extensions in enterprise environments"**, VS Code docs — allow/deny by
  publisher, extension, version, platform.
  <https://code.visualstudio.com/docs/enterprise/extensions>
- Plugin-architecture engineering reference: *"Plugin Architecture in Practice
  (Part 4) — Versioning, Distribution, and Ecosystem"* — filesystem-scan discovery,
  two-level plugin store, manifest as identity card.

## Faithful structured summary (architecture reproduced exactly)

**Manifest as identity + capability advertisement.** *"The manifest serves as the
plugin's identity card, capability advertisement, and integration specification."*
In VS Code the manifest is `package.json` declaring `publisher`, `name`,
`activationEvents`, and **`contributes`** (Contribution Points). **Contribution
Points are static declarations made in the manifest to extend the host** — the host
reads declarations; it does **not** hardcode the set of extensions.

**Unique identity.** *"VS Code uses a combination of the `publisher` and `name`
fields as a unique ID."* (Namespace + name — same identity model as MCP registry,
source 03.)

**Discovery by manifest scan.** *"Filesystem scanning walks a plugins directory to
parse manifests… plugins placed in a well-known directory are automatically
discovered without explicit registration."* Simple, infra-free, deterministic. (For
W4 at small scale; graduates to a catalog/API at large scale — source 03.)

**Distribution / versioning.** *"Separating plugin releases from the manifest and
using a two-level plugin store with an automated publishing system achieves
stability and flexibility"* — the runtime handles multiple plugin sources;
versions are first-class.

**Enterprise gating (least-privilege at the registry edge).** *"VS Code supports
controlling which extensions can be installed by allowing extensions selectively by
publisher, specific extension, version, and platform — only listed extensions are
installable when configured."* This is an **allow-list / policy gate** over a
growable registry: the registry grows freely, but *loading* is policy-gated.

**Activation events.** Extensions declare *when* they activate (`activationEvents`)
— lazy, on-demand loading rather than load-everything-at-startup. (Same principle
as Agent Skills progressive disclosure, source 04.)

## Best parts to take (mapped to the W4 design)

1. **Capabilities are manifest-declared, never enum-coded.** The registry host (W4
   live registry) reads declarations (`CapabilityDescriptor`s projected from
   events) — adding a capability requires *zero host recompilation*. *Maps to:* W4
   "replaces a hardcoded capability/feature list".
2. **`publisher + name` unique identity.** Mirror VS Code's namespace+name identity
   for `CapabilityDescriptor` (emitting role/org + capability name) to prevent
   collisions/forgery in the projection. *Maps to:* W4 unforgeable + source 03/05.
3. **Lazy / on-demand activation.** Capabilities materialise their full detail only
   when matched (cf. `activationEvents` + Agent Skills Level-2 load). *Maps to:* W4
   scaling to thousands.
4. **Enterprise allow/deny gate = least-privilege load policy.** The growable
   registry is decoupled from the *loading policy*: a capability can exist in the
   log yet be **policy-gated from loading** (by publisher/version/verification
   status). Combine with signing/verification (source 06) for fail-closed loading.
   *Maps to:* W4 "least-privilege dynamic capability loading".
5. **Two-level store separates record from release.** Separate the *append-only
   record of growth* (the event log — what was ever conferred) from *what is
   currently loadable* (the active, verified projection). *Maps to:* W4 record vs.
   live registry split.

## Cross-links

- **03** MCP registry — the catalog/API form of the same growable-registry idea.
- **04** Agent Skills — progressive disclosure ≈ activation events.
- **06** supply-chain — why the enterprise allow/deny gate must be signed/verified.
