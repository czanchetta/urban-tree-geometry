"""Tests for the palm-specific crown rule and pipeline handling."""

import pytest

from urban_tree_geometry.crown import crown_diameter_palm
from urban_tree_geometry.models import TreeInput
from urban_tree_geometry.parameters import PalmRule
from urban_tree_geometry.pipeline import process_tree

RULE = PalmRule()


def test_palm_uses_bounds():
    assert crown_diameter_palm(1.0, RULE) == pytest.approx(RULE.palm_crown_min_m)
    assert crown_diameter_palm(100.0, RULE) == pytest.approx(RULE.palm_crown_max_m)


def test_palm_pipeline_low_confidence(params):
    tree = TreeInput(
        tree_id="P1",
        common_name="PALMEIRA JERIVÁ",
        scientific_name="Syagrus romanzoffiana",
        perimeter_cm=55,
    )
    res = process_tree(tree, params)
    assert res.confidence == "low"
    assert any("palm" in w.lower() for w in res.warnings)
    assert res.crown_diameter_x_m == res.crown_diameter_y_m
