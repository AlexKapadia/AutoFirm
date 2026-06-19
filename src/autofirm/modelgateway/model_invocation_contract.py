"""The model-gateway request/response/selector shapes (data-contracts.md §7).

What this does
--------------
Defines the four frozen, fail-closed contracts of ``data-contracts.md`` §7 on top
of the shared identity layer (:mod:`model_reference`):

* :class:`Message` — a role-tagged chat turn whose ``trust_tag`` marks content as
  ``trusted`` or ``untrusted`` for injection defence (CaMeL/dual-LLM; C5).
* :class:`ModelSelector` — a SELECTION POLICY (``pinned`` / ``preferred_with_failover``
  / ``ensemble_quorum``) over an ordered, non-empty tuple of candidate models — the
  core of "many models per use-case" (ADR-003 §3), never a single hard-coded string.
* :class:`ModelInvocationRequest` — one fully-validated call: who is spending, the
  use-case routing key, the selector policy, the (trust-tagged) messages, a bounded
  output budget, a deterministic temperature default, a secret-free credential
  handle, and the kill-switch epoch the call is authorised under.
* :class:`ModelInvocationResponse` — what the gateway returns: the echoed correlation
  id, which model actually served, the (untrusted-by-default) output message, the
  provider-RETURNED token usage, a closed-set finish reason, and an injected clock.

Why it exists / where it sits
-----------------------------
``data-contracts.md`` §7 places these shapes here, on top of ``ModelRef`` /
``UseCaseId`` (this package) and reusing ``TokenUsage`` from the cost ledger and
``ScopedCredentialReference`` from the substrate — never re-declaring identity,
usage, or credential metadata. This file is the *boundary*: every field is validated
at construction so nothing downstream (the policy, the HTTP client) re-validates.

Security / compliance invariants upheld (CLAUDE.md §5.6)
-------------------------------------------------------
* **Injection defence (C5):** every :class:`Message` is trust-tagged; untrusted
  content is never promoted to trusted, and the model's output defaults to
  ``untrusted`` so a downstream consumer cannot mistake it for a trusted instruction.
* **Bounded spend (§5.6):** ``max_output_tokens`` is a ``PositiveInt`` — an
  unbounded/zero budget is refused, so a single call cannot run away.
* **Deterministic by default (§3.11):** ``temperature`` defaults to ``Decimal("0")``
  and is range-checked ``[0, 2]``; ``served_at`` is an injected clock, never wall-time.
* **Secret-free request (§5.6):** the request carries a
  :class:`ScopedCredentialReference` only; the virtual key is resolved at point of use.
* **Selector well-formedness (fail-closed):** ``pinned`` ⇒ exactly one candidate;
  ``ensemble_quorum`` ⇒ a quorum in ``[1, len(candidates)]``; an empty candidate set,
  an unknown strategy, or a quorum on a non-quorum strategy are all refused.
* **Correlation integrity:** the response echoes the request's ``correlation_id``;
  ``served_by`` candidacy is enforced by the gateway client (it has the request).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, PositiveInt, field_validator, model_validator

from autofirm.costledger.usage_cost_record import TokenUsage
from autofirm.modelgateway.kill_switch_epoch import KillSwitchEpoch
from autofirm.modelgateway.model_reference import ModelRef, UseCaseId
from autofirm.org.org_identifiers import RoleId
from autofirm.substrate.scoped_credential_reference import ScopedCredentialReference

__all__ = [
    "Message",
    "ModelInvocationRequest",
    "ModelInvocationResponse",
    "ModelSelector",
    "SelectionStrategy",
    "TrustTag",
]

# Closed selection-policy set (ADR-003 §3): a request names a POLICY, never a model
# string. `pinned` = one exact model; `preferred_with_failover` = try candidates in
# order until one answers; `ensemble_quorum` = call several and reconcile by quorum.
SelectionStrategy = Literal["pinned", "preferred_with_failover", "ensemble_quorum"]

# Injection-defence tag (C5/C5-prime I-row): untrusted content (tool output, fetched
# documents, prior model output) must never become trusted control flow. Default-
# deny — when origin is unknown a Message MUST be constructed "untrusted".
TrustTag = Literal["trusted", "untrusted"]


class Message(BaseModel):
    """One role-tagged chat turn carrying an injection trust tag (§7, C5).

    ``content`` may be empty but never ``None`` (pydantic refuses ``None`` for a
    required ``str``); ``role`` and ``trust_tag`` are closed sets so an unknown role
    or an untagged message is refused at the boundary.
    """

    model_config = ConfigDict(frozen=True)

    role: Literal["system", "user", "assistant", "tool"]  # closed set; refuse unknown
    content: str  # REQUIRED; empty allowed, None refused (no silently-absent content)
    trust_tag: TrustTag  # REQUIRED injection tag; default-deny is the CALLER's job


class ModelSelector(BaseModel):
    """A selection POLICY over an ordered, non-empty tuple of candidate models (§7).

    Fail-closed well-formedness: the candidate tuple is never empty; ``pinned``
    forces exactly one candidate; ``ensemble_quorum`` requires a ``quorum`` in
    ``[1, len(candidates)]`` and the other strategies forbid one. This is "many
    models per use-case" expressed as data, not as scattered call-site branching.
    """

    model_config = ConfigDict(frozen=True)

    strategy: SelectionStrategy  # closed set; an unknown strategy is refused
    candidates: tuple[ModelRef, ...]  # ordered, len>=1; the allowed model set
    quorum: PositiveInt | None = None  # REQUIRED iff ensemble_quorum; else MUST be None

    @field_validator("candidates")
    @classmethod
    def _candidates_non_empty(cls, value: tuple[ModelRef, ...]) -> tuple[ModelRef, ...]:
        # fail-closed: an empty candidate set means "no model to call" — refuse it
        # rather than let a downstream default silently pick a model.
        if not value:
            raise ValueError("selector must list at least one candidate model")
        return value

    @model_validator(mode="after")
    def _strategy_shape_consistent(self) -> ModelSelector:
        # fail-closed: a pinned policy that lists >1 model is ambiguous about which
        # one is pinned — refuse it so "pinned" always means exactly one model.
        if self.strategy == "pinned" and len(self.candidates) != 1:
            raise ValueError("pinned strategy requires exactly one candidate")
        if self.strategy == "ensemble_quorum":
            # fail-closed: a quorum policy with no quorum (or a quorum larger than
            # the candidate set) can never be satisfied — refuse the unsatisfiable
            # policy rather than silently degrade it to a single answer.
            if self.quorum is None:
                raise ValueError("ensemble_quorum strategy requires a quorum")
            if self.quorum > len(self.candidates):
                raise ValueError("quorum must be <= number of candidates")
        elif self.quorum is not None:
            # fail-closed: a quorum on a non-quorum strategy is a contradictory spec
            # — refuse it so a stray quorum can never change a pinned/failover call.
            raise ValueError("quorum is only valid for the ensemble_quorum strategy")
        return self


class ModelInvocationRequest(BaseModel):
    """One fully-validated model call (§7) — the gateway's single input shape.

    Frozen and fail-closed: the bounded output budget, the deterministic temperature
    default, the secret-free credential handle, and the kill-switch epoch are all
    validated here so the policy and the HTTP client operate on a known-good request.
    """

    model_config = ConfigDict(frozen=True)

    correlation_id: UUID  # joins audit + cost ledger; refuse if absent (pydantic)
    requesting_role_id: RoleId  # who is spending — bound from the virtual key, not self-declared
    use_case: UseCaseId  # closed-set-extensible routing key (any non-empty id accepted here)
    model_selector: ModelSelector  # the selection policy (pinned/failover/quorum)
    messages: tuple[Message, ...]  # ordered turns; len>=1, each trust-tagged (§7)
    max_output_tokens: PositiveInt  # bounded spend — no unbounded/zero output (fail-closed)
    temperature: Decimal = Decimal("0")  # deterministic default; range-checked [0, 2]
    credential_ref: ScopedCredentialReference  # secret-FREE handle; key resolved at use
    kill_switch_token: KillSwitchEpoch  # the epoch this call is authorised under (C7)

    @field_validator("requesting_role_id")
    @classmethod
    def _role_non_empty(cls, value: RoleId) -> RoleId:
        # fail-closed: spend must be attributable to a real role (no orphan spend).
        if not str(value).strip():
            raise ValueError("requesting_role_id must be non-empty")
        return value

    @field_validator("use_case")
    @classmethod
    def _use_case_non_empty(cls, value: UseCaseId) -> UseCaseId:
        # fail-closed: an empty routing key cannot attribute cost — refuse it.
        if not str(value).strip():
            raise ValueError("use_case must be non-empty")
        return value

    @field_validator("messages")
    @classmethod
    def _messages_non_empty(cls, value: tuple[Message, ...]) -> tuple[Message, ...]:
        # fail-closed: a call with no messages has nothing to send — refuse it.
        if not value:
            raise ValueError("request must carry at least one message")
        return value

    @field_validator("temperature")
    @classmethod
    def _temperature_in_range(cls, value: Decimal) -> Decimal:
        # fail-closed: a temperature outside [0, 2] is not a meaningful sampling
        # setting — refuse it rather than let a provider clamp it silently.
        if value < Decimal("0") or value > Decimal("2"):
            raise ValueError("temperature must be within [0, 2]")
        return value


class ModelInvocationResponse(BaseModel):
    """What the gateway returns for one call (§7) — provider usage echoed verbatim.

    ``served_by`` records which candidate actually answered (failover-aware); the
    gateway client enforces it is one of the request's candidates. ``output`` is
    ``untrusted`` by default (the gateway never auto-trusts a model's words), and
    ``usage`` is the provider's own count carried through unchanged (the cost ledger's
    single source of truth — never a local tokenizer estimate).
    """

    model_config = ConfigDict(frozen=True)

    correlation_id: UUID  # echoes the request exactly; the client refuses a mismatch
    served_by: ModelRef  # which model/provider actually answered (failover-aware)
    output: Message  # the model's reply; trust_tag is "untrusted" by default (C5)
    usage: TokenUsage  # provider-RETURNED counts, echoed verbatim (never locally guessed)
    finish_reason: Literal["stop", "length", "tool_use", "content_filter", "error"]
    served_at: datetime  # injected clock (deterministic-testable), never wall-clock
