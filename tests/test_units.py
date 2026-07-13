"""Tests for unit handling and validation."""

import pytest

from urban_tree_geometry.calculations import dbh_cm_to_trunk_diameter_m
from urban_tree_geometry.models import TreeInput
from urban_tree_geometry.validation import validate_columns, validate_trees


def test_trunk_metres_is_dbh_over_100():
    assert dbh_cm_to_trunk_diameter_m(73.2) == pytest.approx(0.732)


def test_missing_required_columns():
    assert "perimeter_cm" in validate_columns(["tree_id", "common_name"])
    assert validate_columns(["tree_id", "perimeter_cm"]) == []


def test_negative_perimeter_is_error():
    report = validate_trees([TreeInput(tree_id="X", perimeter_cm=-5)])
    assert not report.ok


def test_large_perimeter_is_warning():
    report = validate_trees([TreeInput(tree_id="X", common_name="A", perimeter_cm=900)])
    assert report.ok
    assert report.n_warnings >= 1
