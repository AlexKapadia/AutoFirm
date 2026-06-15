# INDEX — A5: Claude Code CLI substrate

Branch: A5 (Platform Engineering). Status: **seeded, not yet QA-PASSED** (per RESEARCH-PROGRAM 2).
Owner: single-writer for docs/research/A5-claude-code-substrate/.

## Questions covered
- **L1.A5.1** CLI capabilities/limits (sessions, subagents, hooks, MCP, headless, settings)
- **L1.A5.2** Determinism, resumability & idempotency of CLI sessions
- **L1.A5.3** Tool/permission model & sandboxing of the substrate

## Sources (one folder per source)
| # | Folder | Source | Tier | Primary question(s) |
|---|---|---|---|---|
| 01 | 01-cc-headless-sdk | CC docs: Run Claude Code programmatically (headless) | High | A5.1, A5.2, A5.3 |
| 02 | 02-cc-subagents | CC docs: Create custom subagents | High | A5.1, A5.3 |
| 03 | 03-cc-hooks | CC docs: Hooks reference | High | A5.1, A5.3 |
| 04 | 04-cc-settings | CC docs: Settings | High | A5.1, A5.3 |
| 05 | 05-cc-permissions | CC docs: Configure permissions | High | A5.3, A5.1 |
| 06 | 06-cc-sandboxing | CC docs: Configure the sandboxed Bash tool | High | A5.3, A5.1 |
| 07 | 07-cc-mcp | CC docs: Connect Claude Code to tools via MCP | High | A5.1, A5.3 |
| 08 | 08-cc-sessions | CC docs: Manage sessions (+ CLI reference) | High | A5.2, A5.1 |
| 09 | 09-miller-capability-myths | Miller, Yee, Shapiro 2003, "Capability Myths Demolished" (SRL2003-02, JHU) | High | A5.3 |
| 10 | 10-thinkingmachines-determinism | He et al. 2025, "Defeating Nondeterminism in LLM Inference" (Thinking Machines Lab) | Moderate (up-rated) | A5.2 |

Synthesis: SYNTHESIS.md (surveyed alternative space + cited AutoFirm recommendation).

## Source-count check (DEPTH-RUBRIC 1)
- Safety/correctness-critical claims (permission/sandbox/fail-closed/capability model) corroborated
  across >=3 independent doc pages + Miller 2003 primary theory (sources 03,04,05,06,09).
- Determinism (correctness-critical) corroborated by source 10 + independent Willison summary +
  related arXiv:2601.17768 (>=3).
- Substrate-capability claims grounded in the vendor primary spec (source of record), cross-checked
  across multiple independent doc pages.
