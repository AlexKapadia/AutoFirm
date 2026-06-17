"""Operate-the-company flow: exercise every major feature and assert it works.

Once a company is built (:mod:`.company_build_flow`), this drives the platform to
OPERATE it the way a human owner would, asserting each feature's REAL output is
correct/sensible (not merely that it didn't raise):

* **Finance** — articulate the three statements from a public-style ledger (assert
  the balance sheet balances and the cash-flow ties) and value the firm by DCF.
* **Decisions** — an explainable pricing recommendation (margin floor never
  breached; the driver names the binding constraint) and a runway scenario.
* **Market intelligence** — sense a public signal into a structured insight, then
  a green-light go/no-go verdict whose rationale matches the verdict exactly.
* **Front door** — route the owner's question to the right team (or fail-closed to
  triage), delivered over the real bus.
* **Artifacts + document store** — generate a REAL investor-ready ``.docx`` into
  the isolated workspace and file it in the company's document store.
* **Heartbeat** — register a beat and tick the injected clock so it fires once.
* **Flow** — move a work item through the org (created -> done) with a full trail.

Plus a per-company FAIL-CLOSED edge case (a malformed pricing input is refused),
proving the platform rejects bad input rather than emitting a divergent answer.
"""

from __future__ import annotations

from autofirm.document_store.librarian_filing_service import LibrarianFilingService
from autofirm.e2e.isolated_company_workspace import IsolatedCompanyWorkspace
from autofirm.e2e.operate_decisions_checks import (
    check_fail_closed_guard,
    check_pricing_decision,
    check_runway_decision,
)
from autofirm.e2e.operate_finance_checks import (
    check_finance_statements,
    check_finance_valuation,
)
from autofirm.e2e.operate_platform_checks import (
    check_artifact_and_filing,
    check_flow_handoff,
    check_front_door_routing,
    check_green_light_gate,
    check_heartbeat_tick,
    check_market_intel_sweep,
)
from autofirm.e2e.public_company_scenarios import PublicCompanyScenario
from autofirm.e2e.scenario_result_contract import FeatureCheck
from autofirm.org.org_lifecycle_engine import DynamicOrg


def operate_company(
    scenario: PublicCompanyScenario,
    org: DynamicOrg,
    librarian: LibrarianFilingService,
    workspace: IsolatedCompanyWorkspace,
) -> tuple[FeatureCheck, ...]:
    """Operate ``scenario`` end-to-end; return every feature's verdict.

    Args:
        scenario: The public-data company being operated.
        org: The built, live org (used for front-door routing over the real org).
        librarian: The company's document store (the generated artifact is filed).
        workspace: The isolated workspace (the artifact is written under its root).

    Returns:
        One :class:`FeatureCheck` per exercised operate-phase feature, in a stable
        order, each carrying the real-shaped evidence its assertion verified.
    """
    return (
        check_finance_statements(scenario),
        check_finance_valuation(scenario),
        check_pricing_decision(scenario),
        check_runway_decision(scenario),
        check_market_intel_sweep(scenario),
        check_green_light_gate(scenario),
        check_front_door_routing(scenario, org),
        check_artifact_and_filing(scenario, librarian, workspace),
        check_heartbeat_tick(scenario),
        check_flow_handoff(scenario, org),
        check_fail_closed_guard(scenario),
    )


__all__ = ["operate_company"]
