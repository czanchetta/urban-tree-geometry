# Dual implementation: Python reference + TypeScript frontend

## Why two implementations

GitHub Pages hosts **static files only** and does not execute Python as a
server language. To offer an interactive in-browser calculator *and* keep a
rigorous scientific implementation, the project maintains two code paths that
are kept in lockstep by a shared parameter file and an automated
cross-language equivalence test.

| | Python package (`src/`) | TypeScript frontend (`web/`) |
|---|---|---|
| Role | Scientific reference | Interactive demo |
| Runtime | CPython 3.11+ | Browser (ES2020) |
| Inputs | CSV, XLSX | CSV, XLSX (in-browser) |
| Outputs | CSV, formula-free XLSX, reports | CSV, XLSX download |
| Tests | pytest (incl. 62-row workbook regression) | Vitest (unit + equivalence) |
| Parameters | `data/species_parameters.json` | **same** file (synced into the bundle) |

## Single source of truth

All parameters — per-species H∞ and k, crown groups, palm rule, and the model
constants — live in one document: **`data/species_parameters.json`**.

- The Python package loads it via `load_parameter_set_json()` (the default
  loader prefers it automatically when present).
- The frontend build copies it verbatim into `web/src/data/` via
  `web/scripts/sync-params.mjs`, run automatically before `dev`, `build` and
  `test`. A guard test (`web/test/params.test.ts`) fails if the bundled copy
  ever drifts from the root file.

Parameters are therefore never edited in two places.

## Cross-language equivalence

`scripts/generate_equivalence_fixture.py` runs a deterministic reference set
(every species at several perimeters, plus edge cases: unknown species,
taxonomic divergence, palm, extrapolation, missing/invalid perimeter) through
the **Python** pipeline and records the full expected output to
`tests/fixtures/equivalence_cases.json`.

- **TypeScript side** (`web/test/equivalence.test.ts`): runs the identical
  inputs through the TS pipeline and asserts every numeric field agrees within
  1e-9, and that strings, confidence and warnings match exactly.
- **Python side** (`tests/test_equivalence_fixture.py`): asserts the committed
  fixture still equals the current Python output, so a change to the Python
  pipeline that would break equivalence fails here too and forces the fixture
  (and the diff) to be regenerated.

### A note on rounding

The two languages must round identically. The height model rounds to the
nearest 0.5 m (round-half-away-from-zero, matching the source spreadsheet's
`ROUND(x*2,0)/2`). The display fields (DAP 1 dp, trunk 4 dp, crown 2 dp) use
Python's `round()`, which is **round-half-to-even** (banker's rounding). Exact
binary ties do occur — e.g. `crown_depth = 0.75 · H` with H on a 0.5 m grid
gives values like 5.625, exactly representable in binary — so the TypeScript
`roundDecimal()` reproduces round-half-to-even on the double's exact decimal
expansion rather than using a naive away-from-zero rounder. The equivalence
fixture verifies this end-to-end.

## Local development

```bash
# Python
pip install -e ".[dev,viz]"
pytest -q

# Regenerate the equivalence fixture after any intended model change
python scripts/generate_equivalence_fixture.py

# Frontend
cd web
npm install
npm run dev      # local dev server
npm test         # unit + equivalence tests
npm run build    # static build -> web/dist/
```

## Deployment (GitHub Actions)

`.github/workflows/deploy.yml` runs three gates and only then publishes:

1. `python-tests` — pytest (workbook regression + equivalence fixture);
2. `ts-tests` — Vitest (unit + equivalence);
3. `build-deploy` — builds the MkDocs site **and** the Vite calculator, places
   the calculator under `site/app/`, and deploys to GitHub Pages. This job
   `needs` both test jobs, so a failure in either blocks the deploy.

## XLSX in the browser

CSV is the primary in-browser format (parsed with a small dependency). XLSX
import/export is supported but the XLSX library (~430 kB) is **lazy-loaded**
only when the user actually reads or writes an XLSX file, so it never weighs
down the initial page load.
