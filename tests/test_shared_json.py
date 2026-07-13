"""The shared JSON parameter document must load and reproduce the workbook.

This guards the single-source-of-truth contract: the same file the TypeScript
frontend consumes must drive the Python height core to the identical 62/62
workbook reproduction.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from urban_tree_geometry.models import TreeInput
from urban_tree_geometry.parameters import load_parameter_set, load_parameter_set_json
from urban_tree_geometry.pipeline import process_tree

SHARED = Path(__file__).resolve().parents[1] / "data" / "species_parameters.json"
FIXTURE = Path(__file__).parent / "fixtures" / "workbook_reference.csv"


def test_shared_json_exists():
    assert SHARED.is_file(), "shared species_parameters.json must be present"


def test_json_and_csv_agree_on_species():
    js = load_parameter_set_json(SHARED)
    csv_set = load_parameter_set(
        species_path=SHARED.parent / "parameters" / "species_parameters.csv",
        crown_path=SHARED.parent / "parameters" / "crown_parameters.csv",
        palm_path=SHARED.parent / "parameters" / "palm_rule.csv",
    )
    assert set(js.species) == set(csv_set.species)
    for key, sp in js.species.items():
        other = csv_set.species[key]
        assert sp.height_asymptote_m == other.height_asymptote_m
        assert sp.height_shape_k_cm == other.height_shape_k_cm
        assert sp.crown_group == other.crown_group


def test_default_loader_uses_shared_json():
    # With no explicit paths, the default loader should pick the shared JSON.
    params = load_parameter_set()
    assert len(params.species) == len(load_parameter_set_json(SHARED).species)


def _reference():
    with FIXTURE.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


@pytest.mark.parametrize("row", _reference(), ids=lambda r: r["tree_id"])
def test_json_reproduces_workbook(row):
    params = load_parameter_set_json(SHARED)
    tree = TreeInput(
        tree_id=row["tree_id"],
        common_name=row["common_name"],
        scientific_name=row["scientific_name"],
        perimeter_cm=float(row["perimeter_cm"]),
    )
    res = process_tree(tree, params)
    assert res.height_m == pytest.approx(float(row["height_m"]), abs=1e-9)
