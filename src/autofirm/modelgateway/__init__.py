"""AutoFirm model gateway — the provider-abstraction boundary (data-contracts.md §7).

This package is the single audited model-egress boundary (ADR-003). It is
provider-AGNOSTIC: the request/response/selector contracts name a *selection
policy*, never a hard-coded model string, and the only file that touches HTTP is
:mod:`~autofirm.modelgateway.openai_compatible_gateway_client`.

Layers (low to high):

* :mod:`~autofirm.modelgateway.model_reference` — :class:`ModelRef`
  ``(provider, model_name)``, the :class:`ModelProvider` enum, the
  :class:`UseCaseId` routing key.
* :mod:`~autofirm.modelgateway.kill_switch_epoch` — :class:`KillSwitchEpoch`, the
  fail-closed global egress halt token (C7).
* :mod:`~autofirm.modelgateway.model_invocation_contract` — :class:`Message`,
  :class:`ModelSelector`, :class:`ModelInvocationRequest` /
  :class:`ModelInvocationResponse` (§7).
* :mod:`~autofirm.modelgateway.model_selection_policy` — PURE deterministic
  selection of an in-policy call plan (optional learned-router hook proposes;
  the core disposes).
* :mod:`~autofirm.modelgateway.ensemble_quorum_reconciler` — PURE deterministic
  quorum reconciliation (Self-Consistency majority vote + priority tie-break).
* :mod:`~autofirm.modelgateway.model_egress_client_protocol` — the
  :class:`ModelGatewayClient` seam + a deterministic fake double.
* :mod:`~autofirm.modelgateway.openai_compatible_gateway_client` /
  :mod:`~autofirm.modelgateway.openai_response_parsing` — the ONLY HTTP path.
* :mod:`~autofirm.modelgateway.cli_gateway_env_injection` — PURE CLI gateway env
  builder enforcing the ADR-003 linchpin (CLI lane = Anthropic-only).

Gateway default (research-settled, B1): the recommended egress is a self-hosted,
OpenAI-compatible **LiteLLM** control plane (virtual keys, failover, open per-token
price map), with **OpenRouter** as a ``provider_reported`` cost source where used.
The code here is agnostic to any OpenAI-compatible gateway; the gateway URL comes
from env / secret-manager only (never a literal in the repo). See
``docs/architecture/ADR-003-model-egress-gateway.md`` and
``docs/research/B1-multi-model-egress/``.
"""

from __future__ import annotations

# NOTE: this package __init__ deliberately re-exports ONLY the identity + kill-switch
# value types. The request/response/selector contracts live in
# ``model_invocation_contract`` and are imported FROM THERE by callers — importing them
# here would pull in ``costledger`` (which itself imports ``modelgateway.model_reference``)
# and create an import cycle at package-init time. Keeping __init__ lean keeps the
# dependency graph acyclic (and the import-linter green).
from autofirm.modelgateway.kill_switch_epoch import KillSwitchEngaged, KillSwitchEpoch
from autofirm.modelgateway.model_reference import ModelProvider, ModelRef, UseCaseId

__all__ = [
    "KillSwitchEngaged",
    "KillSwitchEpoch",
    "ModelProvider",
    "ModelRef",
    "UseCaseId",
]
