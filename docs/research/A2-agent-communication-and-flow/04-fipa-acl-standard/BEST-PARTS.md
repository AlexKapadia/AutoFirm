# BEST-PARTS — FIPA-ACL Standard

## What AutoFirm should ADOPT and why

1. **The typed-envelope field set, modernized to JSON.** ADOPT FIPA-ACL's proven envelope as the
   skeleton for AutoFirm's inter-agent message: `performative/intent`, `sender`, `receiver`,
   `content`, `ontology`(vocabulary-version), `protocol`(flow-id), `conversation-id`,
   `reply-with`/`in-reply-to`(threading), `reply-by`(deadline for async/long-horizon). This is
   25 years of MAS field-tested design — do not reinvent it. Build implication: defines the
   concrete JSON schema for the A2 message contract; `conversation-id`+`in-reply-to` give
   threadable, auditable lineage (the "ACL lineage" in L1.A2.1).

2. **A bounded performative vocabulary.** ADOPT a small, closed set of typed acts (request,
   inform, propose, agree, refuse, cfp, not-understood, failure, confirm) rather than free text.
   Build implication: routing + verification become machine-checkable; `not-understood` and
   `failure` are explicit, fail-closed channels (mitigates silent FC2 errors from source 02).

3. **Feasibility precondition + rational effect as message-level contracts.** ADOPT the idea that
   each act carries preconditions and an intended effect. Build implication: a `request` must
   state the expected post-condition; the verification step (FC3) checks the rational effect was
   achieved — gives a precise, testable definition of "task done" (zero-numerical-error, S3.11).

4. **Standardized interaction protocols, esp. Contract Net (cfp/propose/accept).** ADOPT FIPA's
   reusable conversation templates as the named "workflows" agents follow. Build implication:
   AutoFirm's flow library = a small set of typed protocols (Request, Query, Contract-Net) with
   defined valid state transitions -> deterministic, inspectable flows (links to source 08).

## What AutoFirm should REJECT / DEFER

- **REJECT FIPA's heavyweight BDI logical semantics (full belief-desire-intention modal logic).**
  Justified: LLM agents do not have a formal BDI model; enforcing full FIPA SL semantics is
  impractical. ADOPT the *envelope, vocabulary, and protocol templates*; treat precondition/
  effect as practical contracts, not modal-logic proofs.
- **DEFER the older SL content language / KQML wire format** — use JSON-RPC/JSON-LD transports
  (source 01) instead; keep only the ACL *conceptual* model.

## Concrete build implication
FIPA-ACL is the canonical donor for AutoFirm's message *schema and conversation model*. The A2
contract = a JSON envelope with FIPA-derived fields + a closed performative set + named
interaction protocols, validated on every send (missing required field -> refuse). This is the
single most directly reusable prior-art for L1.A2.1, and pairs with the modern security/identity
layer from source 01.
