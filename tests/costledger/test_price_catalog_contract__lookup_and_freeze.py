"""Fail-closed tests for the versioned, SHA-pinned, frozen price catalog.

Proves: a lookup miss is a REFUSAL (never silent $0), the unit_divisor must be
positive (the per-1K/per-1M guard), the SHA pin and SemVer are validated, duplicate
keys are refused, and the catalog is frozen. Surface-aware lookup distinguishes the
SAME model on different surfaces (native vs bedrock).
"""

from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError

from autofirm.costledger.price_catalog_contract import (
    PriceCatalog,
    PriceCatalogEntry,
    PriceCatalogLookupError,
)
from autofirm.modelgateway.model_reference import ModelProvider, ModelRef
from tests.costledger.synthetic_cost_fixtures import make_prices

_SHA = "a" * 64
_MODEL = ModelRef(provider=ModelProvider.BEDROCK, model_name="claude-3")


def _entry(surface: str = "native", divisor: int = 1) -> PriceCatalogEntry:
    return PriceCatalogEntry(
        model=_MODEL,
        surface=surface,
        accessed_date=date(2026, 1, 1),
        prices=make_prices(),
        unit_divisor=divisor,
    )


def _catalog(*entries: PriceCatalogEntry, version: str = "1.0.0") -> PriceCatalog:
    return PriceCatalog(
        version=version,
        source_pin_sha=_SHA,
        effective_at=datetime(2026, 1, 1, tzinfo=UTC),
        entries=tuple(entries) or (_entry(),),
    )


def test_lookup_hit_returns_entry() -> None:
    cat = _catalog(_entry("native"))
    assert cat.lookup(_MODEL, "native").surface == "native"


def test_lookup_miss_fails_closed_not_zero() -> None:
    cat = _catalog(_entry("native"))
    with pytest.raises(PriceCatalogLookupError, match="no price for"):
        cat.lookup(_MODEL, "bedrock-batch")  # unknown surface


def test_lookup_is_surface_aware() -> None:
    native = _entry("native", divisor=1_000_000)
    bedrock = _entry("bedrock", divisor=1_000)
    cat = _catalog(native, bedrock)
    # same model, different surface -> different unit_divisor (the per-1K/per-1M trap).
    assert cat.lookup(_MODEL, "native").unit_divisor == 1_000_000
    assert cat.lookup(_MODEL, "bedrock").unit_divisor == 1_000


def test_unit_divisor_must_be_positive() -> None:
    with pytest.raises(ValidationError, match="must be > 0"):
        _entry(divisor=0)
    with pytest.raises(ValidationError, match="must be > 0"):
        _entry(divisor=-1)


def test_empty_catalog_refused() -> None:
    with pytest.raises(ValidationError, match="at least one entry"):
        PriceCatalog(
            version="1.0.0", source_pin_sha=_SHA,
            effective_at=datetime(2026, 1, 1, tzinfo=UTC), entries=(),
        )


def test_duplicate_keys_refused() -> None:
    with pytest.raises(ValidationError, match="duplicate"):
        _catalog(_entry("native"), _entry("native"))


@pytest.mark.parametrize("bad", ["1.0", "1", "1.0.0.0", "v1.0.0", "1.0.x", ""])
def test_version_must_be_semver(bad: str) -> None:
    with pytest.raises(ValidationError, match="SemVer"):
        _catalog(version=bad)


@pytest.mark.parametrize("bad_sha", ["xyz", "g" * 64, "a" * 10, ""])
def test_source_pin_sha_validated(bad_sha: str) -> None:
    with pytest.raises(ValidationError):
        PriceCatalog(
            version="1.0.0", source_pin_sha=bad_sha,
            effective_at=datetime(2026, 1, 1, tzinfo=UTC), entries=(_entry(),),
        )


def test_catalog_is_frozen() -> None:
    cat = _catalog()
    with pytest.raises(ValidationError):
        cat.version = "2.0.0"  # type: ignore[misc]
