"""Regression: the height core must reproduce the source workbook exactly.

The fixture ``workbook_reference.csv`` is the 62-row formula-free output of the
source workbook. Height, DBH (1 dp) and the operational bands must match with
zero tolerance beyond floating-point rounding of the DBH display value.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from urban_tree_geometry.models import TreeInput
from urban_tree_geometry.parameters import load_parameter_set
from urban_tree_geometry.pipeline import process_tree

FIXTURE = Path(__file__).parent / "fixtures" / "workbook_reference.csv"

# Rounding/float tolerances (explicit).
DBH_TOL = 0.05  # workbook DBH shown to 1 decimal place
H_TOL = 1e-9  # heights are on a 0.5 m grid; must match exactly


def _load_reference():
    with FIXTURE.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


@pytest.fixture(scope="module")
def params():
    return load_parameter_set()


@pytest.mark.parametrize("row", _load_reference(), ids=lambda r: r["tree_id"])
def test_row_matches_workbook(row, params):
    tree = TreeInput(
        tree_id=row["tree_id"],
        common_name=row["common_name"],
        scientific_name=row["scientific_name"],
        perimeter_cm=float(row["perimeter_cm"]),
    )
    res = process_tree(tree, params)
    assert res.dbh_cm == pytest.approx(float(row["dap_cm"]), abs=DBH_TOL)
    assert res.height_m == pytest.approx(float(row["height_m"]), abs=H_TOL)
    assert res.height_min_m == pytest.approx(float(row["height_min_m"]), abs=H_TOL)
    assert res.height_max_m == pytest.approx(float(row["height_max_m"]), abs=H_TOL)


def test_all_rows_reproduced(params):
    """Aggregate check: every row reproduces height exactly."""
    ref = _load_reference()
    mismatches = []
    for row in ref:
        tree = TreeInput(
            tree_id=row["tree_id"],
            common_name=row["common_name"],
            scientific_name=row["scientific_name"],
            perimeter_cm=float(row["perimeter_cm"]),
        )
        res = process_tree(tree, params)
        if abs(res.height_m - float(row["height_m"])) > H_TOL:
            mismatches.append(row["tree_id"])
    assert not mismatches, f"height mismatches: {mismatches}"
