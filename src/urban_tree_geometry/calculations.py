"""Faithful reproduction of the source-workbook height model.

Every formula here mirrors the attached workbook cell-for-cell and is
regression-tested against its 62-row formula-free output. Rounding conventions
are reproduced exactly:

* DAP:    ``DBH = P / pi`` (cm), no rounding in the core value.
* Height: ``H = 1.30 + (H_inf - 1.30) * (1 - exp(-DBH / k))`` rounded to the
  nearest 0.5 m.
* Bands:  a purely *operational* +-20% sensitivity range applied to the
  ALREADY-ROUNDED height, with a 2 m lower floor, each rounded to 0.5 m.

The band is explicitly a sensitivity scenario, NOT a statistical confidence
interval (see ``docs/methodology.md``).
"""

from __future__ import annotations

import math

# Reference breast height used by the model (m). The FAO convention measures
# DBH over bark at 1.30 m above ground.
BREAST_HEIGHT_M = 1.30

# Operational band settings (reproduce the workbook).
BAND_LOWER_FACTOR = 0.80
BAND_UPPER_FACTOR = 1.20
BAND_LOWER_FLOOR_M = 2.0
ROUND_STEP_M = 0.5


class UnitError(ValueError):
    """Raised when an input value is physically impossible for its unit."""


def round_to_step(value: float, step: float = ROUND_STEP_M) -> float:
    """Round ``value`` to the nearest multiple of ``step`` (banker-free).

    Uses round-half-up to match spreadsheet ``ROUND(x*2,0)/2`` behaviour.
    """
    if step <= 0:
        raise ValueError("step must be positive")
    scaled = value / step
    # round-half-away-from-zero, matching Excel ROUND
    rounded = math.floor(scaled + 0.5) if scaled >= 0 else math.ceil(scaled - 0.5)
    return rounded * step


def dbh_from_perimeter(perimeter_cm: float | None) -> float:
    """Convert trunk perimeter (cm) to DBH (cm) assuming a circular section.

    ``DBH = P / pi``. Raises :class:`UnitError` for non-positive perimeter;
    callers that prefer a soft failure should catch it and record a warning.
    """
    if perimeter_cm is None:
        raise UnitError("perimeter is missing")
    if perimeter_cm <= 0:
        raise UnitError(f"perimeter must be positive, got {perimeter_cm!r} cm")
    return perimeter_cm / math.pi


def dbh_cm_to_trunk_diameter_m(dbh_cm: float) -> float:
    """Convert DBH in centimetres to trunk diameter in metres (``/100``)."""
    return dbh_cm / 100.0


def height_from_dbh(dbh_cm: float, height_asymptote_m: float, shape_k_cm: float) -> float:
    """Asymptotic (monomolecular) height model, rounded to 0.5 m.

    ``H = 1.30 + (H_inf - 1.30) * (1 - exp(-DBH / k))``.

    Args:
        dbh_cm: diameter at breast height (cm).
        height_asymptote_m: adopted asymptotic height H_inf (m); must exceed 1.30.
        shape_k_cm: adopted shape parameter k (cm); must be positive.

    Raises:
        ValueError: if ``height_asymptote_m <= 1.30`` or ``shape_k_cm <= 0``.
    """
    if height_asymptote_m <= BREAST_HEIGHT_M:
        raise ValueError(
            f"height_asymptote_m must exceed {BREAST_HEIGHT_M} m, got {height_asymptote_m}"
        )
    if shape_k_cm <= 0:
        raise ValueError(f"shape_k_cm must be positive, got {shape_k_cm}")
    if dbh_cm <= 0:
        raise UnitError(f"dbh must be positive, got {dbh_cm}")
    raw = BREAST_HEIGHT_M + (height_asymptote_m - BREAST_HEIGHT_M) * (
        1.0 - math.exp(-dbh_cm / shape_k_cm)
    )
    return round_to_step(raw)


def height_band(height_m: float) -> tuple[float, float]:
    """Operational +-20% sensitivity band around a (rounded) height.

    Reproduces the workbook: the lower bound is floored at 2 m, and both bounds
    are rounded to 0.5 m. This is a sensitivity scenario, not a confidence
    interval.
    """
    lower = round_to_step(max(BAND_LOWER_FLOOR_M, height_m * BAND_LOWER_FACTOR))
    upper = round_to_step(height_m * BAND_UPPER_FACTOR)
    return lower, upper
