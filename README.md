# urban-tree-geometry

[![tests](https://github.com/czanchetta/urban-tree-geometry/actions/workflows/tests.yml/badge.svg)](https://github.com/czanchetta/urban-tree-geometry/actions/workflows/tests.yml)
[![lint](https://github.com/czanchetta/urban-tree-geometry/actions/workflows/lint.yml/badge.svg)](https://github.com/czanchetta/urban-tree-geometry/actions/workflows/lint.yml)
![python](https://img.shields.io/badge/python-3.11%2B-blue)
![license](https://img.shields.io/badge/license-MIT-green)

**Preliminary estimation of tree height, crown diameter and 3D geometry
parameters for outdoor lighting models (DIALux) from tree-inventory data.**

*Read this in [Português (pt-BR)](README.pt-BR.md).*

> **Scope disclaimer.** This is a *preliminary* tool for estimating tree
> geometry parameters for outdoor-lighting **pre-modelling** when a full field
> dendrometric survey is not available. It is **not** a calibrated regional
> allometric model, a forest inventory, an arboricultural report, or a substitute
> for field measurement with a hypsometer, clinometer or topographic survey. It
> must not be used for tree-removal, compensation, stability or legal decisions.

---

## Problem

Lighting designers modelling outdoor scenes in tools such as DIALux need
approximate tree geometry (height, crown size, trunk) to assess obstruction and
appearance. Full dendrometric field data is often unavailable at the design
stage — frequently the only records are species and **trunk perimeter**.

## Solution

Given a minimal inventory (id, species, trunk perimeter), this package produces
preliminary geometry parameters, clearly separating four levels of trust:

- **measured** — what the project supplied (perimeter);
- **derived** — mathematically computed (DAP, height);
- **adopted** — per-species literature parameters (H∞, k);
- **heuristic** — engineering assumptions for crown/DIALux geometry.

The **height core** faithfully reproduces a source workbook and is
regression-tested against all 62 of its rows. The **crown/DIALux layer** is a
clearly labelled heuristic and is *not* claimed to be workbook-derived or
validated.

![Calculation flow](images/workflow.svg)

## Two implementations, one source of truth

GitHub Pages serves static files only — it cannot run Python server-side. The
project therefore ships **two implementations**:

1. **Python package** (`src/urban_tree_geometry/`) — the scientific reference:
   full XLSX/CSV reading, validation, testing and report generation.
2. **TypeScript frontend** (`web/`) — a static, browser-only calculator
   (Vite + TypeScript, no framework, no backend) published to GitHub Pages.

Both load the **same** parameter file, [`data/species_parameters.json`](data/species_parameters.json)
— parameters are never hand-duplicated. A cross-language **equivalence test**
runs a shared reference dataset (`tests/fixtures/equivalence_cases.json`)
through both implementations and asserts field-by-field agreement (DAP, height,
crown X/Y/Z, base, depth, area, bands, warnings, confidence). The Pages
deployment is gated on the Python tests, the TypeScript/equivalence tests, and
both site builds all passing. See [`docs/dual_implementation.md`](docs/dual_implementation.md).

## Installation

```bash
git clone https://github.com/czanchetta/urban-tree-geometry.git
cd urban-tree-geometry
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,viz]"
```

## Usage (CLI)

```bash
# estimate geometry from an inventory table
urban-tree-geometry calculate \
    --input data/raw/sample_tree_inventory.csv \
    --output outputs/tree_geometry.csv \
    --excel outputs/tree_geometry.xlsx

# validate an inventory without computing
urban-tree-geometry validate --input data/raw/sample_tree_inventory.csv

# inspect an XLSX workbook's structure
urban-tree-geometry inspect-workbook --input some_workbook.xlsx

# convert a results CSV to a formula-free XLSX (with a DIALux sheet)
urban-tree-geometry export-excel --input outputs/tree_geometry.csv --output outputs/tree_geometry.xlsx

# DIALux 3D export — parametric schematic .3ds (open format, one per tree)
urban-tree-geometry export-3ds --input data/raw/sample_tree_inventory.csv --outdir outputs/3ds/

# DIALux 3D export — resize your own .dxobj template (proprietary mesh, git-ignored)
urban-tree-geometry export-dxobj --input data/raw/sample_tree_inventory.csv \
    --template MyTree.dxobj --outdir outputs/dxobj/
```

## Data format

Input CSV (minimum): `tree_id, common_name, scientific_name, perimeter_cm`
(Portuguese aliases such as `ua`, `especie`, `nome_cientifico`, `perimetro_cm`
are also accepted).

## Equations

- **DAP:** `DBH = P / π` (cm); trunk diameter `= DBH / 100` (m)
- **Height:** `H = 1.30 + (H∞ − 1.30)·[1 − exp(−DBH / k)]`, rounded to 0.5 m
- **Height band:** `H_min = max(2, 0.8·H)`, `H_max = 1.2·H` (operational, not a CI)
- **Crown (heuristic):** `D = min(factor·trunk_m, limit·H)`; palms `D = clip(0.35·H, 3.5, 6.0)`
- **Crown area:** `A = π·D²/4` (circular)

## Processing flow

`inventory → DAP → height (+band) → crown/DIALux geometry → result table + DIALux table`

## Example result

| tree_id | common_name | total_height_z_m | crown_diameter_x_m | trunk_diameter_m | crown_base_height_m | confidence |
|---|---|---|---|---|---|---|
| TREE-001 | ANGICO BRANCO | 22.5 | 22.5 | 1.0504 | 4.5 | medium |
| TREE-002 | COPAÍBA | 7.0 | 3.71 | 0.1687 | 2.1 | medium |
| TREE-003 | JACARANDÁ MIMOSO | 14.5 | 14.5 | 0.5984 | 2.9 | medium |
| TREE-004 | AMENDOIM DO CAMPO | 14.0 | 14.0 | 0.5761 | 2.8 | medium |
| TREE-005 | IPÊ BRANCO | 10.5 | 8.4 | 0.4011 | 3.15 | medium |

Full outputs: [`outputs/`](outputs/) and the formula-free DIALux table in
[`data/processed/dialux_tree_parameters.csv`](data/processed/dialux_tree_parameters.csv).

## Conceptual DIALux integration

`total_height → Z`, `crown_diameter_x/y → X, Y`, plus trunk diameter, crown base
height and crown depth for objects that model the trunk and crown separately.
See [`docs/dialux_workflow.md`](docs/dialux_workflow.md). This project does **not**
assert any automatic DIALux import format.

![Tree geometry parameters](images/geometry.svg)

## Documentation

- [Methodology](docs/methodology.md) · [Assumptions](docs/assumptions.md) ·
  [Limitations](docs/limitations.md)
- [Data dictionary](docs/data_dictionary.md) · [References](docs/references.md) ·
  [DIALux workflow](docs/dialux_workflow.md)
- [Audit & validation report](docs/validation_report.md)

## Limitations

Parameters are not locally calibrated; heights and crowns are not field-measured;
crowns are assumed circular; palms and incomplete identifications carry low
confidence; large DBH is an extrapolation. See
[`docs/limitations.md`](docs/limitations.md). **Not for legal or arboricultural
decisions.**

## References

FAO (DBH measurement), Huang et al. 1992 (height–diameter models), Carvalho/
Embrapa and Lorenzi (Brazilian tree references). See
[`docs/references.md`](docs/references.md). Adopted coefficients are operational,
not published species coefficients.

## License

Code: **MIT**. Documentation and synthetic demo data: **CC BY 4.0**. No license
is granted over third-party or proprietary inventory data — verify usage rights
for any real inventory before use. See [LICENSE](LICENSE).

## Disclaimer

Results are **preliminary estimates** for lighting pre-modelling. They do not
replace field dendrometric survey, forest inventory, arboricultural report,
stability assessment or topographic survey.
