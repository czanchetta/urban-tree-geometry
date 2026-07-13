"""Validate the cross-language equivalence fixture from the Python side.

The fixture (tests/fixtures/equivalence_cases.json) stores the expected Python
output for each case; the TypeScript Vitest suite asserts the TS pipeline
matches it. This test guards the OTHER direction: that the committed fixture is
still exactly what the current Python pipeline produces (so a Python change
that would break TS equivalence fails here too, and regenerating the fixture is
required and visible in the diff).
"""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path

import pytest

from urban_tree_geometry.models import TreeInput
from urban_tree_geometry.parameters import load_parameter_set_json
from urban_tree_geometry.pipeline import process_tree

ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT / "data" / "species_parameters.json"
FIXTURE = ROOT / "tests" / "fixtures" / "equivalence_cases.json"


def _dict(res):
    if is_dataclass(res):
        return asdict(res)
    if hasattr(res, "model_dump"):
        return res.model_dump()
    return dict(res.__dict__)


def _cases():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_fixture_present_and_nontrivial():
    cases = _cases()
    assert len(cases) > 100


@pytest.mark.parametrize("case", _cases(), ids=lambda c: c["input"]["tree_id"])
def test_fixture_matches_current_python(case):
    params = load_parameter_set_json(SHARED)
    inp = case["input"]
    tree = TreeInput(
        tree_id=inp["tree_id"],
        common_name=inp["common_name"],
        scientific_name=inp["scientific_name"],
        perimeter_cm=inp["perimeter_cm"],
    )
    got = _dict(process_tree(tree, params))
    assert got == case["expected"], (
        f"Python output changed for {inp['tree_id']}; "
        "regenerate tests/fixtures/equivalence_cases.json and re-run TS tests."
    )
