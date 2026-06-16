"""Typed content spec for a FAST-structured Excel financial model.

What this does
--------------
Defines the immutable, validated input contract for
:mod:`autofirm.artifacts.excel_financial_model_builder`. A spec describes a
financial model the FAST way (``docs/research/B15-artifact-generation`` §2.1):
distinct **Inputs**, **Calculations** and **Outputs** sheets, where every driver
lives once on Inputs and calculations reference those drivers by cell rather than
embedding constants (ICAEW P14 — no embedded constants; P15 — calculate once,
then reference).

Why it exists / where it sits
-----------------------------
Decoupling the *spec* from both the *finance layer* and the *workbook writer*
keeps the builder general (CLAUDE.md §3.9): any source — an
``autofirm.finance`` model, a hand-built scenario, a test fixture — can produce a
spec, and the builder never reaches into finance internals. Validation lives here
so a malformed model is refused at construction (fail-closed — CLAUDE.md §5.6).

Security / compliance invariants upheld
---------------------------------------
``__post_init__`` validates structure eagerly and refuses anything malformed with
:class:`ArtifactSpecError` — empty titles, duplicate driver/line keys, unknown
formula references, or out-of-range periods — so no invalid model can be built.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal

from autofirm.artifacts.artifact_spec_validation_errors import ArtifactSpecError

__all__ = ["CalculationRow", "FinancialModelSpec", "InputDriver"]

# A driver/row key must be a safe identifier: it becomes a defined-name token and
# a human-readable label root, so we forbid anything that could break a formula or
# inject a leading-equals "formula" into a label cell (untrusted-input defence).
_KEY_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,62}$")


@dataclass(frozen=True, slots=True)
class InputDriver:
    """A single model driver living once on the Inputs sheet.

    Args:
        key: Stable identifier referenced by calculation formulas (e.g.
            ``"revenue_growth"``). Must match ``[A-Za-z][A-Za-z0-9_]*``.
        label: Human-readable row label shown on the Inputs sheet.
        values: One value per period, in period order. Length must equal the
            spec's period count. Stored as ``Decimal`` for exactness.
        number_format: Excel number format applied to the value cells.
    """

    key: str
    label: str
    values: tuple[Decimal, ...]
    number_format: str = "#,##0.00"


@dataclass(frozen=True, slots=True)
class CalculationRow:
    """A calculation row whose cells are Excel formulas referencing drivers.

    Args:
        key: Stable identifier for this row (unique across drivers and rows).
        label: Human-readable row label shown on the Calculations sheet.
        formula_template: An Excel formula with ``{key}`` placeholders that the
            builder resolves to the referenced cell for the *current period*
            (e.g. ``"={revenue} - {cogs}"``). Referenced keys must be drivers or
            earlier calculation rows; self-reference is forbidden.
        number_format: Excel number format applied to the formula cells.
    """

    key: str
    label: str
    formula_template: str
    number_format: str = "#,##0.00"


@dataclass(frozen=True, slots=True)
class FinancialModelSpec:
    """A complete, validated FAST-structured financial-model spec.

    Args:
        title: Model title (non-empty), used for the workbook and cover.
        periods: Ordered period labels (e.g. ``("FY24", "FY25")``); at least one.
        drivers: Input drivers, in display order; at least one.
        calculations: Calculation rows, in dependency/display order. May be empty
            (a pure-inputs model), though a real model has at least one.
        outputs: Keys (driver or calculation) surfaced on the Outputs sheet.

    Raises:
        ArtifactSpecError: If the model is structurally invalid (empty title or
            periods, bad keys, duplicate keys, wrong value-vector length, unknown
            or forward/self formula references, or unknown output keys).
    """

    title: str
    periods: tuple[str, ...]
    drivers: tuple[InputDriver, ...]
    calculations: tuple[CalculationRow, ...] = ()
    outputs: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        """Validate the whole model eagerly (fail-closed — CLAUDE.md §5.6)."""
        if not self.title.strip():  # fail-closed: an untitled model is refused
            raise ArtifactSpecError("financial model title must be non-empty")
        if not self.periods:  # fail-closed: a model needs at least one period
            raise ArtifactSpecError("financial model needs at least one period")
        if not self.drivers:  # fail-closed: a model with no inputs is meaningless
            raise ArtifactSpecError("financial model needs at least one input driver")

        n = len(self.periods)
        seen: dict[str, str] = {}
        self._validate_drivers(n, seen)
        self._validate_calculations(seen)
        self._validate_outputs(seen)

    def _validate_drivers(self, period_count: int, seen: dict[str, str]) -> None:
        for d in self.drivers:
            self._check_key(d.key, "driver")
            if not d.label.strip():
                raise ArtifactSpecError(f"driver {d.key!r} must have a non-empty label")
            if d.key in seen:  # fail-closed: duplicate keys make references ambiguous
                raise ArtifactSpecError(f"duplicate key {d.key!r}")
            # A short value vector would silently leave blank cells -> a wrong
            # model. Exact-length is required, not "at least".
            if len(d.values) != period_count:
                raise ArtifactSpecError(
                    f"driver {d.key!r} has {len(d.values)} values, expected {period_count}"
                )
            seen[d.key] = "driver"

    def _validate_calculations(self, seen: dict[str, str]) -> None:
        for c in self.calculations:
            self._check_key(c.key, "calculation")
            if not c.label.strip():
                raise ArtifactSpecError(f"calculation {c.key!r} must have a non-empty label")
            if c.key in seen:
                raise ArtifactSpecError(f"duplicate key {c.key!r}")
            refs = _referenced_keys(c.formula_template)
            if not refs:  # fail-closed: a "calculation" with no references is a constant
                raise ArtifactSpecError(
                    f"calculation {c.key!r} references no driver/row (embedded constant?)"
                )
            for ref in refs:
                if ref == c.key:  # fail-closed: self-reference is a circular formula
                    raise ArtifactSpecError(f"calculation {c.key!r} references itself")
                # Forward/unknown references break calculate-once-then-reference
                # (ICAEW P15): a row may only reference already-defined keys.
                if ref not in seen:
                    raise ArtifactSpecError(
                        f"calculation {c.key!r} references unknown/forward key {ref!r}"
                    )
            seen[c.key] = "calculation"

    def _validate_outputs(self, seen: dict[str, str]) -> None:
        for key in self.outputs:
            if key not in seen:  # fail-closed: cannot surface a key that does not exist
                raise ArtifactSpecError(f"output key {key!r} is not a driver or calculation")

    @staticmethod
    def _check_key(key: str, kind: str) -> None:
        if not _KEY_PATTERN.match(key):
            raise ArtifactSpecError(
                f"{kind} key {key!r} must match {_KEY_PATTERN.pattern} "
                "(letter-led identifier; defends against formula injection in labels)"
            )


def _referenced_keys(formula_template: str) -> tuple[str, ...]:
    """Return the ``{key}`` placeholder names referenced by a formula template.

    Order-preserving and de-duplicated, so validation and rendering agree on the
    exact set of references in a row.
    """
    out: list[str] = []
    for match in re.finditer(r"\{([A-Za-z][A-Za-z0-9_]*)\}", formula_template):
        ref = match.group(1)
        if ref not in out:
            out.append(ref)
    return tuple(out)
