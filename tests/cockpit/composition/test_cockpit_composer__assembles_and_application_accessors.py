"""cockpit_composer + application: DI defaults/overrides, accessors, event round-trip."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from autofirm.cockpit.adapters.kill_switch_source import InMemoryKillSwitchSource
from autofirm.cockpit.composition.cockpit_application import CockpitApplication
from autofirm.cockpit.composition.cockpit_composer import assemble_cockpit
from autofirm.cockpit.composition.cockpit_config import CockpitConfig
from autofirm.cockpit.composition.in_memory_sources import CockpitSources
from autofirm.cockpit.composition.system_clock import SystemClock
from autofirm.cockpit.core.budget_threshold_state import BudgetBand
from autofirm.cockpit.eventlog.cockpit_event_contract import CockpitEventKind
from autofirm.comms.delivery_outcome_types import DeliveryStatus
from autofirm.costledger.append_only_cost_ledger import AppendOnlyCostLedger
from autofirm.foundation.money.money_amount import Money
from autofirm.frontdoor.front_door_provenance_trail import (
    FrontDoorProvenanceEntry,
    InMemoryFrontDoorProvenanceTrail,
)
from autofirm.frontdoor.routing_decision_contract import RoutingOutcome
from autofirm.modelgateway.kill_switch_epoch import KillSwitchEpoch
from autofirm.org.org_identifiers import FrozenClock, RoleId, SequentialIdGenerator
from autofirm.org.org_lifecycle_engine import DynamicOrg
from autofirm.org.role_charter_contract import ROOT_AUTHOR, RoleCharter
from tests.costledger.synthetic_cost_fixtures import (
    FIXED_INSTANT,
    corr,
    make_model,
    make_prices,
    make_usage,
    money,
    role,
    use_case,
)

_FIXED = datetime(2026, 6, 19, 9, 30, 0, tzinfo=UTC)


def _frozen() -> FrozenClock:
    return FrozenClock(_FIXED)  # step 0: now() is constant for exact-time assertions


def _charter(role_id: str, title: str, manager_id: str | None) -> RoleCharter:
    return RoleCharter(
        role_id=RoleId(role_id),
        title=title,
        responsibilities=("do work",),
        ownership_scope="scope",
        success_signal="judged",
        owned_artifacts=frozenset(),
        manager_id=None if manager_id is None else RoleId(manager_id),
        authored_by=ROOT_AUTHOR if manager_id is None else RoleId(manager_id),
    )


def _trail_with_one_entry() -> InMemoryFrontDoorProvenanceTrail:
    trail = InMemoryFrontDoorProvenanceTrail()
    trail.record(
        FrontDoorProvenanceEntry(
            correlation_id="corr-1",
            requester_id="req-1",
            requester_display_name="Asker One",
            routing_outcome=RoutingOutcome.ROUTED_TO_CAPABLE_ROLE,
            handler_role_id="role-1",
            handler_role_title="Handler One",
            routing_reason="matched: finance",
            delivery_status=DeliveryStatus.DELIVERED,
            recorded_at=_FIXED,
        )
    )
    return trail


def _ledger_with_spend(amount: str) -> AppendOnlyCostLedger:
    ledger = AppendOnlyCostLedger()
    rec = ledger.seal_new(
        correlation_id=corr(0),
        requesting_role_id=role("r0"),
        use_case=use_case("uc0"),
        served_by=make_model(),
        usage=make_usage(),
        unit_prices=make_prices(),
        cost=money(amount),
        cost_source="price_map_computed",
        price_catalog_version="1.0.0",
        recorded_at=FIXED_INSTANT,
    )
    return ledger.append(rec)


def _synthetic_sources(*, ledger_amount: str = "40.00", epoch_version: int = 5) -> CockpitSources:
    org = DynamicOrg.found(_charter("root", "CEO", None), _frozen(), SequentialIdGenerator())
    org = org.hire(_charter("m1", "VP", "root"))
    return CockpitSources(
        front_door_trail=_trail_with_one_entry(),
        org_state=org.state,
        cost_ledger=_ledger_with_spend(ledger_amount),
        kill_switch=InMemoryKillSwitchSource(KillSwitchEpoch(version=epoch_version)),
    )


def _config(tmp_path: Path, *, budget: Money | None = None) -> CockpitConfig:
    return CockpitConfig(
        event_log_path=tmp_path / "events.ndjson", currency="USD", budget=budget
    )


# --------------------------- composer DI --------------------------- #


def test_assemble_with_defaults_uses_system_clock_and_in_memory_sources(tmp_path: Path) -> None:
    app = assemble_cockpit(_config(tmp_path))
    assert isinstance(app, CockpitApplication)
    assert isinstance(app.clock, SystemClock)
    # default in-memory org is the single synthetic root
    assert app.org_snapshot().total_role_count == 1
    assert app.front_door_activity().entries == ()
    assert app.kill_switch_epoch().version == 0


def test_assemble_with_injected_clock_and_sources(tmp_path: Path) -> None:
    clock = _frozen()
    sources = _synthetic_sources()
    app = assemble_cockpit(_config(tmp_path), clock=clock, sources=sources)
    assert app.clock is clock
    assert app.org_state is sources.org_state
    assert app.cost_ledger is sources.cost_ledger


# --------------------------- accessors --------------------------- #


def test_org_snapshot_reflects_injected_org(tmp_path: Path) -> None:
    app = assemble_cockpit(_config(tmp_path), clock=_frozen(), sources=_synthetic_sources())
    snap = app.org_snapshot()
    assert snap.root_role_id == "root"
    assert snap.total_role_count == 2


def test_front_door_activity_reflects_injected_trail(tmp_path: Path) -> None:
    app = assemble_cockpit(_config(tmp_path), clock=_frozen(), sources=_synthetic_sources())
    activity = app.front_door_activity()
    assert [e.correlation_id for e in activity.entries] == ["corr-1"]
    assert activity.entries[0].handler_role == "Handler One"


def test_kill_switch_epoch_is_observed_not_flipped(tmp_path: Path) -> None:
    app = assemble_cockpit(
        _config(tmp_path), clock=_frozen(), sources=_synthetic_sources(epoch_version=9)
    )
    assert app.kill_switch_epoch().version == 9
    assert app.kill_switch_epoch().tripped is False


def test_spend_snapshot_band_none_when_no_budget(tmp_path: Path) -> None:
    app = assemble_cockpit(_config(tmp_path), clock=_frozen(), sources=_synthetic_sources())
    spend = app.spend_snapshot()
    assert spend.grand_total == money("40.00")
    assert spend.budget is None
    assert spend.band is None
    assert spend.ledger_verified is True


def test_spend_snapshot_band_classified_when_budget_set(tmp_path: Path) -> None:
    budget = Money(Decimal("50.00"), "USD")  # 40/50 == 80% -> WARN_80
    app = assemble_cockpit(
        _config(tmp_path, budget=budget), clock=_frozen(), sources=_synthetic_sources()
    )
    spend = app.spend_snapshot()
    assert spend.band is BudgetBand.WARN_80
    assert spend.budget == budget


def test_currency_is_threaded_into_spend(tmp_path: Path) -> None:
    cfg = CockpitConfig(event_log_path=tmp_path / "e.ndjson", currency="JPY")
    ledger = AppendOnlyCostLedger()
    rec = ledger.seal_new(
        correlation_id=corr(0),
        requesting_role_id=role("r0"),
        use_case=use_case("uc0"),
        served_by=make_model(),
        usage=make_usage(),
        unit_prices=make_prices(currency="JPY"),
        cost=Money(Decimal("500"), "JPY"),
        cost_source="price_map_computed",
        price_catalog_version="1.0.0",
        recorded_at=FIXED_INSTANT,
    )
    sources = _synthetic_sources()
    sources = CockpitSources(
        front_door_trail=sources.front_door_trail,
        org_state=sources.org_state,
        cost_ledger=ledger.append(rec),
        kill_switch=sources.kill_switch,
    )
    app = assemble_cockpit(cfg, clock=_frozen(), sources=sources)
    assert app.spend_snapshot().grand_total == Money(Decimal("500"), "JPY")


# --------------------------- record + replay round-trip --------------------------- #


def test_record_event_stamps_injected_clock_and_round_trips(tmp_path: Path) -> None:
    clock = _frozen()
    app = assemble_cockpit(_config(tmp_path), clock=clock, sources=_synthetic_sources())
    recorded = app.record_event(CockpitEventKind.ORG_CHANGED, "unit-test", {"k": "v"})
    assert recorded.recorded_at == _FIXED  # stamped with the INJECTED clock exactly
    assert recorded.seq == 0
    replayed = app.recorded_events()
    assert replayed == (recorded,)  # exact round-trip through the on-disk log


def test_record_event_assigns_monotonic_seq(tmp_path: Path) -> None:
    app = assemble_cockpit(_config(tmp_path), clock=_frozen(), sources=_synthetic_sources())
    first = app.record_event(CockpitEventKind.SPEND_RECORDED, "src", {})
    second = app.record_event(CockpitEventKind.SPEND_RECORDED, "src", {})
    assert (first.seq, second.seq) == (0, 1)
    assert tuple(e.seq for e in app.recorded_events()) == (0, 1)


def test_recorded_events_empty_when_no_log(tmp_path: Path) -> None:
    app = assemble_cockpit(_config(tmp_path), clock=_frozen(), sources=_synthetic_sources())
    assert app.recorded_events() == ()  # missing log == empty history (reads event_log_path)


def test_recorded_events_uses_replay_source_path_override(tmp_path: Path) -> None:
    # write events into the LIVE log via one app...
    live = tmp_path / "live.ndjson"
    writer_cfg = CockpitConfig(event_log_path=live, currency="USD")
    writer_app = assemble_cockpit(writer_cfg, clock=_frozen(), sources=_synthetic_sources())
    writer_app.record_event(CockpitEventKind.KILL_SWITCH_OBSERVED, "writer", {})

    # ...then a second app whose event_log_path is empty but replay_source_path points at it.
    reader_cfg = CockpitConfig(
        event_log_path=tmp_path / "empty.ndjson",
        currency="USD",
        replay_source_path=live,
    )
    reader_app = assemble_cockpit(reader_cfg, clock=_frozen(), sources=_synthetic_sources())
    events = reader_app.recorded_events()
    assert len(events) == 1
    assert events[0].source == "writer"  # read from the replay-source override, not event_log
