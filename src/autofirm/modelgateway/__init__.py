"""AutoFirm model gateway — provider-agnostic model identity (shared value types).

This package owns model identity and (later, W1) the request/response/selector
shapes of ``data-contracts.md`` §7. Only the shared identity layer is built here
now — the cost ledger (W5) depends on it; W1 builds the invocation contracts on
top later.

* :mod:`~autofirm.modelgateway.model_reference` — :class:`ModelRef`
  ``(provider, model_name)``, the :class:`ModelProvider` closed enum, and the
  :class:`UseCaseId` routing-key alias.
"""

from __future__ import annotations

from autofirm.modelgateway.model_reference import ModelProvider, ModelRef, UseCaseId

__all__ = [
    "ModelProvider",
    "ModelRef",
    "UseCaseId",
]
