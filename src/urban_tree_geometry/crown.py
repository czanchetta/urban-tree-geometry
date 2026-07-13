"""Heuristic crown and DIALux geometry layer.

IMPORTANT PROVENANCE NOTE
-------------------------
Nothing in this module comes from the source workbook. The workbook estimates
tree *height* only. The crown diameter, crown base height, crown depth,
projected area and DIALux X/Y/Z parameters computed here are an **engineering
heuristic**: operational parameters derived from general urban-forestry
literature and adjusted by crown architecture. They are:

* NOT species-specific published allometric coefficients;
* NOT calibrated with any local sample;
* NOT regression-tested against the workbook (there are no workbook values to
  test against).

Confidence for the crown layer is therefore reported no higher than the
species' own confidence, and palms are always treated as low confidence.
"""

from __future__ import annotations

import math

from .parameters import CrownGroup, PalmRule

# Crown-diameter sensitivity band settings (operational, not statistical).
CROWN_BAND_REL = 0.20
CROWN_BAND_MIN_M = 1.5


def crown_diameter_dbh_scaled(trunk_diameter_m: float, height_m: float, group: CrownGroup) -> float:
    """Heuristic crown diameter for non-palm trees.

    ``D_raw   = crown_dbh_factor * trunk_diameter_m``
    ``D_limit = crown_height_limit_fraction * height_m``
    ``D_crown = min(D_raw, D_limit)``

    The height-linked limit prevents implausibly wide crowns on stout, short
    trunks.
    """
    d_raw = group.crown_dbh_factor * trunk_diameter_m
    d_limit = group.crown_height_limit_fraction * height_m
    return max(0.0, min(d_raw, d_limit))


def crown_diameter_palm(height_m: float, rule: PalmRule) -> float:
    """Heuristic palm crown diameter, scaled from height and bounded.

    ``D_crown = clip(factor * H, min, max)``. Palms are low confidence; field
    measurement is recommended.
    """
    d = rule.palm_crown_height_factor * height_m
    return min(rule.palm_crown_max_m, max(rule.palm_crown_min_m, d))


def crown_base_and_depth(height_m: float, group: CrownGroup) -> tuple[float, float]:
    """Heuristic crown base height and crown depth from a depth fraction.

    ``crown_depth = crown_depth_fraction * H``
    ``crown_base_height = H - crown_depth``
    """
    depth = group.crown_depth_fraction * height_m
    base = height_m - depth
    return max(0.0, base), max(0.0, depth)


def crown_projected_area(crown_diameter_m: float) -> float:
    """Projected crown area assuming a circular projection.

    ``A = pi * D^2 / 4``. The circular assumption ignores real crown asymmetry
    and does not use two field-measured orthogonal axes; it serves pre-modelling
    only.
    """
    return math.pi * crown_diameter_m**2 / 4.0


def crown_band(crown_diameter_m: float) -> tuple[float, float]:
    """Operational crown-diameter sensitivity band.

    ``uncertainty = max(0.20 * D, 1.5 m)``; the lower bound is clipped at 0.
    This is a sensitivity scenario, not a confidence interval.
    """
    uncertainty = max(CROWN_BAND_REL * crown_diameter_m, CROWN_BAND_MIN_M)
    lower = max(0.0, crown_diameter_m - uncertainty)
    upper = crown_diameter_m + uncertainty
    return lower, upper
