# Changelog

All notable changes to this project are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **DIALux 3D export** — two paths, in both the Python package and the browser
  app. `export-3ds` writes a parametric schematic tree (trunk cylinder + crown
  ellipsoid) sized to the computed geometry as an open-format `.3ds` binary; the
  Python and TypeScript writers emit byte-identical output for the same tree.
  `export-dxobj` rewrites the STEP dimensions/scale-factors of a user-supplied
  DIALux `.dxobj` template (proprietary mesh reused verbatim, git-ignored). The
  app adds a single-tree **Export .3ds** button and a batch **.3ds (ZIP)**
  download, all generated in-browser.
- **Shared parameter file** `data/species_parameters.json` — single source of
  truth loaded by both the Python package and the TypeScript frontend
  (`load_parameter_set_json()`; the default loader prefers it when present).
- **Static TypeScript/Vite frontend** (`web/`): browser-only single-tree
  calculator with min/central/max scenarios, provenance table, confidence and
  warnings, a schematic tree SVG, and in-browser CSV/XLSX import (column
  mapping) and CSV/XLSX export. No backend, no analytics.
- **Cross-language equivalence**: `tests/fixtures/equivalence_cases.json`
  (135 cases) generated from the Python pipeline, asserted field-by-field by
  both `web/test/equivalence.test.ts` (Vitest) and
  `tests/test_equivalence_fixture.py` (pytest).
- **Gated GitHub Pages deploy** (`.github/workflows/deploy.yml`): publishes the
  MkDocs site plus the calculator under `/app/` only after Python tests,
  TypeScript/equivalence tests, and both builds pass.
- Documentation of the dual implementation (`docs/dual_implementation.md`,
  `web/README.md`) and a decimal round-half-to-even helper in TypeScript that
  reproduces Python's `round()` exactly.

## [0.1.0] - 2026-07-13

### Added
- Faithful reproduction of the source workbook height model:
  `DAP = P/π` and `H = 1.30 + (H∞ − 1.30)·[1 − exp(−DAP/k)]`, with 0.5 m
  rounding and the operational ±band (2 m lower floor).
- Externalised per-species parameters (H∞, k, size class, source) in
  `data/parameters/species_parameters.csv`.
- Separate, clearly-labelled **heuristic** crown + DIALux geometry layer
  (crown diameter, palm rule, crown base height, crown depth, projected area,
  X/Y/Z parameters) in `data/parameters/crown_parameters.csv`.
- Data model (`TreeInput`, `SpeciesParameters`, `TreeGeometryResult`).
- Validation, IO (CSV/XLSX), reporting and a Typer CLI
  (`calculate`, `validate`, `inspect-workbook`, `export-excel`).
- Regression test suite against all 62 rows of the source workbook.
- Synthetic anonymised demonstration dataset and generated outputs.
- Bilingual documentation (EN/PT-BR) and MkDocs Material site.

### Notes
- The height core is validated against the source workbook.
- The crown/DIALux layer is an engineering heuristic and is **not** derived
  from, nor validated against, the workbook.
