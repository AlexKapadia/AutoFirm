"""Capture real, populated PNG screenshots of the operator cockpit for the README.

This is an analysis/evidence script (NOT runtime code): it assembles the REAL cockpit
object graph via the on-main composition root, seeds it through the genuine domain
contracts (DynamicOrg.hire, AppendOnlyCostLedger.seal_new/append, the front-door
provenance trail, a KillSwitchEpoch, and real recorded cockpit events), then drives the
actual ``CockpitApp`` Textual TUI headlessly via Pilot and saves an SVG screenshot per
state. The SVGs are rasterised to PNG with cairosvg (analysis extra).

Data provenance: 100% real-shaped, public-data-only synthetic inputs flowing through the
SAME contracts the live platform uses (CLAUDE.md §3.12). No hand-drawn fake frames.
"""

from __future__ import annotations

import asyncio
import contextlib
import io
import re
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

import cairosvg
from rich.console import Console

from autofirm.cockpit.adapters.kill_switch_source import InMemoryKillSwitchSource
from autofirm.cockpit.composition.cockpit_application import CockpitApplication
from autofirm.cockpit.composition.cockpit_composer import assemble_cockpit
from autofirm.cockpit.composition.cockpit_config import CockpitConfig
from autofirm.cockpit.composition.in_memory_sources import CockpitSources
from autofirm.cockpit.eventlog.cockpit_event_contract import CockpitEventKind
from autofirm.cockpit.transport.cockpit_cli import main as cli_main
from autofirm.cockpit.tui.cockpit_app import CockpitApp
from autofirm.comms.delivery_outcome_types import DeliveryStatus
from autofirm.costledger.append_only_cost_ledger import AppendOnlyCostLedger
from autofirm.costledger.usage_cost_record import PriceVector, TokenUsage
from autofirm.foundation.money.money_amount import Money
from autofirm.frontdoor.front_door_provenance_trail import (
    FrontDoorProvenanceEntry,
    InMemoryFrontDoorProvenanceTrail,
)
from autofirm.frontdoor.routing_decision_contract import RoutingOutcome
from autofirm.modelgateway.kill_switch_epoch import KillSwitchEpoch
from autofirm.modelgateway.model_reference import ModelProvider, ModelRef, UseCaseId
from autofirm.org.org_identifiers import FrozenClock, RoleId, SequentialIdGenerator
from autofirm.org.org_lifecycle_engine import DynamicOrg
from autofirm.org.role_charter_contract import ROOT_AUTHOR, RoleCharter

_OUT = Path(__file__).resolve().parents[1] / "evidence" / "cockpit-screenshots"
_CLOCK = FrozenClock(datetime(2026, 6, 19, 9, 0, 0, tzinfo=UTC), step_seconds=1)
_INSTANT = datetime(2026, 6, 19, 9, 0, 0, tzinfo=UTC)
# Wide, tall terminal so every panel's rows are fully legible in the capture.
_SIZE = (200, 54)
_PRICES = PriceVector(
    currency="USD",
    input_price=Decimal("0.000003"),
    output_price=Decimal("0.000015"),
    cache_read_price=Decimal("0.0000003"),
    cache_write_price=Decimal("0.00000375"),
    reasoning_price=Decimal("0.000015"),
)
_USAGE = TokenUsage(input_tokens=1000, output_tokens=500)


def _charter(role_id: str, title: str, manager: str | None) -> RoleCharter:
    """A fully-specified charter (passes the completeness gate) for a real hire."""
    return RoleCharter(
        role_id=RoleId(role_id),
        title=title,
        responsibilities=("own its mandate",),
        ownership_scope="its remit",
        success_signal="judged on outcomes",
        owned_artifacts=frozenset(),
        manager_id=None if manager is None else RoleId(manager),
        authored_by=ROOT_AUTHOR if manager is None else RoleId(manager),
    )


def _real_org() -> DynamicOrg:
    """Found and grow a realistic multi-level company through the real lifecycle engine."""
    root = _charter("ceo", "Chief Executive", None)
    org = DynamicOrg.found(root, _CLOCK, SequentialIdGenerator())
    org = org.hire(_charter("coo", "Chief Operating Officer", "ceo"))
    org = org.hire(_charter("cto", "Chief Technology Officer", "ceo"))
    org = org.hire(_charter("cfo", "Chief Financial Officer", "ceo"))
    org = org.hire(_charter("research-lead", "Head of Research", "cto"))
    org = org.hire(_charter("eng-lead", "Head of Engineering", "cto"))
    org = org.hire(_charter("market-lead", "Head of Market Intel", "coo"))
    org = org.hire(_charter("fin-analyst", "Financial Analyst", "cfo"))
    return org


