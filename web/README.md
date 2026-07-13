# Tree Geometry Estimator — web calculator

Static, browser-only calculator (TypeScript + Vite, no framework, no backend,
no analytics). It reproduces the height core and heuristic crown/DIALux layer
of the Python package, loading the **same** parameter file
(`../data/species_parameters.json`, synced into `src/data/` at build time).

## Scripts

```bash
npm install
npm run dev      # dev server (auto-syncs params)
npm test         # Vitest: unit tests + Python<->TS equivalence
npm run build    # type-check + static build -> dist/
npm run preview  # preview the production build
```

## Structure

- `src/core/` — the ported calculation modules (`params`, `calculations`,
  `crown`, `pipeline`, `schematic`, `format`). These mirror the Python package
  and are covered by the cross-language equivalence test.
- `src/main.ts` — single-tree calculator UI + schematic + min/central/max
  scenarios.
- `src/batch.ts` — CSV/XLSX import, column mapping, validation, batch compute,
  CSV/XLSX export, and a `.3ds` (ZIP) export (all in-browser; XLSX lazy-loaded).
- `src/core/dialux3ds.ts` — DIALux `.3ds` writer (schematic trunk+crown mesh),
  verified byte-identical to the Python writer by `test/dialux3ds.test.ts`.
- `src/core/zipstore.ts` — minimal store-only ZIP writer for the batch bundle.
- `test/` — Vitest suites (`calculations`, `params`, `equivalence`,
  `dialux3ds`, `zipstore`).
- `scripts/sync-params.mjs` — copies the single source-of-truth parameter file
  into the bundle (runs before dev/build/test).

## Equivalence

`test/equivalence.test.ts` runs `../tests/fixtures/equivalence_cases.json`
(produced by the Python pipeline) through the TypeScript pipeline and asserts
field-by-field agreement. If you change the model, regenerate the fixture on
the Python side (`python scripts/generate_equivalence_fixture.py`) and re-run
both test suites.

## Privacy

All processing happens in your browser. No data is uploaded, and there are no
analytics or third-party trackers.
