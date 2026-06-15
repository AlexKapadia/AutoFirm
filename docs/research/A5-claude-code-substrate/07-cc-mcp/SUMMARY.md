# SUMMARY — Claude Code: Connect Claude Code to tools via MCP

## Full citation
- **Title:** "Connect Claude Code to tools via MCP"
- **Author/Org:** Anthropic (Claude Code documentation)
- **Year:** 2026 (live docs; fetched 2026-06-15)
- **Venue/Publisher:** Official Claude Code documentation
- **URL:** https://code.claude.com/docs/en/mcp
- **Underlying standard:** Model Context Protocol — https://modelcontextprotocol.io/introduction

## Questions informed
- **L1.A5.1** MCP integration capability (the substrate's external-tool plane).
- **L1.A5.3** MCP scoping, restriction, and untrusted-server risk.

## GRADE tier
**High** (primary source of record for how the substrate uses MCP). The MCP standard itself is an
independent open spec (modelcontextprotocol.io). Prompt-injection risk corroborated by the
Security page and by agentic-AI threat-model literature (A7 branch, TRiSM).

## Key claims (exact, with locators)

1. **Transports.** Remote **HTTP** (recommended; `--transport http`; `.mcp.json` `type` accepts
   `streamable-http` as alias for `http`); **SSE** (`--transport sse`, **deprecated** — "Use HTTP
   servers instead"); local **stdio** (`--transport stdio`, local process; `--` separates Claude
   options from the server command); **WebSocket** (`type: "ws"` in `.mcp.json`; "supports neither
   OAuth nor the `--transport` flag"; header-only auth).

2. **Install scopes (3).** **Local** (default; current project only; private; stored in
   `~/.claude.json`); **Project** (current project; shared via version control; stored in
   `.mcp.json` in project root); **User** (all your projects; stored in `~/.claude.json`). Plus
   enterprise/managed via managed configuration. Project-scoped servers awaiting approval show as
   "Pending approval" in `claude mcp list`.

3. **Tool naming scheme.** `mcp__<server>__<tool>` (e.g. `mcp__puppeteer__puppeteer_navigate`).
   Plugin-bundled: `mcp__plugin_<plugin-name>_<server-name>__<tool-name>` (non-[A-Za-z0-9_-] chars
   replaced with `_`). Permission rules: `mcp__puppeteer` (whole server), `mcp__puppeteer__*`
   (wildcard, all its tools), exact tool name.

4. **Authentication.** OAuth 2.0 for remote servers via `/mcp`. stdio servers take `--env KEY=val`
   (set in the server's env, not Claude Code's). HTTP/WS support `headers` and dynamic
   `headersHelper`. Per-server `timeout` (ms) in `.mcp.json` overrides `MCP_TOOL_TIMEOUT`
   (hard wall-clock per tool call; values <1000 ignored).

5. **Reliability.** HTTP/SSE auto-reconnect on mid-session disconnect: exponential backoff, up to
   5 attempts (1s, doubling); after 5 failures marked failed, retry from `/mcp`. Initial-connection
   retry up to 3 times on transient (5xx/refused/timeout) errors (v2.1.121); auth/not-found errors
   NOT retried. Stdio servers are NOT auto-reconnected.

6. **Restriction flags / managed control.** `--strict-mcp-config` and `--bare` restrict which MCP
   servers load; enterprise managed MCP config; `allowedMcpServers`/`deniedMcpServers` policies;
   `allowManagedMcpServersOnly` (managed). These also cover MCP servers declared in subagent
   frontmatter (v2.1.153). `--strict-mcp-config` does NOT filter servers passed inline via
   `--agents`/SDK `agents` (explicit caller input). `deny: ["mcp__*"]` removes all MCP tools.

7. **Untrusted-server risk (security).** "Verify you trust each server before connecting it.
   Servers that fetch external content can expose you to **prompt injection risk**." (Links to
   Security page §protect-against-prompt-injection.)

## Reproducibility note
Re-fetch and verify the four transport names (HTTP/SSE-deprecated/stdio/WS), the 3-scope table,
the `mcp__server__tool` naming scheme, and the "prompt injection risk" trust warning. The MCP
standard is independently verifiable at modelcontextprotocol.io.
