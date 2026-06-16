"""Client design & product capability — the governed, testable contract layer.

What this package is
--------------------
AutoFirm is headless; it builds and operates UIs and products for the CLIENT
companies it runs. This package is **not a UI** — it is the deterministic,
fail-closed CONTRACT layer that models and governs that design/product work so
the platform can hold every client build to the institution-grade bar of
CLAUDE.md §2 (CDO / Head-of-Design), §3.14 and §4.9.

It encodes three things as checkable contracts:

* the per-project **design brief** AutoFirm's design org authors for a client
  (design tokens + component inventory + state coverage + quality bar), with the
  "every state / not vibe-coded" rules turned into construction-time gates
  (:mod:`~autofirm.design_product.design_brief_contract`,
  :mod:`~autofirm.design_product.design_tokens_contract`,
  :mod:`~autofirm.design_product.ui_state_coverage_contract`);
* the audited **design/product workflow** brief -> build -> visual-review ->
  done, as a deterministic state machine with the §4.9 generator/evaluator split
  and a gapless trail
  (:mod:`~autofirm.design_product.design_workflow_state_machine`,
  :mod:`~autofirm.design_product.design_workflow_trail`);
* the typed **UI Definition-of-Done gate** that returns DONE only when every
  §4.9 quality gate passes, fail-closed
  (:mod:`~autofirm.design_product.ui_definition_of_done_gate`).

Where it sits
-------------
A thin governance layer over the platform primitives: design/product roles are
ordinary dynamic :mod:`autofirm.org` roles, the design workflow is an audited
flow that mirrors :mod:`autofirm.flow`, and design-review requests route through
:mod:`autofirm.frontdoor`. This package adds the design-specific contracts and
gates on top; it never reaches into those modules' internals.

Security / compliance posture
-----------------------------
Everything here is **deterministic and fail-closed**: an incomplete brief, an
illegal workflow transition, or a Definition-of-Done with any missing/failing
gate is **refused** with an explicit reason — never silently accepted. Nothing
is industry-specific; the contracts apply to any client company or product.
"""
