# BEST-PARTS — Interoperability Protocols Survey

## What AutoFirm should ADOPT and why

1. **MCP as the tool/data plane (already native).** AutoFirm runs on Claude Code CLI, whose
   tool layer IS MCP. ADOPT MCP for every agent->tool and agent->data call. Build implication:
   the integration layer (A8) standardizes on JSON-RPC-2.0 MCP servers; no bespoke tool RPC.

2. **A2A-style "Agent Card" capability descriptor for inter-team comms.** ADOPT a typed,
   signed capability manifest per agent/role (skills, inputs, outputs, tools, boundaries).
   Build implication: the message-schema contract for L2.A1/L2.ORG carries an Agent-Card-shaped
   header so the orchestrator can route by declared capability, not by guesswork. This directly
   attacks MAST FM "duplicate agent roles" / mis-delegation (see source 02).

3. **JWS-signed messages + DID/identity per agent (from A2A/ACP/ANP).** ADOPT message signing
   and per-agent scoped identity. Build implication: every inter-agent message is signed and
   attributable -> feeds the append-only audit log (A6) and least-privilege (A7, CLAUDE S5.6).
   This is the "audited inter-team comms" top priority for A2 made concrete.

4. **Async-first + streaming + push (from ACP/A2A).** ADOPT async-first messaging with
   streaming progress and push notifications for long-horizon work (A3). Build implication:
   handoff/resume protocol uses durable async messages, not blocking RPC.

5. **The phased adoption ordering as a build sequence.** ADOPT: tool plane (MCP) first, then
   rich typed inter-agent messaging, then capability-based collaboration. Open agent
   marketplaces (ANP) are DEFERRED.

## What AutoFirm should REJECT / DEFER and why

- **REJECT centralized-server-only assumptions of MCP for the *inter-agent* plane.** MCP's
  "centralized server assumption" (Tbl 7) is fine for tools but a single point of failure for
  team-to-team comms; use a signed-message contract there instead.
- **DEFER ANP / open decentralized marketplaces.** "High negotiation overhead; evolving
  adoption ecosystem" (Tbl 7) — AutoFirm's agents are a *governed internal company*, not an open
  market, so DID-marketplace discovery is out of scope until cross-org federation is needed.
- **REJECT relying on the survey's tier alone for any safety claim.** It is Moderate (preprint);
  every security control it suggests is corroborated by sources 02/04 and CLAUDE S5.6 before use.

## Concrete build implication
Defines the **inter-agent message contract** for L2.A1/L2.ORG: a typed envelope =
{Agent-Card capability header, signed (JWS) body, conversation-id, async/stream mode,
scoped sender identity}. Drives the audit-log test (every message attributable) and the
routing test (orchestrator dispatches only to a capability that declares the needed skill).