_HEALTHY_SPEND = [
    ("research-lead", "deep-research", ModelProvider.ANTHROPIC, "claude-opus-4", "182.40"),
    ("eng-lead", "code-synthesis", ModelProvider.ANTHROPIC, "claude-sonnet-4", "96.15"),
    ("market-lead", "market-sensing", ModelProvider.OPENAI, "gpt-4o", "64.80"),
    ("fin-analyst", "financial-modeling", ModelProvider.OPENAI, "gpt-4o-mini", "21.05"),
    ("research-lead", "literature-review", ModelProvider.GOOGLE, "gemini-1.5-pro", "48.60"),
]
# An extra burst of spend that pushes the run past 95% of the $500 budget -> CRIT_95 band.
_BREACH_SPEND = [
    *_HEALTHY_SPEND,
    ("eng-lead", "code-synthesis", ModelProvider.ANTHROPIC, "claude-opus-4", "71.20"),
    ("research-lead", "deep-research", ModelProvider.ANTHROPIC, "claude-opus-4", "9.85"),
]


def _real_ledger(rows: list[tuple[str, str, ModelProvider, str, str]]) -> AppendOnlyCostLedger:
    """Build a real, hash-chained cost ledger with spend across several models/roles."""
    ledger = AppendOnlyCostLedger()
    for i, (role_name, uc, provider, model, amount) in enumerate(rows):
        rec = ledger.seal_new(
            correlation_id=uuid.UUID(int=i),
            requesting_role_id=RoleId(role_name),
            use_case=UseCaseId(uc),
            served_by=ModelRef(provider=provider, model_name=model),
            usage=_USAGE,
            unit_prices=_PRICES,
            cost=Money(Decimal(amount), "USD"),
            cost_source="price_map_computed",
            price_catalog_version="1.0.0",
            recorded_at=_INSTANT,
        )
        ledger = ledger.append(rec)
    return ledger


def _real_trail() -> InMemoryFrontDoorProvenanceTrail:
    """Record real-shaped front-door requests, including a failed delivery (kept visible)."""
    trail = InMemoryFrontDoorProvenanceTrail()
    entries = [
        ("req-1001", "Jane Owner (Founder)", RoutingOutcome.ROUTED_TO_CAPABLE_ROLE,
         "cfo", "Chief Financial Officer", DeliveryStatus.DELIVERED, 2),
        ("req-1002", "Acme Board", RoutingOutcome.ROUTED_TO_CAPABLE_ROLE,
         "research-lead", "Head of Research", DeliveryStatus.DELIVERED, 9),
        ("req-1003", "Press Desk", RoutingOutcome.TRIAGED_NO_CAPABLE_ROLE,
         "coo", "Chief Operating Officer", DeliveryStatus.DEAD_LETTERED, 17),
        ("req-1004", "Jane Owner (Founder)", RoutingOutcome.ROUTED_TO_CAPABLE_ROLE,
         "market-lead", "Head of Market Intel", DeliveryStatus.DELIVERED, 28),
        ("req-1005", "Partner Channel", RoutingOutcome.TRIAGED_NO_PERMITTED_ROLE,
         "cto", "Chief Technology Officer", DeliveryStatus.DUPLICATE_SUPPRESSED, 41),
    ]
    for corr, who, outcome, rid, title, delivery, mins in entries:
        trail.record(
            FrontDoorProvenanceEntry(
                correlation_id=corr,
                requester_id=who,
                requester_display_name=who,
                routing_outcome=outcome,
                handler_role_id=rid,
                handler_role_title=title,
                routing_reason="matched capability terms",
                delivery_status=delivery,
                recorded_at=_INSTANT + timedelta(minutes=mins),
            )
        )
    return trail


def _build_app(*, breach: bool, log_path: Path) -> CockpitApplication:
    """Assemble the REAL cockpit application over populated sources (healthy vs budget-breach)."""
    epoch = KillSwitchEpoch(version=2)  # armed; egress permitted
    config = CockpitConfig(
        event_log_path=log_path,
        currency="USD",
        budget=Money(Decimal("500.00"), "USD"),  # makes a real budget band classify
        kill_switch_epoch=epoch,
    )
    sources = CockpitSources(
        front_door_trail=_real_trail(),
        org_state=_real_org().state,
        cost_ledger=_real_ledger(_BREACH_SPEND if breach else _HEALTHY_SPEND),
        kill_switch=InMemoryKillSwitchSource(epoch),
    )
    app = assemble_cockpit(config, clock=_CLOCK, sources=sources)
    # Record REAL cockpit audit events through the append-only writer (durable, hash-stamped).
    app.record_event(CockpitEventKind.ORG_CHANGED, "lifecycle", {"action": "hire", "role": "cfo"})
    app.record_event(CockpitEventKind.SPEND_RECORDED, "ledger", {"model": "claude-opus-4"})
    app.record_event(
        CockpitEventKind.FRONT_DOOR_REQUEST, "frontdoor", {"correlation": "req-1003"}
    )
    app.record_event(
        CockpitEventKind.KILL_SWITCH_OBSERVED, "modelgateway", {"epoch": "2"}
    )
    return app


