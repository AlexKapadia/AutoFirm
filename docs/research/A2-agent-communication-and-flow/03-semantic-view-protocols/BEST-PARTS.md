# BEST-PARTS — Semantic View of Agent Communication Protocols

## What AutoFirm should ADOPT and why

1. **A shared ontology / vocabulary layer ABOVE the syntactic envelope.** ADOPT a small,
   versioned domain vocabulary for the company-building doctrine (e.g. canonical names for
   business functions, artifacts, verdicts) so agents mean the same thing by the same term.
   Build implication: the message contract (source 01) carries an `ontology`/`schema-version`
   field (mirrors FIPA-ACL's `ontology` parameter, source 04); receivers reject unknown
   vocabularies (fail-closed). Directly mitigates MAST "format mismatch between agents".

2. **Explicit intent on every message (pragmatic layer).** ADOPT a typed *performative/intent*
   tag (request / inform / propose / verify / refuse) so intent is explicit, not inferred. Build
   implication: this is the FIPA-ACL `performative` carried into AutoFirm's envelope — kills
   FM-2.6 reasoning-action mismatch by making the *intended act* machine-checkable against the
   action taken.

3. **Semantic contracts negotiated before long interactions.** ADOPT a lightweight "contract
   handshake" (declare expected inputs/outputs/units) before a multi-message collaboration.
   Build implication: feeds the L2.A1/L2.ORG handshake; pairs with A3 handoff/resume.

## What AutoFirm should REJECT / DEFER

- **DEFER heavyweight formal ontology stacks (OWL/RDF reasoners).** Justified: AutoFirm's agents
  are LLM-based and internal; a heavy formal-semantics engine adds cost without evidence of
  payoff here. ADOPT a *minimal* versioned JSON vocabulary instead, and only escalate to formal
  ontology if evidence (L2 golden set) shows ambiguity failures persist.
- **REJECT treating syntactic protocols (MCP/A2A) as sufficient on their own** — this paper's
  central, corroborated point. The envelope must carry meaning, not just structure.

## Concrete build implication
Adds two required fields to the A2 message envelope — `intent` (typed performative) and
`vocabulary-version` (shared-ontology pointer) — and a pre-collaboration semantic handshake.
Drives a test: a message whose `intent` is contradicted by the sender's logged action is flagged
(FM-2.6 detector), and a message with an unknown `vocabulary-version` is refused (fail-closed).
