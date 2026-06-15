# BEST-PARTS — AI authorship / copyright of generated works

## ADOPT
- **A1. Flag AI-generated artifacts as POSSIBLY-uncopyrightable.** Because purely AI-authored output is
  not copyrightable in the US, AutoFirm's artifact-generation engines (L2.B15 docs/decks/models; L2.B13
  designs; client code) must **tag each output with its authorship provenance** (human-directed vs.
  autonomous) and **surface the copyright risk** to the client. Build implication: an `authorship_
  provenance` field + a copyright-status advisory on every generated deliverable.
- **A2. Preserve and record human creative control where copyright matters.** When a client needs
  enforceable copyright, the playbook routes the work through a **human-in-the-loop creative-control
  step** (a human makes the expressive choices the AI then executes) and **logs that human contribution**
  — the audit trail becomes the evidence of human authorship for registration. Aligns with the creative-
  control test verbatim.
- **A3. Disclaimer discipline on registration.** If a client registers copyright in an AI-assisted work,
  the playbook **auto-generates the AI-disclaimer** (identifying AI-generated portions) required by the
  2023 Guidance — a concrete, automatable compliance step.

## REJECT / DEFER
- **R1. REJECT asserting AutoFirm/its agents as "authors."** The agent is a tool; never represent agent-
  generated content as independently copyrighted by the agent. This prevents a false IP claim (which
  would also be a misrepresentation risk).
- **R2. DEFER non-US authorship regimes** (e.g. UK CDPA s.9(3) "computer-generated works" which DOES
  grant a limited authorship) to the jurisdiction module — note explicitly that the human-authorship
  rule is **US-specific** and other jurisdictions differ (generality caveat, CLAUDE.md §3.9).

## Build implication (concrete)
- **Component:** `legal/ip/ai_authorship_advisor.py`; integrates with L2.B15/B13 generators.
- **Contract:** `GeneratedArtifact{ ..., authorship_provenance ∈ {human_directed, ai_assisted,
  ai_autonomous}, copyright_status_advisory, human_contribution_log_ref, ai_disclaimer }`.
- **Test:** an ai_autonomous artifact must carry a "not copyrightable (US)" advisory; an ai_assisted
  artifact intended for registration must have a non-empty human_contribution_log + generated disclaimer;
  generality test asserts the advisory is jurisdiction-aware (US vs UK differ).
