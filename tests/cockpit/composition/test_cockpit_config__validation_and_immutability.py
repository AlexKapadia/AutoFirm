"""cockpit_config: fail-closed currency validation + frozen/slots immutability; no secret field."""

from __future__ import annotations

import dataclasses
import typing
from decimal import Decimal
from pathlib import Path

import pytest

from autofirm.cockpit.composition.cockpit_config import CockpitConfig
from autofirm.foundation.money.money_amount import Money
from autofirm.modelgateway.kill_switch_epoch import KillSwitchEpoch


def _path() -> Path:
    return Path("events.ndjson")


def test_valid_config_holds_its_fields() -> None:
    budget = Money(Decimal("100.00"), "USD")
    epoch = KillSwitchEpoch(version=2, tripped=True)
    cfg = CockpitConfig(
        event_log_path=_path(),
        currency="USD",
        budget=budget,
        replay_source_path=Path("archive.ndjson"),
        kill_switch_epoch=epoch,
    )
    assert cfg.event_log_path == _path()
    assert cfg.currency == "USD"
    assert cfg.budget == budget
    assert cfg.replay_source_path == Path("archive.ndjson")
    assert cfg.kill_switch_epoch is epoch


def test_defaults_are_none() -> None:
    cfg = CockpitConfig(event_log_path=_path(), currency="EUR")
    assert cfg.budget is None
    assert cfg.replay_source_path is None
    assert cfg.kill_switch_epoch is None


@pytest.mark.parametrize("blank", ["", "   ", "\t", "\n"])
def test_blank_currency_is_refused(blank: str) -> None:
    with pytest.raises(ValueError, match="non-empty ISO-4217"):
        CockpitConfig(event_log_path=_path(), currency=blank)


@pytest.mark.parametrize("bad", ["usd", "Usd", "uSD"])
def test_non_uppercase_currency_is_refused(bad: str) -> None:
    with pytest.raises(ValueError, match="upper-case ISO-4217"):
        CockpitConfig(event_log_path=_path(), currency=bad)


def test_uppercase_currency_is_accepted() -> None:
    assert CockpitConfig(event_log_path=_path(), currency="JPY").currency == "JPY"


def test_config_is_frozen() -> None:
    cfg = CockpitConfig(event_log_path=_path(), currency="USD")
    with pytest.raises(dataclasses.FrozenInstanceError):
        cfg.currency = "EUR"  # type: ignore[misc]


def test_config_has_no_dict_slots_enforced() -> None:
    cfg = CockpitConfig(event_log_path=_path(), currency="USD")
    assert not hasattr(cfg, "__dict__")  # slots: no smuggling extra attributes


def test_config_has_no_token_field() -> None:
    # a secret must never be a config field (it could be logged / repr'd / audited).
    field_names = {f.name for f in dataclasses.fields(CockpitConfig)}
    assert not any("token" in name or "secret" in name for name in field_names)


# --------------------------- exact optional-union annotations --------------------------- #
# `get_type_hints` EVALUATES the (stringised, via `from __future__ import annotations`) field
# annotations. The real `X | None` evaluates fine; a `X & None` mutant raises TypeError inside
# the eval, so this kills the `|`->`&` annotation mutants (they are NOT equivalent under eval).


def test_optional_field_annotations_evaluate_to_unions_with_none() -> None:
    hints = typing.get_type_hints(CockpitConfig)
    assert hints["budget"] == (Money | None)
    assert hints["replay_source_path"] == (Path | None)
    assert hints["kill_switch_epoch"] == (KillSwitchEpoch | None)


# ------------------ exact validation messages (kills substring mutants) ------------------ #


def test_blank_currency_message_is_exact() -> None:
    with pytest.raises(ValueError) as exc:
        CockpitConfig(event_log_path=_path(), currency="   ")
    assert str(exc.value) == "currency must be a non-empty ISO-4217 code"


def test_non_uppercase_currency_message_is_exact() -> None:
    with pytest.raises(ValueError) as exc:
        CockpitConfig(event_log_path=_path(), currency="usd")
    assert str(exc.value) == "currency must be an upper-case ISO-4217 code, got 'usd'"
