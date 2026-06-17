"""Shared model-gateway value types: ``ModelRef``, ``UseCaseId``, ``ModelProvider``.

What this does
--------------
Defines the small, provider-agnostic value types the model gateway and the cost
ledger both depend on: :class:`ModelRef` (a frozen ``(provider, model_name)``
pair), the :class:`ModelProvider` closed enum of supported provider identities,
and the opaque :class:`UseCaseId` routing-key alias. This is *only* the shared
identity layer of ``data-contracts.md`` §7 — the request/response/selector shapes
(``model_invocation_contract.py``) are built later by W1 on top of these types.

Why it exists / where it sits
-----------------------------
``data-contracts.md`` §7 places ``ModelRef`` / ``UseCaseId`` / the closed enums in
``modelgateway/model_reference.py``, and §8 (the cost ledger) types ``served_by``
as ``ModelRef`` and ``use_case`` as ``UseCaseId``. Putting these here (not in the
ledger) keeps the gateway as the single owner of model identity and lets the
ledger price *any* provider's request without re-declaring identity — this file is
the lowest gateway layer; nothing here depends on a higher package.

Security / compliance invariants upheld
---------------------------------------
* **No silent default model (fail-closed, §7):** ``provider`` and ``model_name``
  are both required and must be non-empty; a model is never picked by default.
* **Provider-agnostic identity:** ``provider`` is a closed, lower-cased enum value,
  so a typo or unknown surface is refused rather than mis-priced.
* **Immutable:** ``ModelRef`` is frozen — a model identity is a value, not state.
"""

from __future__ import annotations

from enum import StrEnum
from typing import NewType

from pydantic import BaseModel, ConfigDict, field_validator

__all__ = [
    "ModelProvider",
    "ModelRef",
    "UseCaseId",
]

# The closed set of supported provider identities (research folders 01-06). Lower-
# cased, stable strings — pricing is keyed by (provider, model, surface), so an
# unknown provider must be refused, not defaulted (fail-closed). Adding a provider
# is a deliberate, reviewed change here, never an ad-hoc string elsewhere.
class ModelProvider(StrEnum):
    """The closed set of model providers AutoFirm can price and route (§7).

    Values are lower-cased, provider-agnostic identities (e.g. ``"anthropic"``).
    ``BEDROCK`` and ``OPENROUTER`` are distinct *surfaces* for hosted models — the
    same underlying model is priced differently by surface (research folder 04/07),
    so the surface is part of the provider identity here.
    """

    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"
    BEDROCK = "bedrock"
    OPENROUTER = "openrouter"


# Opaque, closed-set-extensible routing key (a NewType over str: static separation,
# zero runtime cost). The cost ledger attributes spend per use-case; the gateway
# routes on it. It is intentionally a free-form non-empty id (not an enum) so new
# use-cases need no code change — the selector policy decides if it must be known.
UseCaseId = NewType("UseCaseId", str)


class ModelRef(BaseModel):
    """A provider-agnostic ``(provider, model_name)`` model identity (§7).

    Frozen and fail-closed: both fields are required and non-empty, so a request or
    a ledger row can never reference an un-named model or a default picked silently.
    """

    model_config = ConfigDict(frozen=True)

    provider: ModelProvider  # closed enum — refuse an unknown/typo'd provider
    model_name: str  # REQUIRED, non-empty; never a silently-defaulted model (§7)

    @field_validator("model_name")
    @classmethod
    def _model_name_non_empty(cls, value: str) -> str:
        # fail-closed: an empty model name means "no model chosen" — refuse it
        # rather than letting a downstream default silently pick one (§7).
        if not value.strip():
            raise ValueError("model_name must be non-empty (no silent default model)")
        return value
