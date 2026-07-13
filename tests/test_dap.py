"""Tests for perimeter -> DBH conversion."""

import math

import pytest

from urban_tree_geometry.calculations import (
    UnitError,
    dbh_cm_to_trunk_diameter_m,
    dbh_from_perimeter,
)


def test_dbh_100cm():
    assert dbh_from_perimeter(100.0) == pytest.approx(100.0 / math.pi)


def test_dbh_positive_known():
    # P = pi * 50 -> DBH exactly 50
    assert dbh_from_perimeter(math.pi * 50) == pytest.approx(50.0)


def test_perimeter_zero_raises():
    with pytest.raises(UnitError):
        dbh_from_perimeter(0.0)


def test_perimeter_negative_raises():
    with pytest.raises(UnitError):
        dbh_from_perimeter(-10.0)


def test_perimeter_missing_raises():
    with pytest.raises(UnitError):
        dbh_from_perimeter(None)  # type: ignore[arg-type]


def test_trunk_diameter_metres():
    assert dbh_cm_to_trunk_diameter_m(50.0) == pytest.approx(0.5)
