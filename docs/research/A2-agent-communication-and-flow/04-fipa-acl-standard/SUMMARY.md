# SUMMARY — FIPA Agent Communication Language (ACL) Standard

## Full citation
- **Title (a):** FIPA ACL Message Structure Specification — Document **SC00061G**
- **Title (b):** FIPA Communicative Act Library Specification — Document **SC00037J**
- **Author/Org:** Foundation for Intelligent Physical Agents (FIPA); since 2005 an **IEEE**
  Computer Society standards body (FIPA founded 1996)
- **Year:** 2002 (standard status); foundations in Searle/Austin speech-act theory (1960s),
  extended by Winograd & Flores (1970s)
- **Venue/Publisher:** FIPA / IEEE standard
- **URL:** http://www.fipa.org/specs/fipa00061/SC00061G.html ·
  http://www.fipa.org/specs/fipa00037/SC00037J.html ·
  Performative list: https://jmvidal.cse.sc.edu/talks/agentcommunication/performatives.html ·
  Overview: https://en.wikipedia.org/wiki/Agent_Communications_Language

## Questions it informs
- **L1.A2.1** (typed message schema + ACL lineage — PRIMARY, the canonical prior art)
- L1.A2.3 (standardized communicative acts as a coordination contract — supporting)

## GRADE tier: High
Official IEEE/FIPA standard (primary, normative). Decades of MAS deployment (JADE, FIPA-OS).
No down-rate for the standard's own definitions. (Note: web-rendered overviews used to locate
fields are pointers; the normative source of record is SC00061G/SC00037J themselves.)

## Key claims (exact)

**Message structure (SC00061G).** A FIPA-ACL message is a typed envelope. Parameters:
- **performative** — the communicative act type. **Only `performative` is strictly mandatory.**
- **sender**, **receiver**, **reply-to**
- **content**
- **language**, **encoding**, **ontology** (content description)
- **protocol**, **conversation-id**, **reply-with**, **in-reply-to**, **reply-by**
  (conversation management)

**Communicative acts (SC00037J).** **22 performatives**: accept-proposal, agree, cancel, cfp,
confirm, disconfirm, failure, inform, inform-if, inform-ref, not-understood, propagate, propose,
proxy, query-if, query-ref, refuse, reject-proposal, request, request-when, request-whenever,
subscribe.

**Formal semantics.** Each performative has a **feasibility precondition** and a **rational
effect**. Example (inform): "an agent i is able to inform an agent j that some proposition p is
true only if i believes p." Grounded in **speech act theory** (Searle).

**Interaction protocols (standardized conversations).** FIPA defines reusable protocols, incl.
**FIPA-Request**, **FIPA-Query**, and the **FIPA Contract Net** (CFP -> propose -> accept/
reject-proposal). Relationship: FIPA-ACL is the IEEE-standardized successor lineage to **KQML**
(Knowledge Query and Manipulation Language); both define performatives and their meanings.

## Reproducibility note
The 22-performative count and the field list are normatively fixed in SC00037J / SC00061G and
re-verifiable there and in the JADE source (which implements FIPA-ACL). The inform feasibility/
rational-effect example is from the Communicative Act Library semantics.
