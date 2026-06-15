# SUMMARY — A Survey of Agent Interoperability Protocols (MCP, ACP, A2A, ANP)

## Full citation
- **Title:** A Survey of Agent Interoperability Protocols: Model Context Protocol (MCP),
  Agent Communication Protocol (ACP), Agent-to-Agent Protocol (A2A), and Agent Network
  Protocol (ANP)
- **Authors/Org:** Abul Ehtesham, Aditi Singh, Gaurav Kumar Gupta, Saket Kumar
- **Year:** 2025 (v1 submitted 3 May 2025; v2 23 May 2025)
- **Venue:** arXiv preprint (cs.AI)
- **URL/DOI:** https://arxiv.org/abs/2505.02279 · HTML: https://arxiv.org/html/2505.02279v1

## Questions it informs
- **L1.A2.1** (protocols & message schemas — PRIMARY)
- L1.A2.2 (interaction modes / coordination patterns — supporting)

## GRADE tier: Moderate
arXiv preprint with methods + a structured comparative analysis across four named, publicly
documented protocols. **Down-rate:** not peer-reviewed; fast-moving area, details age quickly
(MCP later donated to Linux Foundation Dec 2025; A2A to LF Jun 2025). **Up-rate:** the four
protocols are independently documented primary specs, so per-protocol claims are corroborable
against the vendor specs themselves. Held at Moderate; per-protocol facts cross-checked.

## Key claims (exact, with locators)

**Common substrate.** MCP and A2A both build on the "JSON-RPC 2.0 specification" (MCP S4.3;
A2A S5.3); ACP is "REST-native" over HTTP; ANP uses "HTTP(S) for transport and JSON-LD for data
formatting" (S7.3).

**Per-protocol (creator, year, transport, discovery, identity, modes, stated limitation):**

| Protocol | Creator (yr) | Transport / format | Discovery | Identity/security | Modes | Stated limitation |
|---|---|---|---|---|---|---|
| **MCP** | Anthropic (2024) | JSON-RPC 2.0; Stdio + HTTP w/ optional SSE (S4.3) | Manual reg. / static URL (Tbl 7) | Token auth; DIDs optional; TLS, mutual auth (Tbl 3,7) | Sync requests w/ timeouts; async notifications (S4.5) | "Centralized server assumption; prompt injection risks" (Tbl 7) |
| **ACP** | IBM BeeAI (2024) | REST-native performative messaging, multi-part; HTTP w/ incremental streams | Registry / manifest at well-known URLs (S6.2-6.3) | Bearer tokens, mutual TLS, JWS; signed Agent Detail manifests (Tbl 5,7) | "Asynchronous-first" (S2); sync + streaming (S6.3) | "Registry required; strong assumptions on server control" (Tbl 7) |
| **A2A** | Google (2024) | JSON-RPC 2.0 over HTTP + SSE (S5.3) | "Agent Card retrieval via HTTP"; Agent Cards describe skills (S5.1.2, S5.2) | DID handshake or out-of-band headers; TLS, JWS, schema validation (Tbl 4,7) | Sync task invocation; optional SSE streaming or Push Notifications (S5.3) | "Enterprise-centric; assumes agent catalog" (Tbl 7) |
| **ANP** | Open-source (2024) | HTTP(S) + JSON-LD graphs (S7.3) | "Search Engine Discovery"; ADP doc in JSON-LD at `.well-known/agent-descriptions` (S7.2) | Decentralized Identifiers (DID), esp. `did:wba`; DID public keys (Tbl 6,7) | "Stateless; DID-authenticated tokens used across connections" (Tbl 7) | "High negotiation overhead; evolving adoption ecosystem" (Tbl 7) |

**Phased adoption roadmap (S9).** Exact recommended sequence:
1. "MCP for Tool Invocation" (S9.1)
2. "ACP for Rich Interaction" (S9.2)
3. "A2A for Enterprise Collaboration" (S9.3)
4. "ANP for Open Agent Markets" (S9.4)

Rationale (quoted): "This phased approach enables organizations to adopt agent communication
protocols progressively, maximizing interoperability while minimizing integration complexity at
each stage" (S9.4).

**Comparative dimensions (S8/Tbl 7).** Protocols compared across interaction modes, discovery
mechanisms, communication patterns, and security models.

## Reproducibility note
Per-protocol facts are re-derivable from each protocol's own public spec (MCP spec; Google A2A
spec; IBM ACP/BeeAI docs; ANP agent-network-protocol repo). A reviewer can confirm the
JSON-RPC-2.0 / REST / JSON-LD split directly from those specs.
