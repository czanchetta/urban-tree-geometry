"""Tests for the heuristic crown layer."""

import math

import pytest

from urban_tree_geometry.crown import (
    crown_band,
    crown_base_and_depth,
    crown_diameter_dbh_scaled,
    crown_projected_area,
)
from urban_tree_geometry.parameters import CrownGroup

BROAD = CrownGroup("broad", 25.0, 1.00, 0.80, "dbh_scaled")
NARROW = CrownGroup("narrow", 14.0, 0.50, 0.60, "dbh_scaled")


def test_crown_not_negative():
    assert crown_diameter_dbh_scaled(0.5, 10.0, BROAD) >= 0


def test_crown_respects_height_limit():
    # very stout trunk, short tree -> height limit dominates
    d = crown_diameter_dbh_scaled(2.0, 5.0, BROAD)  # raw=50, limit=5
    assert d == pytest.approx(5.0)


def test_narrow_factor_less_than_broad():
    assert NARROW.crown_dbh_factor < BROAD.crown_dbh_factor


def test_projected_area_circular():
    assert crown_projected_area(4.0) == pytest.approx(math.pi * 16 / 4)


def test_base_and_depth_sum_to_height():
    base, depth = crown_base_and_depth(10.0, BROAD)
    assert base + depth == pytest.approx(10.0)


def test_crown_band_min_floor():
    lo, hi = crown_band(2.0)  # 20% = 0.4 -> floor 1.5
    assert hi - 2.0 == pytest.approx(1.5)
    assert lo == pytest.approx(0.5)
