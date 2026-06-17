"""The versioned, frozen price snapshot — never trust a live price.

What this does
--------------
Defines :class:`PriceCatalogEntry` (one immutable price row keyed by ``(model,
surface, accessed_date)`` carrying an explicit ``unit_divisor`` and the per-token
:class:`~autofirm.costledger.usage_cost_record.PriceVector`) and :class:`PriceCatalog`
(the SemVer-versioned, SHA-pinned, frozen collection). Lookup is fail-closed: a miss
is a refusal, never a silent ``$0``. The ``unit_divisor`` makes the per-1K-vs-per-1M
Bedrock trap (a 1000x error) impossible — every entry states its own scale.

Why it exists / where it sits
-----------------------------
``data-contracts.md`` §8 requires the price snapshot to be versioned, frozen, and
pinned by the upstream catalog commit SHA (the LiteLLM catalog has NO versioning —
research folder 05 — so we pin a SHA and snapshot-and-freeze). It sits above the
``PriceVector`` value type and is consumed by the pure cost computation, which never
sees a live price. An update is a deliberate, version-bumped, reconciled change — NOT
an in-place edit (no graveyard, §3.8).

Security / compliance invariants upheld
---------------------------------------
* **Snapshot-and-freeze (folder 05, §8):** the catalog is frozen; prices are pinned
  by ``(version, source_pin_sha, effective_at)`` and never read live for a recorded
  request.
* **Explicit unit scale (folder 04):** every entry carries a positive ``unit_divisor``
  so a per-1K row and a per-1M row are both priced correctly — no 1000x error.
* **Lookup miss fails closed (§8):** an unknown ``(model, surface)`` is refused, never
  priced at ``$0`` (which would silently under-bill).
* **SHA-pinned provenance:** ``source_pin_sha`` is a 64-char hex digest of the pinned
  upstream snapshot, refused if malformed — the price's origin is auditable.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

from autofirm.costledger.usage_cost_record import PriceVector
from autofirm.modelgateway.model_reference import ModelRef

__all__ = [
    "PriceCatalog",
    "PriceCatalogEntry",
    "PriceCatalogLookupError",
    "PriceSurface",
]

# A 64-char lowercase-hex commit SHA / digest — the pinned upstream catalog snapshot
# (folder 05). Stored as a validated string so a malformed pin is refused at build.
HexSha = Annotated[
    str, StringConstraints(pattern=r"^[0-9a-f]{40,64}$", min_length=40, max_length=64)
]

# The surface a model was served through (folder 04/07): the SAME model is priced
# differently by surface (native vs Bedrock vs batch), so the price key is
# (model, surface), never model alone. A free-form non-empty string keeps it
# extensible without a code change per new tier.
PriceSurface = Annotated[str, StringConstraints(min_length=1)]

# SemVer is exactly three dot-separated numeric parts (MAJOR.MINOR.PATCH).
_SEMVER_PART_COUNT = 3


class PriceCatalogLookupError(Exception):
    """Raised when a ``(model, surface)`` is not in the snapshot (fail-closed miss)."""


class PriceCatalogEntry(BaseModel):
    """One immutable price row: prices for a ``(model, surface)`` on an accessed date.

    The :class:`PriceVector` holds per-``unit_divisor`` rates; ``unit_divisor`` is the
    number of tokens one quoted rate covers (1 for per-token, 1000 for per-1K,
    1_000_000 for per-1M) — folder 04. The cost computation divides by it exactly, so
    a per-1K and a per-1M row both yield the correct cost with no 1000x error.
    """

    model_config = ConfigDict(frozen=True)

    model: ModelRef  # which model this price applies to
    surface: PriceSurface  # the serving surface (native / bedrock / batch / ...)
    accessed_date: date  # the date this price was observed/snapshotted (provenance)
    prices: PriceVector  # the per-unit_divisor rates (Decimal, frozen)
    unit_divisor: int  # tokens per quoted rate: 1 / 1000 / 1_000_000 (folder 04)

    @field_validator("unit_divisor")
    @classmethod
    def _unit_divisor_positive(cls, value: int) -> int:
        # fail-closed: a zero/negative divisor would divide-by-zero or invert the
        # sign — refuse it. This is the guard that makes the per-1K/per-1M trap safe.
        if value <= 0:
            raise ValueError("unit_divisor must be > 0 (tokens per quoted rate)")
        return value


class PriceCatalog(BaseModel):
    """The SemVer-versioned, SHA-pinned, frozen price snapshot (data-contracts.md §8).

    Keyed internally by ``(provider, model_name, surface)`` so a lookup is exact and
    surface-aware. An update is a deliberate, version-bumped replacement (a new frozen
    catalog), never an in-place edit (§3.8). A lookup miss is a refusal (fail-closed).
    """

    model_config = ConfigDict(frozen=True)

    version: str  # SemVer; a price-shape-breaking change is a MAJOR bump (§8)
    source_pin_sha: HexSha  # the pinned upstream catalog commit SHA (folder 05)
    effective_at: datetime  # when this snapshot became authoritative
    entries: tuple[PriceCatalogEntry, ...]  # the frozen price rows (refused if empty)

    @field_validator("version")
    @classmethod
    def _version_is_semver(cls, value: str) -> str:
        # fail-closed: the version must be a real SemVer MAJOR.MINOR.PATCH so a row's
        # `price_catalog_version` is reconcilable and orderable (§8). Refuse garbage.
        parts = value.split(".")
        if len(parts) != _SEMVER_PART_COUNT or not all(p.isdigit() for p in parts):
            raise ValueError(f"version must be SemVer MAJOR.MINOR.PATCH, got {value!r}")
        return value

    @field_validator("entries")
    @classmethod
    def _entries_non_empty_and_unique(
        cls, value: tuple[PriceCatalogEntry, ...]
    ) -> tuple[PriceCatalogEntry, ...]:
        # fail-closed: an empty catalog can only ever return misses (§8); and a
        # duplicate (model, surface) key would make lookup ambiguous — refuse both.
        if not value:
            raise ValueError("price catalog must contain at least one entry")
        keys = [(e.model.provider.value, e.model.model_name, e.surface) for e in value]
        if len(set(keys)) != len(keys):
            raise ValueError("price catalog has duplicate (provider, model, surface) keys")
        return value

    def lookup(self, model: ModelRef, surface: str) -> PriceCatalogEntry:
        """Return the frozen price entry for ``(model, surface)`` or fail closed.

        Args:
            model: The model whose price to fetch.
            surface: The serving surface (native / bedrock / batch / ...).

        Returns:
            The matching :class:`PriceCatalogEntry`.

        Raises:
            PriceCatalogLookupError: If no entry matches (fail-closed: a miss is a
                refusal, never a silent ``$0`` price — §8).
        """
        for entry in self.entries:
            if (
                entry.model.provider == model.provider
                and entry.model.model_name == model.model_name
                and entry.surface == surface
            ):
                return entry
        # fail-closed: pricing an unknown model/surface at $0 would silently under-
        # bill and break reconciliation — refuse so the gap is visible and audited.
        raise PriceCatalogLookupError(
            f"no price for ({model.provider.value}, {model.model_name}, {surface}) "
            f"in catalog {self.version}"
        )
