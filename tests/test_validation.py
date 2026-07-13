"""Tests for pipeline warnings and confidence handling."""

from urban_tree_geometry.models import TreeInput
from urban_tree_geometry.pipeline import process_tree


def test_unknown_species_warns(params):
    tree = TreeInput(tree_id="U1", common_name="NOT A REAL SPECIES", perimeter_cm=50)
    res = process_tree(tree, params)
    assert res.height_m is None
    assert res.confidence == "low"
    assert res.warnings


def test_taxonomic_divergence_warns(params):
    # UA07: common name ANGICO BRANCO but recorded scientific Platypodium elegans
    tree = TreeInput(
        tree_id="UA07",
        common_name="ANGICO BRANCO",
        scientific_name="Platypodium elegans",
        perimeter_cm=330,
    )
    res = process_tree(tree, params)
    assert any("diverges" in w for w in res.warnings)


def test_zero_perimeter_soft_fails(params):
    tree = TreeInput(tree_id="Z", common_name="IPÊ BRANCO", perimeter_cm=0)
    res = process_tree(tree, params)
    assert res.height_m is None
    assert res.confidence == "low"


def test_extrapolation_flag(params):
    # UA50: P=520 -> DBH ~165 cm, large extrapolation
    tree = TreeInput(
        tree_id="UA50",
        common_name="ANGICO BRANCO",
        scientific_name="Anadenanthera colubrina",
        perimeter_cm=520,
    )
    res = process_tree(tree, params)
    assert any("extrapolation" in w for w in res.warnings)
