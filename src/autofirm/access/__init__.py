"""Access-control foundation: credential broker + tenant-isolating RLS data layer.

What this package does
----------------------
This is AutoFirm's fail-closed, least-privilege access spine (research:
``docs/research/A8-integration-and-data-layer/SYNTHESIS.md`` L1.A8.2 / L1.A8.3).
It fences every agent/component's access to two resources:

* **secrets/credentials** — :mod:`autofirm.access.credential_broker` issues
  per-component, explicitly-scoped, short-TTL credentials from an env/secret-
  manager source (never a shared god-key, never a hard-coded secret); and
* **tenant data** — :mod:`autofirm.access.tenant_scoped_session_contract` plus
  :mod:`autofirm.access.in_memory_rls_backend` model Postgres row-level security
  so one tenant's rows are *unreachable* from another's, enforced in the data
  layer (not by an app-side WHERE clause that one missing line could leak).

A third module, :mod:`autofirm.access.workspace_data_boundary`, marks the
code-vs-sensitive-data boundary so secrets/finance/company data only ever live
in a gitignored ``.autofirm/`` root, never the code repo.

Why it exists / where it sits
-----------------------------
Lowest security layer of the platform: the org engine, comms bus, and audit log
all sit above it and rely on its guarantees. It depends only on
:mod:`autofirm.audit` (to record issuance/denials append-only) and the standard
library.

Security / compliance invariants upheld (CLAUDE.md §3.2, §5.6)
-------------------------------------------------------------
* **Fail closed everywhere:** a missing / ambiguous / expired credential, or any
  out-of-scope or cross-tenant access, is *refused*, never silently allowed.
* **Least privilege:** every credential is the narrowest scope that works; there
  is no shared god-key and no way to widen a credential after issue.
* **Secrets never logged:** the secret value lives only inside an opaque holder
  whose ``repr``/``str``/audit projection redact it; only non-secret metadata
  (component, scope, expiry) is ever emitted.
* **Tenant isolation in the data layer:** cross-tenant read/write is impossible
  through the session interface, matching the committed Postgres RLS policy.
"""

from __future__ import annotations
