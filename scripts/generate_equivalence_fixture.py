"""Generate the cross-language equivalence fixture.

Builds a deterministic set of tree inputs (every species at several perimeters,
plus edge cases: unknown species, taxonomic divergence, palm, extrapolation,
missing/invalid perimeter) and records the FULL Python pipeline output for each.
The TypeScript Vitest suite runs the same inputs through the TS pipeline and
asserts field-by-field equality (see web/test/equivalence.test.ts).

Output: tests/fixtures/equivalence_cases.json
"""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path

from urban_tree_geometry.models import TreeInput
from urban_tree_geometry.parameters import load_parameter_set_json
from urban_tree_geometry.pipeline import process_tree

ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT / "data" / "species_parameters.json"
OUT = ROOT / "tests" / "fixtures" / "equivalence_cases.json"

PERIMETERS = [30.0, 80.0, 150.0, 240.0, 330.0]


def _result_dict(res) -> dict:
    if is_dataclass(res):
        return asdict(res)
    if hasattr(res, "model_dump"):
        return res.model_dump()
    return dict(res.__dict__)


def build_cases(params) -> list[dict]:
    cases: list[dict] = []
    n = 0
    # every known species across a range of perimeters
    for sp in params.species.values():
        for p in PERIMETERS:
            n += 1
            cases.append(
                {
                    "tree_id": f"EQ-{n:04d}",
                    "common_name": sp.common_name,
                    "scientific_name": sp.scientific_name,
                    "perimeter_cm": p,
                }
            )
    # explicit edge cases
    edge = [
        ("EDGE-unknown", "ESPECIE NAO IDENTIFICADA", None, 120.0),
        ("EDGE-divergence", "ANGICO BRANCO", "Platypodium elegans", 330.0),
        ("EDGE-extrapolation", "ANGICO BRANCO", "Anadenanthera colubrina", 520.0),
        ("EDGE-tiny", next(iter(params.species.values())).common_name, None, 5.0),
        ("EDGE-suspicious", "ANGICO BRANCO", None, 900.0),
    ]
    for tid, cn, sn, p in edge:
        cases.append({"tree_id": tid, "common_name": cn, "scientific_name": sn, "perimeter_cm": p})
    return cases


def main() -> None:
    params = load_parameter_set_json(SHARED)
    inputs = build_cases(params)
    records = []
    for c in inputs:
        tree = TreeInput(
            tree_id=c["tree_id"],
            common_name=c["common_name"],
            scientific_name=c["scientific_name"],
            perimeter_cm=c["perimeter_cm"],
        )
        res = process_tree(tree, params)
        records.append({"input": c, "expected": _result_dict(res)})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(records)} equivalence cases -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