# Textual's SVG embeds "Fira Code" which is absent on this box, so cairosvg substitutes a
# fallback that lacks heavy box-drawing glyphs -> missing-glyph boxes. Re-point the SVG at a
# Windows monospace font that DOES cover box-drawing (Consolas) before rasterising. This only
# changes the rasteriser's glyph source; it never alters the captured content.
_RENDER_FONT = "Consolas"


def _svg_to_png(svg_text: str, png_path: Path, *, width: int = 1600) -> None:
    """Rasterise an SVG string to PNG, re-pointing the font at one with box-drawing coverage."""
    fixed = re.sub(r'font-family:[^;}"]*', f"font-family: {_RENDER_FONT}, monospace", svg_text)
    cairosvg.svg2png(bytestring=fixed.encode("utf-8"), write_to=str(png_path), output_width=width)


async def _capture_tui(app: CockpitApplication, png_path: Path) -> None:
    """Drive the real CockpitApp via Pilot, export its SVG, and rasterise it to PNG."""
    tui = CockpitApp(app, refresh_interval=1000.0)  # quiet tick; capture the seeded refresh
    async with tui.run_test(size=_SIZE) as pilot:
        await pilot.pause()
        await pilot.pause()  # let the coalesced refresh paint every panel
        svg = tui.export_screenshot(title="AutoFirm Operator Cockpit")
    _svg_to_png(svg, png_path)


def _capture_cli(log_path: Path, png_path: Path) -> None:
    """Run the REAL cockpit CLI (version + replay) and rasterise its true stdout to PNG.

    The kill-switch / audit trail surface that the headless TUI export cannot paint (a
    docked-header Textual limitation) is shown here as genuine CLI output, captured from the
    real :func:`autofirm.cockpit.transport.cockpit_cli.main` against the seeded event log.
    """
    token = "demo-operator-token"  # nosec B105 - synthetic demo token for the evidence capture
    env = {"AUTOFIRM_COCKPIT_TOKEN": token}
    buf = io.StringIO()
    # Capture BOTH streams so the fail-closed auth refusal (which the CLI emits to stderr) is
    # visible alongside the successful read-only snapshots.
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        print("$ export AUTOFIRM_COCKPIT_TOKEN=********")
        print("$ python -m autofirm.cockpit version")
        cli_main(["version"])
        print()
        print("$ python -m autofirm.cockpit run --token ********")
        cli_main(["run", "--token", token, "--event-log", str(log_path)], env=env)
        print()
        print("$ python -m autofirm.cockpit replay --token ******** \\")
        print(f"      --event-log {log_path.name}")
        cli_main(["replay", "--token", token, "--event-log", str(log_path)], env=env)
        print()
        print("$ python -m autofirm.cockpit run --token 'wrong'   # fail-closed auth")
        cli_main(["run", "--token", "wrong"], env=env)
    console = Console(record=True, width=92, file=io.StringIO())
    console.print(buf.getvalue().rstrip("\n"), highlight=False, markup=False)
    _svg_to_png(console.export_svg(title="AutoFirm Operator Cockpit — CLI"), png_path, width=1400)


def main() -> None:
    """Capture the two TUI states and the CLI surface, writing PNGs under ``evidence/``."""
    _OUT.mkdir(parents=True, exist_ok=True)
    tui_shots = [
        ("01-cockpit-operating-healthy", False),
        ("02-cockpit-budget-breach-crit", True),
    ]
    with TemporaryDirectory() as tmp:
        for name, breach in tui_shots:
            log = Path(tmp) / f"{name}.ndjson"
            app = _build_app(breach=breach, log_path=log)
            png = _OUT / f"{name}.png"
            asyncio.run(_capture_tui(app, png))
            print(f"wrote {png}")
        # The CLI surface (real stdout) — carries the kill-switch line + audit replay + a
        # fail-closed auth refusal that the headless TUI export cannot render.
        cli_log = Path(tmp) / "cockpit-events.ndjson"
        _build_app(breach=False, log_path=cli_log)  # seed the real event log
        cli_png = _OUT / "03-cockpit-cli-replay-and-auth.png"
        _capture_cli(cli_log, cli_png)
        print(f"wrote {cli_png}")


if __name__ == "__main__":
    main()
